import subprocess

def install_sugar_candy(runner):
    """
    runner: funkcja, która wykonuje komendę (np. self.run_cmd w wątku)
    """
    print("Konfiguracja SDDM Sugar Candy...")

    # 1. Instalacja SDDM i motywu
    # Zakładamy, że yay jest już zainstalowany w poprzednich krokach
    runner("yay -S --noconfirm sddm sddm-sugar-candy-git")

    # 2. Włączenie usługi SDDM
    runner("sudo systemctl enable sddm")

    # 3. Tworzenie konfiguracji
    config_content = """[Theme]
Current=sugar-candy
"""
    # Zapisz do pliku tymczasowego i przenieś z sudo
    # Używamy triku z bash -c, żeby sudo zadziałało na przekierowanie
    cmd = f"echo '{config_content}' | sudo tee /etc/sddm.conf.d/theme.conf"

    # Musimy upewnić się, że folder istnieje
    runner("sudo mkdir -p /etc/sddm.conf.d")
    runner(cmd, use_shell=True)
