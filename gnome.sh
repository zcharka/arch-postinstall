#!/bin/bash

# Skrypt poinstalacyjny dla GNOME - wersja działająca
# Uruchom z uprawnieniami użytkownika (sudo będzie używane gdzie potrzebne)

echo "=== Rozpoczynam skrypt poinstalacyjny dla GNOME ==="

# Sprawdzenie czy to GNOME
if ! echo "$XDG_CURRENT_DESKTOP" | grep -iq "GNOME"; then
    echo "To nie jest środowisko GNOME. Skrypt przeznaczony tylko dla GNOME."
    exit 1
fi

# ------------------------------------------------------------
# 1. NAPRAWA MIRRORÓW I AKTUALIZACJA
# ------------------------------------------------------------
echo "Aktualizuję serwery i bazę pakietów..."
sudo pacman -Sy --noconfirm archlinux-keyring
sudo pacman -Syu --noconfirm

# ------------------------------------------------------------
# 2. INSTALACJA NARZĘDZI BUDOWANIA I PODSTAW
# ------------------------------------------------------------
echo "Instaluję base-devel, git i podstawowe narzędzia..."
sudo pacman -S --needed base-devel git wget cmake flatpak ntfs-3g unzip --noconfirm

# ------------------------------------------------------------
# 3. KONFIGURACJA LOKALNEGO REPOZYTORIUM LINEXIN
# ------------------------------------------------------------
echo "Pobieram i konfiguruję linexin-repo jako lokalne repozytorium..."
sudo mkdir -p /opt
if [ ! -d "/opt/linexin-repo" ]; then
    sudo git clone https://github.com/Petexy/linexin-repo.git /opt/linexin-repo
else
    cd /opt/linexin-repo && sudo git pull && cd -
fi

# Dodanie wpisu do pacman.conf, jeśli jeszcze nie istnieje
if ! grep -q "\[linexin-repo\]" /etc/pacman.conf; then
    echo -e "\n[linexin-repo]\nSigLevel = Optional TrustAll\nServer = file:///opt/linexin-repo/x86_64" | sudo tee -a /etc/pacman.conf
    sudo pacman -Sy --noconfirm
fi

# ------------------------------------------------------------
# 4. INSTALACJA YAY (AUR helper)
# ------------------------------------------------------------
if ! command -v yay &> /dev/null; then
    echo "Buduję yay..."
    git clone https://aur.archlinux.org/yay.git
    cd yay
    makepkg -si --noconfirm
    cd ..
    rm -rf yay
fi

# ------------------------------------------------------------
# 5. INSTALACJA PROGRAMÓW Z REPOZYTORIÓW
# ------------------------------------------------------------
echo "Instaluję podstawowe programy z oficjalnych repozytoriów..."
sudo pacman -S --noconfirm \
    fish \
    gnome-tweaks \
    gnome-browser-connector \
    bibata-cursor-theme-bin \
    starship \
    ttf-jetbrains-mono-nerd \
    fastfetch \
    pacman-contrib \
    btop \
    virt-manager \
    qemu-desktop \
    libvirt \
    edk2-ovmf \
    dnsmasq \
    iptables-nft \
    bridge-utils \
    openbsd-netcat \
    lutris

# ------------------------------------------------------------
# 6. APLIKACJE FLATPAK
# ------------------------------------------------------------
echo "Konfiguruję Flathub i instaluję aplikacje Flatpak..."
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install flathub -y \
    com.discordapp.Discord \
    com.valvesoftware.Steam \
    org.mozilla.firefox \
    io.github.zen_browser.zen \
    com.usebottles.bottles

# ------------------------------------------------------------
# 7. INSTALACJA ROZSZERZEŃ GNOME Z AUR
# ------------------------------------------------------------
echo "Instaluję rozszerzenia GNOME z AUR..."
yay -S --noconfirm \
    gnome-shell-extension-accent-icons-git \
    gnome-shell-extension-appindicator \
    gnome-shell-extension-blur-my-shell \
    gnome-shell-extension-dash-to-dock \
    gnome-shell-extension-ding \
    gnome-shell-extension-gsconnect \
    gnome-shell-extension-quick-settings-audio-panel \
    gnome-shell-extension-rounded-window-corners-reborn-git \
    gnome-shell-extension-user-theme

# Dodatkowe pakiety z AUR
yay -S --noconfirm ttf-poppins faugus-launcher

# ------------------------------------------------------------
# 8. MOTYW GTK I IKONY
# ------------------------------------------------------------
echo "Instaluję motyw GTK Colloid..."
cd /tmp
git clone https://github.com/vinceliuice/Colloid-gtk-theme.git
./Colloid-gtk-theme/install.sh -t purple -s standard
rm -rf Colloid-gtk-theme

