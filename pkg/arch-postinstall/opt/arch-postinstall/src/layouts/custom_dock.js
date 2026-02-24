// src/layouts/custom_dock.js

// 1. Usuń istniejące panele, żeby zacząć na czysto
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) {
    allPanels[i].remove();
}

// 2. GÓRNY PASEK (Top Bar)
var topPanel = new Panel();
topPanel.location = "top";
topPanel.height = 30; // Cienki pasek
topPanel.hiding = "normal";

// Dodajemy widgety do górnego paska
// "org.kde.plasma.appmenu" to Global Menu (jak na macOS/Unity)
// Jeśli chcesz tytuł okna, użyj "org.kde.activewindowcontrol" (wymaga instalacji)
topPanel.addWidget("org.kde.plasma.appmenu");
topPanel.addWidget("org.kde.plasma.panelspacer"); // Odstęp
topPanel.addWidget("org.kde.plasma.digitalclock");
topPanel.addWidget("org.kde.plasma.systemtray");


// 3. DOLNY DOCK (Floating)
var bottomPanel = new Panel();
bottomPanel.location = "bottom";
bottomPanel.height = 48;
bottomPanel.floating = true; // Klucz do wyglądu z obrazka!
bottomPanel.alignment = "center"; // Wyśrodkowany
// To sprawia, że pasek nie jest na całą szerokość, tylko dopasowuje się do ikon
bottomPanel.lengthMode = "fit";

// Dodajemy widgety do docka
bottomPanel.addWidget("org.kde.plasma.icontasks"); // Tylko ikony
