# Maintainer: Sebastian <twoj@email.com>
pkgname=arch-postinstall
pkgver=2.1
pkgrel=1
pkgdesc="Arch Linux Post-Install Wizard & Theme Manager"
arch=('any')
url="https://github.com/zcharka/arch-postinstall"
license=('GPL')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'flatpak')
makedepends=('git')
source=("git+https://github.com/zcharka/arch-postinstall.git")
md5sums=('SKIP')

package() {
    # 1. Tworzymy foldery systemowe
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # 2. Kopiujemy cały kod źródłowy do /opt
    cp -r "$srcdir/$pkgname/src" "$pkgdir/opt/$pkgname/"

    # --- APLIKACJA 1: INSTALATOR (arch-setup) ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"
    chmod +x "$pkgdir/usr/bin/arch-setup"

    # --- APLIKACJA 2: MENEDŻER MOTYWÓW (linexin-themes) ---
    echo "#!/bin/sh" > "$pkgdir/usr/bin/linexin-themes"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/linexin-themes"
    chmod +x "$pkgdir/usr/bin/linexin-themes"

    # 3. Instalujemy ikonkę w menu (plik .desktop)
    install -Dm644 "$srcdir/$pkgname/src/linexin-themes.desktop" "$pkgdir/usr/share/applications/linexin-themes.desktop"

    # (Opcjonalnie) Jeśli chcesz skrót też do instalatora w menu,
    # musiałbyś stworzyć drugi plik .desktop, ale instalator zazwyczaj odpala się z terminala.
    # Theme Manager natomiast będzie widoczny w menu.
}
