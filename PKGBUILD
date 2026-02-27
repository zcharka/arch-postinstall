# Maintainer: Sebastian <twoj@email.com>
pkgname=ratinstall
pkgver=2.4
pkgrel=1
pkgdesc="Arch Linux Post-Install Wizard & Presets"
arch=('any')
url="https://github.com/zcharka/arch-postinstall"
license=('GPL')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'flatpak')
makedepends=('git')
source=("git+https://github.com/zcharka/arch-postinstall.git")
md5sums=('SKIP')

package() {
    # Katalog, do którego git klonuje repozytorium (nazwa z URL)
    local _sourcedir="$srcdir/arch-postinstall"

    # Tworzenie struktury katalogów w docelowym pakiecie
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # Kopiowanie całego katalogu 'src' z repozytorium do /opt/ratinstall/
    cp -r "$_sourcedir/src" "$pkgdir/opt/$pkgname/"

    # Skrypt uruchamiający główny instalator (main_window.py)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/ratinstall"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/ratinstall"
    chmod +x "$pkgdir/usr/bin/ratinstall"

    # Skrypt uruchamiający przełącznik motywów (theme_switcher.py)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/ratinstall-presets"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/ratinstall-presets"
    chmod +x "$pkgdir/usr/bin/ratinstall-presets"

    # Pliki .desktop (jeśli istnieją w repozytorium, możesz je dodać później)
    # if [ -f "$_sourcedir/src/ratinstall.desktop" ]; then
    #     install -Dm644 "$_sourcedir/src/ratinstall.desktop" "$pkgdir/usr/share/applications/ratinstall.desktop"
    # fi
}
