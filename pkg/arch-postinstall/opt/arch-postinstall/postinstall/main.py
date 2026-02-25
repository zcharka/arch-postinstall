import os
from . import gnome, system, plasma

def run():
    print("--- Arch Linux Post-Install Wizard ---")

    # 1. Wykrywanie środowiska
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()

    # Wykonaj wspólne kroki (repozytoria, yay, steam fix)
    # system.update_system() itd... (zakładam, że to masz z poprzedniego kroku)

    if 'gnome' in desktop:
        print("Wykryto GNOME.")
        gnome.install_gnome_deps()
        gnome.setup_appearance()

    elif 'kde' in desktop or 'plasma' in desktop:
        print("\n--- Wykryto KDE Plasma ---")
        print("Wybierz tryb konfiguracji:")
        print("1. Standardowa Plasma (tylko aplikacje i poprawki)")
        print("2. Custom Preset (Motyw Layan + Dock + Blur - jak na screenie)")

        choice = input("Twój wybór [1/2]: ").strip()

        # Zawsze instalujemy podstawowe apki
        # system.install_flatpaks()

        if choice == "2":
            plasma.install_plasma_deps() # Instaluje motywy z AUR
            plasma.apply_custom_look()   # Włącza KWin effects
            plasma.apply_layout_preset() # Robi Docka
        else:
            print("Pominięto modyfikacje wizualne.")

    else:
        print(f"Nieobsługiwane środowisko: {desktop}")

    print("\nGotowe! Zrestartuj system, aby zobaczyć zmiany.")
