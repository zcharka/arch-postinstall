# Maintainer: Sebastian zcharkayt@gmail.com
pkgname=arch-postinstall
pkgver=1.0
pkgrel=1
pkgdesc="Mój osobisty konfigurator Arch Linux (KDE/GNOME)"
arch=('any')
url="https://github.com/TWÓJ_NICK/arch-postinstall"
license=('MIT')
# Zależności, które makepkg zainstaluje sam
depends=('python' 'python-pyqt6' 'python-requests' 'yay')
makedepends=('git')
# Ponieważ to repo prywatne, nie używamy source=(), tylko kopiujemy lokalne pliki
options=('!strip')

package() {
    # 1. Tworzymy folder w /opt/
    mkdir -p "$pkgdir/opt/$pkgname"

    # 2. Kopiujemy kod źródłowy do systemu
    cp -r "$startdir/src" "$pkgdir/opt/$pkgname/"

    # 3. Tworzymy skrypt uruchamiający w /usr/bin/
    mkdir -p "$pkgdir/usr/bin"
    echo "#!/bin/bash" > "$pkgdir/usr/bin/arch-setup"
    # Uruchamiamy przez pythona systemowego
    echo "python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"

    # 4. Nadajemy prawa wykonywalności
    chmod +x "$pkgdir/usr/bin/arch-setup"
}
