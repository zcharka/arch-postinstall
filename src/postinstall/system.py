import subprocess
import os

def setup_refind():
    if os.path.exists("/boot/EFI/refind/refind_linux.conf"):
        # Pobieranie UUID w Pythonie jest bardzo proste
        root_uuid = subprocess.check_output(["findmnt", "-n", "-o", "UUID", "/"]).decode().strip()

        # Budowanie parametrów
        params = f"rw root=UUID={root_uuid} video=HDMI-A-1:d"

        # Sprawdzanie Nvidii
        lspci = subprocess.check_output(["lspci"]).decode().lower()
        if "nvidia" in lspci:
            params += " nvidia-drm.modeset=1"

        # Tutaj zapisalibyśmy plik używając standardowego: with open(...) as f:
        print(f"Wygenerowano parametry rEFInd: {params}")
