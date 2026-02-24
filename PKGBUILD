# Maintainer: Sebastian <twoj@email.com>
pkgname=arch-postinstall
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
    # 1. Tworzymy foldery w wirtualnym systemie plików paczki
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # 2. Kopiujemy kod źródłowy do /opt/arch-postinstall
    # $srcdir/$pkgname to folder, gdzie makepkg ściągnął Twoje repozytorium
    cp -r "$srcdir/$pkgname/src" "$pkgdir/opt/$pkgname/"

    # --- APLIKACJA 1: INSTALATOR (arch-setup) ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"
    chmod +x "$pkgdir/usr/bin/arch-setup"

    # --- APLIKACJA 2: PRESETS (arch-presets) ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-presets"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/arch-presets"
    chmod +x "$pkgdir/usr/bin/arch-presets"

    # --- 3. PLIK .DESKTOP ---
    # Instalujemy Twój plik presets.desktop pod nazwą systemową arch-presets.desktop
    install -Dm644 "$srcdir/$pkgname/src/presets.desktop" "$pkgdir/usr/share/applications/arch-presets.desktop"
}
