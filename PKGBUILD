# Maintainer: Sebastian <twoj@email.com>
pkgname=arch-postinstall
pkgver=2.5
pkgrel=4
pkgdesc="Arch Linux Post-Install Wizard"
arch=('any')
url="https://github.com/zcharka/arch-postinstall"
license=('GPL')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'flatpak')
makedepends=('git')
source=("git+https://github.com/zcharka/arch-postinstall.git")
md5sums=('SKIP')

package() {
    # 1. Wejdź do folderu pobranego z Gita
    cd "$srcdir/$pkgname"

    # 2. UWAGA: Wchodzimy jeszcze głębiej do zagnieżdżonego folderu!
    # To tutaj siedzą Twoje pliki ui/ i layouts/ widoczne na screenie
    cd arch-postinstall

    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # 3. Kopiujemy wszystko z tego zagnieżdżonego folderu do /opt
    cp -r . "$pkgdir/opt/$pkgname/"

    # 4. WRAPPERY (Celują w /opt/arch-postinstall/ui/...)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"
    chmod +x "$pkgdir/usr/bin/arch-setup"

    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-presets"
    echo "exec python /opt/$pkgname/ui/theme_switcher.py" >> "$pkgdir/usr/bin/arch-presets"
    chmod +x "$pkgdir/usr/bin/arch-presets"

    # 5. INSTALACJA DESKTOP
    if [ -f "ui/presets.desktop" ]; then
        install -Dm644 "ui/presets.desktop" "$pkgdir/usr/share/applications/arch-presets.desktop"
    fi
}
