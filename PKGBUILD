# Maintainer: Sebastian <twoj@email.com>
pkgname=arch-postinstall
pkgver=2.5
pkgrel=7
pkgdesc="Arch Linux Post-Install Wizard & Presets"
arch=('any')
url="https://github.com/zcharka/arch-postinstall"
license=('GPL')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'flatpak')
makedepends=('git')
source=("git+https://github.com/zcharka/arch-postinstall.git")
md5sums=('SKIP')

package() {
    # UWAGA: Nie używamy 'cd', bo makepkg automatycznie wprowadza nas do folderu źródłowego

    # 1. Tworzymy strukturę katalogów wewnątrz paczki
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # 2. Kopiujemy całą zawartość repozytorium do /opt/arch-postinstall
    # Kropka oznacza kopiowanie wszystkiego z bieżącego folderu roboczego
    cp -r . "$pkgdir/opt/$pkgname/"

    # --- WRAPPERY (Skrypty startowe w /usr/bin) ---

    # Instalator (arch-setup)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"
    chmod +x "$pkgdir/usr/bin/arch-setup"

    # Presety (arch-presets)
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-presets"
    echo "exec python /opt/$pkgname/ui/theme_switcher.py" >> "$pkgdir/usr/bin/arch-presets"
    chmod +x "$pkgdir/usr/bin/arch-presets"

    # --- IKONA I SKRÓT (.desktop) ---
    if [ -f "presets.desktop" ]; then
        install -Dm644 "presets.desktop" "$pkgdir/usr/share/applications/arch-presets.desktop"
    fi
}
