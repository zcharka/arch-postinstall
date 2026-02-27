# Maintainer: Sebastian <twoj@email.com>
pkgname=ratinstall
pkgver=2.4
pkgrel=2
pkgdesc="Arch Linux Post-Install Wizard & Presets + Rat Center"
arch=('any')
url="https://github.com/zcharka/arch-postinstall"
license=('GPL')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'flatpak')
makedepends=('git')
source=("git+https://github.com/zcharka/arch-postinstall.git")
md5sums=('SKIP')

package() {
    # Katalog źródłowy po sklonowaniu
    local _sourcedir="$srcdir/arch-postinstall"

    # Tworzenie katalogów docelowych
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # Kopiowanie całego kodu źródłowego (katalog src/) do /opt/ratinstall/
    cp -r "$_sourcedir/src" "$pkgdir/opt/$pkgname/"

    # --- Skrypty uruchomieniowe ---
    # 1. Główny instalator (main_window.py)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/ratinstall"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/ratinstall"
    chmod +x "$pkgdir/usr/bin/ratinstall"

    # 2. Przełącznik motywów KDE (theme_switcher.py)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/ratinstall-presets"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/ratinstall-presets"
    chmod +x "$pkgdir/usr/bin/ratinstall-presets"

    # 3. Rat Center (rat_center.py)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/rat-center"
    echo "exec python /opt/$pkgname/src/ui/rat_center.py" >> "$pkgdir/usr/bin/rat-center"
    chmod +x "$pkgdir/usr/bin/rat-center"

    # --- Pliki .desktop (jeśli istnieją w repozytorium) ---
    # Dla głównego instalatora
    if [ -f "$_sourcedir/src/ratinstall.desktop" ]; then
        install -Dm644 "$_sourcedir/src/ratinstall.desktop" "$pkgdir/usr/share/applications/ratinstall.desktop"
    fi

    # Dla przełącznika motywów
    if [ -f "$_sourcedir/src/ratinstall-presets.desktop" ]; then
        install -Dm644 "$_sourcedir/src/ratinstall-presets.desktop" "$pkgdir/usr/share/applications/ratinstall-presets.desktop"
    fi

    # Dla Rat Center
    if [ -f "$_sourcedir/src/rat-center.desktop" ]; then
        install -Dm644 "$_sourcedir/src/rat-center.desktop" "$pkgdir/usr/share/applications/rat-center.desktop"
    fi
}
