# Maintainer: Sebastian <twoj@email.com>
pkgname=arch-postinstall
pkgver=2.3
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
    # Tworzenie folderów
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # Kopiowanie kodu
    cp -r "$srcdir/$pkgname/src" "$pkgdir/opt/$pkgname/"

    # --- 1. GŁÓWNY INSTALATOR (arch-setup) ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"
    chmod +x "$pkgdir/usr/bin/arch-setup"

    # --- 2. PRESETS (arch-presets) ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-presets"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/arch-presets"
    chmod +x "$pkgdir/usr/bin/arch-presets"

    # --- 3. PLIK .DESKTOP (Twoja zmiana) ---
    # Tutaj wskazujemy na Twój nowy plik presets.desktop
    install -Dm644 "$srcdir/$pkgname/src/presets.desktop" "$pkgdir/usr/share/applications/presets.desktop"
}
