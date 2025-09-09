import os               # Modul für Betriebssystemfunktionen (Dateien, Ordner etc.)
import subprocess       # Modul, um Shell-Befehle über Python auszuführen

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
        
        auswahl = input("Deine Auswahl: ")     # Benutzerabfrage für Menüoption
        
        if auswahl == "1":
            alle_notizen_anzeigen()           # ruft die Funktion zum Anzeigen auf
        elif auswahl == "2":
            neue_notiz()                       # ruft die Funktion zum Erstellen auf
        elif auswahl == "3":
            notiz_loeschen()                   # ruft die Funktion zum Löschen auf
        elif auswahl == "4":
            print("👋 Bis bald!")             # Verabschiedung
            break                               # Schleife verlassen → Skript endet
        else:
            print("Ungültige Auswahl, bitte nochmal versuchen.")