echo "Instaluję ikony Colloid (wariant purple)..."
git clone https://github.com/vinceliuice/Colloid-icon-theme.git
./Colloid-icon-theme/install.sh -t purple
rm -rf Colloid-icon-theme

# ------------------------------------------------------------
# 9. KONFIGURACJA rEFInd (Automatyczny UUID + parametry)
# ------------------------------------------------------------
if [ -d "/boot/EFI/refind" ]; then
    CURRENT_ROOT_UUID=$(findmnt -n -o UUID /)
    echo "Konfiguruję rEFInd dla UUID: $CURRENT_ROOT_UUID"
    
    PARAMS="rw root=UUID=$CURRENT_ROOT_UUID video=HDMI-A-1:d"
    lspci | grep -iq "nvidia" && PARAMS="$PARAMS nvidia-drm.modeset=1"
    
    # Wykrywanie Microcode
    UCODE="initrd=\\intel-ucode.img"
    grep -q "AMD" /proc/cpuinfo && UCODE="initrd=\\amd-ucode.img"

    sudo tee /boot/EFI/refind/refind_linux.conf <<EOF
"Standard Boot"  "$PARAMS $UCODE initrd=\\initramfs-linux.img"
"Terminal Boot"  "$PARAMS $UCODE initrd=\\initramfs-linux.img systemd.unit=multi-user.target"
EOF
    echo "✓ rEFInd skonfigurowany"
fi

# ------------------------------------------------------------
# 10. DYSK NTFS i STEAM FIX
# ------------------------------------------------------------
if lsblk -dno LABEL | grep -q "nowy"; then
    echo "Konfiguruję dysk NTFS 'nowy' i dowiązania dla Steam..."
    sudo mkdir -p /mnt/nowy
    if ! grep -q "/mnt/nowy" /etc/fstab; then
        echo "LABEL=nowy /mnt/nowy ntfs-3g defaults,nosuid,nodev,nofail,uid=$(id -u),gid=$(id -g),dmask=022,fmask=133,windows_names 0 0" | sudo tee -a /etc/fstab
    fi
    sudo mount -a
    mkdir -p ~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/
    mkdir -p ~/.steam_compat_fix
    ln -sf ~/.steam_compat_fix ~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata
    echo "✓ Dysk 'nowy' skonfigurowany"
fi

# ------------------------------------------------------------
# 11. KONFIGURACJA WIRTUALIZACJI (libvirt)
# ------------------------------------------------------------
echo "Konfiguruję usługi systemd i grupy dla wirtualizacji..."

# Załadowanie modułów jądra
sudo modprobe bridge 2>/dev/null || echo "Moduł bridge już załadowany"
sudo modprobe br_netfilter 2>/dev/null || echo "Moduł br_netfilter już załadowany"

# Automatyczne ładowanie modułów przy starcie
echo "bridge" | sudo tee /etc/modules-load.d/virt-network.conf
echo "br_netfilter" | sudo tee -a /etc/modules-load.d/virt-network.conf

# Włączenie i uruchomienie libvirtd
if systemctl list-unit-files | grep -q libvirtd.service; then
    sudo systemctl enable libvirtd.service
    sudo systemctl start libvirtd.service
    echo "✓ Usługa libvirtd uruchomiona"
else
    echo "⚠ Usługa libvirtd nie została znaleziona"
fi

# Dodanie użytkownika do grupy libvirt
sudo usermod -aG libvirt $USER
echo "✓ Użytkownik $USER dodany do grupy libvirt"

# Definiowanie domyślnej sieci NAT
if [ -f /etc/libvirt/qemu/networks/default.xml ]; then
    sudo virsh net-define /etc/libvirt/qemu/networks/default.xml 2>/dev/null || true
    sudo virsh net-autostart default 2>/dev/null || true
    sudo virsh net-start default 2>/dev/null || true
fi

# Definiowanie sieci mostkowanej (macvtap) dla głównego interfejsu
MAIN_IF=$(ip route | grep default | awk '{print $5}' | head -n 1)
if [ -n "$MAIN_IF" ]; then
    cat <<EOF > /tmp/host-bridge.xml
<network>
  <name>host-bridge</name>
  <forward mode="bridge">
    <interface dev="$MAIN_IF"/>
  </forward>
</network>
EOF
    sudo virsh net-define /tmp/host-bridge.xml 2>/dev/null || true
    sudo virsh net-autostart host-bridge 2>/dev/null || true
    sudo virsh net-start host-bridge 2>/dev/null || true
    rm -f /tmp/host-bridge.xml
    echo "✓ Sieć mostkowana skonfigurowana"
fi

