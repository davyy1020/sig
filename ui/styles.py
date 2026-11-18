# =============================================================================
# styles.py - Algarae Carbon Flow Theme (Sleek SaaS & Neo-Brutalist Kiosk Edition)
# =============================================================================
# A dark, high-end dashboard theme inspired by modern carbon flow applications.
# Designed with crisp borders, a balanced font scale, and green/cyan gradients.
# Eliminates standard PyQt clunkiness in favor of micro-glowing focus states.
# =============================================================================

DARK_STYLE = '''
/* =========================================================================
   GLOBAL / BASE STYLES
   ========================================================================= */

QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #050814,
                                stop:0.5 #0B132B, /* High-contrast cobalt indigo space */
                                stop:1 #02040A);
    color: #F8FAFC;
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 16px;
}

/* Use dot selector to avoid background color propagation to sub-widgets */
.QWidget#central_widget, QStackedWidget, QScrollArea, QScrollArea > QWidget {
    background: transparent;
}

QWidget {
    color: #F8FAFC;
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 16px;
}

QDialog {
    background-color: rgba(10, 15, 30, 0.9);
    color: #F8FAFC;
    border: 1.5px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
}

/* =========================================================================
   BUTTONS
   ========================================================================= */

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00F5D4, stop:1 #10B981);
    color: #050A18; /* Deep rich dark text for outstanding contrast */
    border: none;
    border-radius: 12px;
    padding: 10px 24px;
    font-size: 18px;
    font-weight: 700;
    font-family: "Segoe UI", "Inter", sans-serif;
    min-height: 52px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #33FFEB, stop:1 #34D399);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00D1B2, stop:1 #059669);
}

QPushButton:disabled {
    background-color: #151F32;
    border: 1.5px solid #1E293B;
    color: #475569;
}

/* Specific buttons mapped by object names */
QPushButton#secondary_btn {
    background-color: rgba(6, 182, 212, 0.12);
    color: #00F5D4;
    border: 1.5px solid rgba(0, 245, 212, 0.5);
}
QPushButton#secondary_btn:hover {
    background-color: rgba(6, 182, 212, 0.22);
    color: #33FFEB;
    border: 1.5px solid #00F5D4;
}
QPushButton#secondary_btn:pressed {
    background-color: rgba(6, 182, 212, 0.35);
    color: #00D1B2;
    border: 1.5px solid #00D1B2;
}

QPushButton#danger_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF5E62, stop:1 #FF9966);
    color: #FFFFFF;
    border: none;
}
QPushButton#danger_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF7376, stop:1 #FFAA80);
}
QPushButton#danger_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E04D51, stop:1 #E08556);
}

QPushButton#warning_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F59E0B, stop:1 #FFD700);
    color: #050A18;
    border: none;
}
QPushButton#warning_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FBBF24, stop:1 #FFE033);
}
QPushButton#warning_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #E6B800);
}

QPushButton#ghost_btn {
    background-color: rgba(255, 255, 255, 0.03);
    color: #F1F5F9;
    border: 1.5px solid rgba(255, 255, 255, 0.15);
}
QPushButton#ghost_btn:hover {
    background-color: rgba(0, 245, 212, 0.08);
    border-color: #00F5D4;
    color: #00F5D4;
}
QPushButton#ghost_btn:pressed {
    background-color: rgba(0, 245, 212, 0.15);
    border-color: #00D1B2;
    color: #00D1B2;
}

/* =========================================================================
   TEXT INPUTS & EDIT WIDGETS
   ========================================================================= */

QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: rgba(5, 8, 16, 0.9); /* Deep high-contrast obsidian input */
    border: 1.5px solid rgba(255, 255, 255, 0.15); /* Clean visible border */
    border-radius: 10px;
    padding: 11px 15px;
    color: #FFFFFF; /* Pure high-contrast white text */
    font-size: 18px;
    font-weight: 600;
    font-family: "Segoe UI", sans-serif;
    min-height: 52px;
}

QLineEdit:hover, QDateEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border: 1.5px solid rgba(0, 245, 212, 0.75); /* Glowing Neon Teal hover */
}

QLineEdit:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 2px solid #00F5D4; /* Glowing Neon Teal active focus border */
    background-color: rgba(0, 245, 212, 0.05); /* Aqua active tint */
}

QLineEdit:disabled, QDateEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {
    background-color: rgba(15, 23, 42, 0.5);
    border-color: rgba(255, 255, 255, 0.05);
    color: #64748B;
}

QLineEdit::placeholder {
    color: #94A3B8; /* High-visibility medium silver placeholder */
    font-size: 17px;
}

/* =========================================================================
   SPIN BOX UP/DOWN CONTROLS
   ========================================================================= */

QSpinBox::up-button, QDoubleSpinBox::up-button, QDateEdit::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1.5px solid #23314B;
    border-bottom: 1.5px solid #23314B;
    background-color: #0B0F19;
    border-top-right-radius: 7px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QDateEdit::up-button:hover {
    background-color: #1E293B;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QDateEdit::up-arrow {
    width: 8px;
    height: 8px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #94A3B8;
}

QSpinBox::down-button, QDoubleSpinBox::down-button, QDateEdit::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 28px;
    border-left: 1.5px solid #23314B;
    background-color: #0B0F19;
    border-bottom-right-radius: 7px;
}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover, QDateEdit::down-button:hover {
    background-color: #1E293B;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QDateEdit::down-arrow {
    width: 8px;
    height: 8px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94A3B8;
}

/* =========================================================================
   COMBO BOX WIDGETS
   ========================================================================= */

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border-left: 1.5px solid #23314B;
    background-color: #0B0F19;
    border-top-right-radius: 7px;
    border-bottom-right-radius: 7px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94A3B8;
}

QComboBox QAbstractItemView {
    background-color: #0B0F19;
    color: #F8FAFC;
    border: 1.5px solid #1E293B;
    selection-background-color: #1E293B;
    selection-color: #10B981;
    padding: 6px;
    border-radius: 8px;
}

/* =========================================================================
   LABELS (Typography & Accents)
   ========================================================================= */

QLabel {
    color: #F1F5F9;
    font-size: 17px;
    font-weight: 500;
    font-family: "Segoe UI", "Inter", sans-serif;
    background-color: transparent;
    border: none;
}

QLabel#title_label {
    font-size: 34px;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.5px;
}

QLabel#subtitle_label {
    font-size: 19px;
    font-weight: 600;
    color: #94A3B8;
}

QLabel#secondary_label {
    color: #94A3B8;
    font-size: 16px;
    font-weight: 500;
}

QLabel#field_label {
    color: #FFFFFF; /* Pure high-contrast white */
    font-size: 18px;
    font-weight: 700; /* Bold field label */
    padding-bottom: 4px;
}

QLabel#stat_value {
    font-size: 42px;
    font-weight: 800;
    color: #00F5D4; /* Glowing Neon Teal value */
    font-family: "Segoe UI", "Inter", sans-serif;
}

/* Embedded Card Titles */
QLabel#card_title {
    font-size: 22px;
    font-weight: 800;
    color: #00F5D4; /* Glowing Neon Teal */
    padding-bottom: 10px;
    border-bottom: 1.5px solid rgba(0, 245, 212, 0.25); /* Cyan-Teal matching separator */
}

/* =========================================================================
   TABLE WIDGETS
   ========================================================================= */

QTableWidget {
    background-color: #0D1321;
    alternate-background-color: #090E17;
    color: #F8FAFC;
    gridline-color: #1E293B;
    border: 1px solid #1E293B;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 500;
    selection-background-color: #1E293B;
    selection-color: #10B981;
}

QTableWidget::item {
    padding: 14px 18px;
    border-bottom: 1px solid #1E293B;
}

QTableWidget::item:selected {
    background-color: #1E293B;
    color: #10B981;
}

QHeaderView {
    background-color: #090E17;
    border: none;
}

QHeaderView::section {
    background-color: #090E17;
    color: #94A3B8;
    border: none;
    border-bottom: 2px solid #1E293B;
    border-right: 1px solid #1E293B;
    padding: 14px 18px;
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QHeaderView::section:hover {
    background-color: #1E293B;
}

/* =========================================================================
   SCROLLBAR STYLING (Ultra-Thin Minimalist)
   ========================================================================= */

QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #1E293B;
    min-height: 32px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* =========================================================================
   CARDS / GROUP BOXES
   ========================================================================= */

QGroupBox, QFrame#card_frame, QFrame#sensor_card {
    background-color: rgba(8, 14, 28, 0.82); /* Sleek translucent deep obsidian glass */
    border: 1.5px solid rgba(0, 245, 212, 0.18); /* Subtle neon teal outer glow edge */
    border-radius: 18px;
    margin-top: 0px;
    padding: 0px;
}

/* Completely remove native QGroupBox title drawing */
QGroupBox::title {
    width: 0px;
    height: 0px;
    padding: 0px;
    margin: 0px;
    border: none;
    background: transparent;
}

/* =========================================================================
   PROGRESS BARS
   ========================================================================= */

QProgressBar {
    background-color: #080C14;
    border: 1px solid #1E293B;
    border-radius: 8px;
    text-align: center;
    color: transparent;
    min-height: 18px;
    max-height: 18px;
}

QProgressBar::chunk {
    background-color: #06B6D4;
    border-radius: 6px;
}

/* =========================================================================
   STATUS BAR
   ========================================================================= */

QStatusBar {
    background-color: #06090F;
    color: #64748B;
    border-top: 1px solid #1E293B;
    font-size: 13px;
    padding: 6px 16px;
}
QStatusBar::item {
    border: none;
}

/* =========================================================================
   FRAMES (Modular Panels)
   ========================================================================= */

QFrame#card_frame, QFrame#sensor_card {
    background-color: rgba(8, 14, 28, 0.82);
    border: 1.5px solid rgba(0, 245, 212, 0.18);
    border-radius: 18px;
    padding: 20px;
}
'''


