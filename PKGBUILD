# ... (nagłówek)
package() {
    # 1. Tworzymy strukturę
    mkdir -p "$pkgdir/opt/$pkgname"
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"

    # 2. Kopiujemy źródła
    cp -r "$srcdir/$pkgname/src" "$pkgdir/opt/$pkgname/"

    # 3. Instalator
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-setup"
    echo "exec python /opt/$pkgname/src/ui/main_window.py" >> "$pkgdir/usr/bin/arch-setup"
    chmod +x "$pkgdir/usr/bin/arch-setup"

    # 4. Presets
    echo "#!/bin/sh" > "$pkgdir/usr/bin/arch-presets"
    echo "exec python /opt/$pkgname/src/ui/theme_switcher.py" >> "$pkgdir/usr/bin/arch-presets"
    chmod +x "$pkgdir/usr/bin/arch-presets"

    # 5. Desktop File
    install -Dm644 "$srcdir/$pkgname/src/presets.desktop" "$pkgdir/usr/share/applications/arch-presets.desktop"
}