# ------------------------------------------------------------
# 12. KONFIGURACJA POWŁOKI (Fish + Starship)
# ------------------------------------------------------------
echo "Konfiguruję Starship dla Fish..."
mkdir -p ~/.config/fish
echo 'starship init fish | source' > ~/.config/fish/config.fish
echo 'fastfetch' >> ~/.config/fish/config.fish

echo "Zmieniam domyślną powłokę na Fish..."
chsh -s /usr/bin/fish $USER

# ------------------------------------------------------------
# 13. USTAWIENIA WYGLĄDU (Kursor, Ikony, Tapeta)
# ------------------------------------------------------------
echo "Stosuję ustawienia wyglądu..."

# Poczekaj chwilę na załadowanie ustawień
sleep 3

# Ustaw ikony i kursor
gsettings set org.gnome.desktop.interface icon-theme 'Colloid-purple' 2>/dev/null || echo "⚠ Motyw ikon Colloid-purple niedostępny"
gsettings set org.gnome.desktop.interface cursor-theme 'Bibata-Classic-Black' 2>/dev/null || echo "⚠ Motyw kursora Bibata niedostępny"

# Ustaw czcionkę Poppins jeśli dostępna
gsettings set org.gnome.desktop.interface font-name 'Poppins 10' 2>/dev/null || echo "⚠ Czcionka Poppins niedostępna"
gsettings set org.gnome.desktop.interface document-font-name 'Poppins 10' 2>/dev/null

# Pobierz i ustaw tapetę
URL_TAPETY="https://i.imgur.com/Y9X3VQz.jpeg"
NAZWA_PLIKU="tapeta_arch.jpg"
mkdir -p ~/Pobrane ~/Obrazy
curl -L "$URL_TAPETY" -o ~/Pobrane/$NAZWA_PLIKU 2>/dev/null
cp ~/Pobrane/$NAZWA_PLIKU ~/Obrazy/$NAZWA_PLIKU 2>/dev/null
SCIEZKA_FINALNA="$HOME/Obrazy/$NAZWA_PLIKU"

if [ -f "$SCIEZKA_FINALNA" ]; then
    gsettings set org.gnome.desktop.background picture-uri "file://$SCIEZKA_FINALNA" 2>/dev/null
    gsettings set org.gnome.desktop.background picture-uri-dark "file://$SCIEZKA_FINALNA" 2>/dev/null
    gsettings set org.gnome.desktop.background picture-options 'zoom' 2>/dev/null
    echo "✓ Tapeta ustawiona"
fi

# ------------------------------------------------------------
# 14. WŁĄCZANIE ROZSZERZEŃ GNOME
# ------------------------------------------------------------
echo "Włączam zainstalowane rozszerzenia GNOME..."
sleep 5  # Czekamy na załadowanie powłoki

EXTENSIONS=(
    "dash-to-dock@micxgx.gmail.com"
    "blur-my-shell@aunetx"
    "appindicatorsupport@rgcjonas.gmail.com"
    "rounded-window-corners@fxgn"
    "ding@rastersoft.com"
    "gsconnect@andyholmes.github.io"
    "quick-settings-audio-panel@rayzeq.github.io"
    "user-theme@gnome-shell-extensions.gcampax.github.com"
)

for ext in "${EXTENSIONS[@]}"; do
    if gnome-extensions list | grep -q "$ext"; then
        gnome-extensions enable "$ext" 2>/dev/null && echo "✓ Włączono $ext"
    fi
done

# ------------------------------------------------------------
# 15. KONIEC
# ------------------------------------------------------------
echo ""
echo "====================================================="
echo "=== SKRYPT ZAKOŃCZONY POMYŚLNIE ==="
echo "====================================================="
echo ""
echo "✅ Wykonano:"
echo "  - Aktualizacja systemu"
echo "  - Instalacja narzędzi (git, base-devel, yay)"
echo "  - Konfiguracja linexin-repo"
echo "  - Instalacja programów z oficjalnych repozytoriów"
echo "  - Instalacja aplikacji Flatpak"
echo "  - Instalacja rozszerzeń GNOME z AUR"
echo "  - Instalacja motywów GTK i ikon"
echo "  - Konfiguracja rEFInd"
echo "  - Konfiguracja dysku NTFS i Steam"
echo "  - Konfiguracja wirtualizacji (libvirt)"
echo "  - Ustawienie powłoki Fish ze Starship"
echo "  - Ustawienie wyglądu (ikony, kursor, tapeta)"
echo "  - Włączenie rozszerzeń GNOME"
echo ""
echo "⚠️  UWAGA: Aby zmiany w grupach (libvirt) zadziałały,"
echo "   musisz się wylogować i zalogować ponownie."
echo ""
echo "🔁 System zrestartuje się za 10 sekund..."
echo "Naciśnij Ctrl+C, aby anulować restart."

sleep 10
sudo reboot
