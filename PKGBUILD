# Maintainer: Sebastian

pkgname=archrat-git
pkgver=1.0.0
pkgrel=1
pkgdesc="ArchRat - Post installation scripts for GNOME and KDE on Arch"
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
  
  install -d "$pkgdir/usr/share/archrat"
  install -d "$pkgdir/usr/bin"
  install -d "$pkgdir/usr/share/applications"
  
  install -Dm755 main.py "$pkgdir/usr/share/archrat/main.py"
  install -Dm755 gnome.sh "$pkgdir/usr/share/archrat/gnome.sh"
  install -Dm755 kde.sh "$pkgdir/usr/share/archrat/kde.sh"
  
  # Wygeneruj skrypt uruchomieniowy
  cat <<EOF > "$pkgdir/usr/bin/archrat"
#!/bin/bash
exec python /usr/share/archrat/main.py "\$@"
EOF
  chmod 755 "$pkgdir/usr/bin/archrat"
  
  install -Dm644 archrat.desktop "$pkgdir/usr/share/applications/archrat.desktop"
}
