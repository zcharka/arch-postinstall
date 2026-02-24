# src/ui/styles.py

# Paleta kolorów (Mocha / Kinexin Dark)
# Tło: #1e1e2e
# Akcent (Fiolet): #cba6f7
# Tekst: #cdd6f4
# Sukces (Zieleń): #a6e3a1
# Konsola: #11111b

STYLESHEET = """
/* --- GŁÓWNE OKNO --- */
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QWidget {
    font-family: 'Segoe UI', 'Noto Sans', sans-serif;
    font-size: 14px;
    color: #cdd6f4;
}

/* --- ETYKIETY (Tekst) --- */
QLabel {
    color: #cdd6f4;
}

/* Nagłówki */
QLabel#Title {
    font-size: 26px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 10px;
}

/* Status (np. "Instalowanie...") */
QLabel#StatusLabel {
    font-size: 14px;
    color: #bac2de;
    font-style: italic;
}

/* Sukces (np. "Gotowe!") */
QLabel#SuccessLabel {
    font-size: 28px;
    font-weight: bold;
    color: #a6e3a1; /* Jasna zieleń */
}

/* --- PRZYCISKI --- */

/* Główny przycisk (Fioletowy) */
QPushButton#PrimaryBtn {
    background-color: #cba6f7;
    color: #1e1e2e; /* Ciemny tekst na jasnym tle */
    font-weight: bold;
    font-size: 16px;
    border-radius: 20px; /* Mocne zaokrąglenie */
    padding: 12px 30px;
    border: none;
}

QPushButton#PrimaryBtn:hover {
    background-color: #d8b4fe; /* Jaśniejszy fiolet po najechaniu */
}

QPushButton#PrimaryBtn:pressed {
    background-color: #b492e0; /* Ciemniejszy przy kliknięciu */
    padding-top: 14px; /* Efekt wciskania */
    padding-bottom: 10px;
}

QPushButton#PrimaryBtn:disabled {
    background-color: #45475a;
    color: #7f849c;
}

/* Przycisk dodatkowy (Przezroczysty / Outline) */
QPushButton#DetailsBtn {
    background-color: transparent;
    color: #a6adc8;
    border: 1px solid #45475a;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 12px;
}

QPushButton#DetailsBtn:hover {
    background-color: #313244;
    color: #cdd6f4;
    border-color: #585b70;
}

QPushButton#DetailsBtn:checked {
    background-color: #45475a;
    color: #ffffff;
    border-color: #cba6f7;
}

/* --- PASEK POSTĘPU --- */
QProgressBar {
    background-color: #313244; /* Ciemne tło paska */
    border-radius: 10px;
    height: 12px;
    text-align: center;
    border: none;
}

QProgressBar::chunk {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #cba6f7, stop:1 #f5c2e7); /* Gradient Fiolet -> Róż */
    border-radius: 10px;
}

/* --- KONSOLA / LOGI --- */
QTextEdit {
    background-color: #11111b; /* Prawie czarny */
    color: #a6adc8;
    border: 1px solid #313244;
    border-radius: 12px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    padding: 10px;
    selection-background-color: #cba6f7;
    selection-color: #1e1e2e;
}

/* --- PASEK PRZEWIJANIA (SCROLLBAR) --- */
/* Ważne dla nowoczesnego wyglądu */
QScrollBar:vertical {
    border: none;
    background: #1e1e2e;
    width: 8px;
    margin: 0px 0px 0px 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #45475a;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #585b70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* --- OKNA DIALOGOWE (np. pytania o hasło) --- */
QInputDialog {
    background-color: #1e1e2e;
}

QLineEdit {
    background-color: #313244;
    color: white;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 5px;
    selection-background-color: #cba6f7;
}

QLineEdit:focus {
    border: 1px solid #cba6f7;
}
"""
