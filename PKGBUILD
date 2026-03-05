# Maintainer: Sebastian

pkgname=rat-center-git
pkgver=1.0.0
pkgrel=1
pkgdesc="Rat Center - Post installation scripts for GNOME and KDE on Arch"
arch=('any')
url="https://github.com/example/rat-center"
license=('GPL')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita')
makedepends=('git')
source=()
md5sums=()

# Używamy lokalnego katalogu jako źródła dla łatwego budowania
# przy użyciu polecenia: makepkg -si

package() {
  cd "$srcdir/.."
  
  install -d "$pkgdir/usr/share/rat-center"
  install -d "$pkgdir/usr/bin"
  install -d "$pkgdir/usr/share/applications"
  
  install -Dm755 main.py "$pkgdir/usr/share/rat-center/main.py"
  install -Dm755 gnome.sh "$pkgdir/usr/share/rat-center/gnome.sh"
  install -Dm755 kde.sh "$pkgdir/usr/share/rat-center/kde.sh"
  
  # Wygeneruj skrypt uruchomieniowy
  cat <<EOF > "$pkgdir/usr/bin/rat-center"
#!/bin/bash
exec python /usr/share/rat-center/main.py "\$@"
EOF
  chmod 755 "$pkgdir/usr/bin/rat-center"
  
  install -Dm644 rat-center.desktop "$pkgdir/usr/share/applications/rat-center.desktop"
}
