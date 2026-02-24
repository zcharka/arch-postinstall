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
    # 1. Tworzymy strukturę katalogów
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # 2. Kopiujemy kod źródłowy
    cp -r "$srcdir/$pkgname/src" "$pkgdir/opt/$pkgname/"

    # --- APLIKACJA 1: INSTALATOR (arch-setup) ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"
    # WAŻNE: Tu musi być ta sama nazwa co linijkę wyżej
    chmod +x "$pkgdir/usr/bin/arch-setup"

    # --- APLIKACJA 2: PRESETS (arch-presets) ---
    # Tworzymy plik 'arch-presets'
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-presets"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/arch-presets"
    # WAŻNE: Naprawiony błąd - teraz chmodujemy 'arch-presets', a nie 'presets'
    chmod +x "$pkgdir/usr/bin/arch-presets"

    # 3. Instalujemy plik .desktop
    # Upewnij się, że plik na dysku nazywa się presets.desktop!
    install -Dm644 "$srcdir/$pkgname/src/presets.desktop" "$pkgdir/usr/share/applications/arch-presets.desktop"
}
