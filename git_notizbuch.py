import os               # Modul für Betriebssystemfunktionen (Dateien, Ordner etc.)
import subprocess       # Modul, um Shell-Befehle über Python auszuführen
import boto3
from datetime import datetime, timezone

# S3 Client erstellen
s3 = boto3.client('s3')
bucket_name = "devops-notizbuch"  # Name deines S3-Buckets

NOTIZ_ORDNER = "notizen"

#-------------------------
#Syncronisiere
#------------------------
def synchronisieren():
    print("🔄 Starte Synchronisation zwischen lokal und S3...")

    # 1. Lokale Dateien sammeln
    lokale_dateien = {}
    for datei in os.listdir("."):
        if datei.endswith(".txt"):  # nur Notizen berücksichtigen
            lokale_dateien[datei] = os.path.getmtime(datei)  # Änderungszeitpunkt speichern

    # 2. Dateien aus S3 sammeln
    s3_dateien = {}
    response = s3.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        for obj in response["Contents"]:
            key = obj["Key"]
            if key.endswith(".txt"):
                s3_dateien[key] = obj["LastModified"].replace(tzinfo=timezone.utc).timestamp()

    # 3. Abgleich
    # a) Dateien nur lokal → hochladen
    for datei in lokale_dateien:
        if datei not in s3_dateien:
            print(f"⬆️ Hochladen: {datei}")
            s3.upload_file(datei, bucket_name, datei)

    # b) Dateien nur in S3 → herunterladen
    for key in s3_dateien:
        if key not in lokale_dateien:
            print(f"⬇️ Herunterladen: {key}")
            s3.download_file(bucket_name, key, key)

    # c) Dateien in beiden vorhanden → Änderungszeit prüfen
    for datei in lokale_dateien:
        if datei in s3_dateien:
            lokal_zeit = lokale_dateien[datei]
            s3_zeit = s3_dateien[datei]

            if lokal_zeit > s3_zeit:
                print(f"⚡ Lokale Datei neuer → Hochladen: {datei}")
                s3.upload_file(datei, bucket_name, datei)
            elif s3_zeit > lokal_zeit:
                print(f"⚡ S3-Version neuer → Herunterladen: {datei}")
                s3.download_file(bucket_name, datei, datei)

    print("✅ Synchronisation abgeschlossen!")


#---------------------------------
#Download
#-------------------------------


def notizen_aus_s3_herunterladen():
    """Lädt alle Notizen aus dem S3-Bucket herunter und speichert sie lokal ab"""
    try:
        # Liste aller Objekte im Bucket abrufen
        response = s3.list_objects_v2(Bucket=bucket_name)

        # Prüfen, ob überhaupt Dateien im Bucket sind
        if "Contents" not in response:
            print("📭 Keine Notizen im S3-Bucket gefunden.")
            return

        # Sicherstellen, dass der lokale Notizordner existiert
        if not os.path.exists(NOTIZ_ORDNER):
            os.makedirs(NOTIZ_ORDNER)

        # Jede Datei aus S3 herunterladen
        for obj in response["Contents"]:
            key = obj["Key"]
            local_path = os.path.join(NOTIZ_ORDNER, key)

            # Prüfen, ob die Datei schon lokal existiert
            if os.path.exists(local_path):
                print(f"⚠️ {key} existiert bereits lokal.")
                # Optional: Nachfrage, ob überschrieben werden soll
                choice = input(f"Soll {key} überschrieben werden? (j/n): ")
                if choice.lower() != "j":
                    print(f"⏩ Überspringe {key}")
                    continue

            # Datei herunterladen
            s3.download_file(bucket_name, key, local_path)
            print(f"⬇️  {key} heruntergeladen und gespeichert.")

    except Exception as e:
        print("❌ Fehler beim Herunterladen aus S3:", str(e))


#-------------------------------
# Funktion Upload zu s3
#-------------------------------
def upload_s3(datei):
    try:
        s3.upload_file(datei, bucket_name, datei)   # Datei hochladen
        print(f"☁️ Datei '{datei}' erfolgreich zu S3 hochgeladen!")
    except Exception as e:
        print("❌ Fehler beim Upload:", e)


# -------------------------------
# Funktion: Neue Notiz anlegen
# -------------------------------
def neue_notiz():
    titel = input("Titel der Notiz: ") + ".txt"  # Benutzer fragt nach Titel, hängt '.txt' an
    inhalt = input("Inhalt der Notiz: ")         # Inhalt der Notiz abfragen
    
    # Datei schreiben
    with open(titel, "w") as f:                 # Datei öffnen im Schreibmodus, automatisch schließen
        f.write(inhalt)
    print(f"✅ Notiz '{titel}' erstellt.")
    
    # Git Befehle ausführen
    subprocess.run(["git", "add", titel])      # Datei zum Git-Index hinzufügen
    subprocess.run(["git", "commit", "-m", f"Notiz '{titel}' hinzugefügt"])  # Commit erstellen
    subprocess.run(["git", "push"])            # Commit zu GitHub pushen
    print("📦 Notiz zu GitHub gepusht!")
    upload_s3(titel) 			#DAtei wird zu s3 hochgeladen

