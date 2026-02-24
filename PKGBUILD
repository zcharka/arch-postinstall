# Maintainer: Sebastian <twoj@email.com>
pkgname=arch-postinstall
pkgver=2.0
pkgrel=1
pkgdesc="Arch Linux Post-Install Wizard (GTK4/Libadwaita)"
arch=('any')
url="https://github.com/zcharka/arch-postinstall"
license=('GPL')
# Tutaj są nowe zależności dla GTK4 i Libadwaita
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'flatpak')
makedepends=('git')
source=("git+https://github.com/zcharka/arch-postinstall.git")
md5sums=('SKIP')

package() {
    # Tworzymy foldery systemowe
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"

    # Kopiujemy pliki źródłowe do /opt/arch-postinstall
    cp -r "$srcdir/$pkgname/src" "$pkgdir/opt/$pkgname/"

    # Tworzymy plik uruchamiający (skrót)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"

    # Nadajemy uprawnienia wykonywania
    chmod +x "$pkgdir/usr/bin/arch-setup"
}