def get_button_style(style_type='primary') -> str:
    """
    Returns specific button CSS styling to maintain visual hierarchy.
    """
    base_btn = '''
        QPushButton {
            border: none;
            border-radius: 12px;
            padding: 10px 24px;
            font-size: 18px;
            font-weight: 700;
            font-family: "Segoe UI", "Inter", sans-serif;
            min-height: 52px;
        }
        QPushButton:disabled {
            background-color: #151F32;
            border: 1.5px solid #1E293B;
            color: #475569;
        }
    '''

    styles = {
        'primary': base_btn + '''
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F5D4, stop:1 #10B981); color: #050A18; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33FFEB, stop:1 #34D399); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D1B2, stop:1 #059669); }
        ''',
        'secondary': base_btn + '''
            QPushButton { background-color: rgba(6, 182, 212, 0.12); color: #00F5D4; border: 1.5px solid rgba(0, 245, 212, 0.5); }
            QPushButton:hover { background-color: rgba(6, 182, 212, 0.22); color: #33FFEB; border: 1.5px solid #00F5D4; }
            QPushButton:pressed { background-color: rgba(6, 182, 212, 0.35); color: #00D1B2; border: 1.5px solid #00D1B2; }
        ''',
        'danger': base_btn + '''
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF5E62, stop:1 #FF9966); color: #FFFFFF; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF7376, stop:1 #FFAA80); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E04D51, stop:1 #E08556); }
        ''',
        'warning': base_btn + '''
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F59E0B, stop:1 #FFD700); color: #050A18; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FBBF24, stop:1 #FFE033); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #E6B800); }
        ''',
        'ghost': base_btn + '''
            QPushButton { background-color: rgba(255, 255, 255, 0.03); color: #F1F5F9; border: 1.5px solid rgba(255, 255, 255, 0.15); }
            QPushButton:hover { background-color: rgba(0, 245, 212, 0.08); border-color: #00F5D4; color: #00F5D4; }
            QPushButton:pressed { background-color: rgba(0, 245, 212, 0.15); border-color: #00D1B2; color: #00D1B2; }
        ''',
    }

    return styles.get(style_type, styles['primary'])


def get_progress_bar_style(color='#06B6D4') -> str:
    """
    Returns a styled progress bar with a customizable color accent.
    """
    return f'''
        QProgressBar {{
            background-color: #080C14;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            text-align: center;
            color: transparent;
            min-height: 18px;
            max-height: 18px;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 6px;
        }}
    '''