# -------------------------------
# Funktion: Alle Notizen aus S3 anzeigen
# -------------------------------
def alle_notizen_s3_anzeigen():
    try:
        # Listet alle Objekte im Bucket auf
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"\n--- {obj['Key']} ---")  # Dateiname ausgeben
                # Datei aus S3 herunterladen in temporäre Variable
                s3.download_file(bucket_name, obj['Key'], obj['Key'])
                with open(obj['Key'], "r") as f:
                    print(f.read())              # Inhalt der Datei anzeigen
        else:
            print("📂 Keine Notizen im S3-Bucket gefunden.")
    except Exception as e:
        print("❌ Fehler beim Abrufen der S3-Notizen:", e)


# -------------------------------
# Funktion: Notiz aus S3 löschen
# -------------------------------
def notiz_s3_loeschen():
    titel = input("Welche Notiz aus S3 möchtest du löschen? ") + ".txt"
    try:
        # Prüfen, ob Datei existiert
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=titel)
        if 'Contents' in response:
            s3.delete_object(Bucket=bucket_name, Key=titel)  # Löschen aus S3
            print(f"✅ Notiz '{titel}' aus S3 gelöscht.")
        else:
            print("❌ Diese Notiz existiert nicht im S3-Bucket.")
    except Exception as e:
        print("❌ Fehler beim Löschen der Notiz aus S3:", e)


# -------------------------------
# Funktion: Alle Notizen anzeigen
# -------------------------------
def alle_notizen_anzeigen():
    for datei in os.listdir("."):               # Alle Dateien im aktuellen Verzeichnis durchgehen
        if datei.endswith(".txt"):             # Nur Dateien mit '.txt' anzeigen
            print(f"\n--- {datei} ---")        # Dateiname ausgeben
            with open(datei, "r") as f:
                print(f.read())               # Inhalt der Datei anzeigen

# -------------------------------
# Funktion: Notiz löschen
# -------------------------------
def notiz_loeschen():
    titel = input("Welche Notiz möchtest du löschen? ") + ".txt"
    if os.path.exists(titel):                  # Prüfen, ob die Datei existiert
        os.remove(titel)                       # Datei löschen
        print(f"✅ Notiz '{titel}' gelöscht.")
        
        # Git Befehle für Löschung
        subprocess.run(["git", "add", "-A"])   # Alle Änderungen inkl. Löschungen zum Git-Index hinzufügen
        subprocess.run(["git", "commit", "-m", f"Notiz '{titel}' gelöscht"])  # Commit erstellen
        subprocess.run(["git", "push"])       # Push zu GitHub
        print("📦 Änderungen zu GitHub gepusht!")
    else:
        print("❌ Diese Notiz existiert nicht.")

# -------------------------------
# Hauptmenü
# -------------------------------
if __name__ == "__main__":                     # Prüft, ob Skript direkt ausgeführt wird
    while True:                                # Endlosschleife für das Menü
        print("\n--- Git-Notizbuch Menü ---")
        print("1: Alle Notizen anzeigen")
        print("2: Neue Notiz anlegen")
        print("3: Notiz löschen")
        print("4: Beenden")
        print("5: Alle Notizen uas S3 anzeigen")
        print("6: Notiz aus S3 löschen")
        print("7: Notizen aus S3 herunterladen")
        print("8: Syncronisieren")
        auswahl = input("Deine Auswahl: ")     # Benutzerabfrage für Menüoption

        if auswahl == "1":
            alle_notizen_anzeigen()           # ruft die Funktion zum Anzeigen auf
        elif auswahl == "2":
            neue_notiz()                       # ruft die Funktion zum Erstellen auf
        elif auswahl == "3":
            notiz_loeschen()                   # ruft die Funktion zum Löschen auf
        elif auswahl == "4":
            print("👋 Bis bald")
            break
        elif auswahl == "5":
            alle_notizen_s3_anzeigen()
        elif auswahl == "6":
            notiz_s3_loeschen()
        elif auswahl == "7":
            notizen_aus_s3_herunterladen()
        elif auswahl == "8":
            synchronisieren()
        else:
            print("Ungültige Auswahl, bitte nochmal versuchen.")

