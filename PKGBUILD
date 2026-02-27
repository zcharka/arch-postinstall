# Maintainer: Sebastian <twoj@email.com>
pkgname=ratinstall
pkgver=2.4
pkgrel=1
pkgdesc="Arch Linux Post-Install Wizard & Presets"
arch=('any')
url="https://github.com/zcharka/arch-postinstall"  # to może być nadal arch-postinstall, ale możesz zmienić
license=('GPL')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'flatpak')
makedepends=('git')
source=("git+https://github.com/zcharka/arch-postinstall.git")
md5sums=('SKIP')

package() {
    # Nazwa katalogu po sklonowaniu to "arch-postinstall" (bo tak nazywa się repozytorium)
    local _sourcedir="$srcdir/arch-postinstall"

    # 1. Tworzymy foldery w wirtualnym systemie plików paczki
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # 2. Kopiujemy kod źródłowy do /opt/ratinstall
    cp -r "$_sourcedir/src" "$pkgdir/opt/$pkgname/"

    # --- GŁÓWNA APLIKACJA: ratinstall ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/ratinstall"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/ratinstall"
    chmod +x "$pkgdir/usr/bin/ratinstall"

    # --- APLIKACJA PRESETÓW: ratinstall-presets ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/ratinstall-presets"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/ratinstall-presets"
    chmod +x "$pkgdir/usr/bin/ratinstall-presets"

    # --- PLIKI .DESKTOP ---
    # Główny desktop
    install -Dm644 "$_sourcedir/src/ratinstall.desktop" "$pkgdir/usr/share/applications/ratinstall.desktop" 2>/dev/null || true
    # Desktop dla presets (jeśli osobny)
    install -Dm644 "$_sourcedir/src/ratinstall-presets.desktop" "$pkgdir/usr/share/applications/ratinstall-presets.desktop" 2>/dev/null || true
}
