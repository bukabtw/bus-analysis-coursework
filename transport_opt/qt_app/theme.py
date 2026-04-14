from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    name: str
    window_bg: str
    text: str
    muted_text: str
    header_bg: str
    header_border: str
    sidebar_bg: str
    sidebar_text: str
    sidebar_muted: str
    sidebar_hover: str
    sidebar_selected_bg: str
    sidebar_selected_text: str
    card_bg: str
    card_border: str
    input_bg: str
    input_border: str
    input_text: str
    button_bg: str
    button_hover: str
    button_text: str
    primary_bg: str
    primary_hover: str
    primary_text: str
    accent_bg: str
    accent_hover: str
    accent_text: str
    table_header_bg: str
    table_header_text: str
    table_grid: str
    selection_bg: str
    selection_text: str
    status_bg: str
    status_text: str
    chart_bg: str
    chart_plot_bg: str
    chart_text: str
    chart_muted: str
    chart_grid: str
    chart_axis: str
    recommendation_critical: str
    recommendation_warning: str
    recommendation_low: str


LIGHT_THEME = ThemePalette(
    name="light",
    window_bg="#F4F1EA",
    text="#22313A",
    muted_text="#6E7C83",
    header_bg="#FFFDF8",
    header_border="#E7DED1",
    sidebar_bg="#18323B",
    sidebar_text="#E8F0F2",
    sidebar_muted="#ADC3CA",
    sidebar_hover="rgba(255, 255, 255, 0.12)",
    sidebar_selected_bg="#E9A54A",
    sidebar_selected_text="#18323B",
    card_bg="#FFFDF8",
    card_border="#E7DED1",
    input_bg="#FFFCF7",
    input_border="#E7DED1",
    input_text="#22313A",
    button_bg="#E8DDD0",
    button_hover="#DECDB8",
    button_text="#22313A",
    primary_bg="#18323B",
    primary_hover="#244651",
    primary_text="#F8F3EA",
    accent_bg="#C2410C",
    accent_hover="#9A3412",
    accent_text="#FFF7ED",
    table_header_bg="#EFE4D4",
    table_header_text="#22313A",
    table_grid="#EEE5D9",
    selection_bg="#18323B",
    selection_text="#FFFFFF",
    status_bg="#FFFDF8",
    status_text="#22313A",
    chart_bg="#FFFFFF",
    chart_plot_bg="#F8FAFC",
    chart_text="#0F172A",
    chart_muted="#64748B",
    chart_grid="#E2E8F0",
    chart_axis="#94A3B8",
    recommendation_critical="#B91C1C",
    recommendation_warning="#B45309",
    recommendation_low="#047857",
)


DARK_THEME = ThemePalette(
    name="dark",
    window_bg="#10161A",
    text="#EAF1F3",
    muted_text="#9FB0B7",
    header_bg="#162127",
    header_border="#24343C",
    sidebar_bg="#0C1317",
    sidebar_text="#EAF1F3",
    sidebar_muted="#90A2A9",
    sidebar_hover="rgba(255, 255, 255, 0.08)",
    sidebar_selected_bg="#F2A34F",
    sidebar_selected_text="#1B2429",
    card_bg="#162127",
    card_border="#24343C",
    input_bg="#0F171B",
    input_border="#29414B",
    input_text="#EAF1F3",
    button_bg="#24343C",
    button_hover="#31464F",
    button_text="#EAF1F3",
    primary_bg="#F2A34F",
    primary_hover="#E38C32",
    primary_text="#1A2328",
    accent_bg="#14B8A6",
    accent_hover="#0D9488",
    accent_text="#071B19",
    table_header_bg="#1D2A31",
    table_header_text="#EAF1F3",
    table_grid="#24343C",
    selection_bg="#F2A34F",
    selection_text="#10161A",
    status_bg="#162127",
    status_text="#EAF1F3",
    chart_bg="#162127",
    chart_plot_bg="#111B21",
    chart_text="#EAF1F3",
    chart_muted="#9FB0B7",
    chart_grid="#29414B",
    chart_axis="#4C6570",
    recommendation_critical="#F87171",
    recommendation_warning="#FBBF24",
    recommendation_low="#34D399",
)


THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}


def get_theme(name: str) -> ThemePalette:
    return THEMES.get(name, LIGHT_THEME)


def build_stylesheet(theme: ThemePalette) -> str:
    return f"""
    QMainWindow, QWidget#shell {{
        background: {theme.window_bg};
        color: {theme.text};
    }}
    QWidget {{
        color: {theme.text};
        font-family: "Segoe UI";
        font-size: 13px;
    }}
    QLabel {{
        background: transparent;
    }}
    QStackedWidget#pageStack {{
        background: transparent;
    }}
    QFrame#headerCard, QFrame#toolbarCard, QFrame#contentCard, QFrame#metricCard {{
        background: {theme.card_bg};
        border: 1px solid {theme.card_border};
        border-radius: 16px;
    }}
    QFrame#sidebarCard {{
        background: {theme.sidebar_bg};
        border: 1px solid {theme.header_border};
        border-radius: 16px;
    }}
    QLabel#appTitle {{
        font-size: 28px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#appSubtitle, QLabel#metricNote, QLabel#pageHint {{
        color: {theme.muted_text};
        font-size: 12px;
    }}
    QLabel#metaLabel, QLabel#clockLabel {{
        color: {theme.text};
        font-size: 14px;
        font-weight: 600;
    }}
    QLabel#sidebarBrand {{
        color: {theme.sidebar_text};
        font-size: 18px;
        font-weight: 700;
    }}
    QLabel#sidebarCaption {{
        color: {theme.sidebar_muted};
        font-size: 12px;
    }}
    QLabel#sectionTitle {{
        font-size: 18px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#metricTitle {{
        color: {theme.muted_text};
        font-size: 12px;
    }}
    QLabel#metricValue {{
        font-size: 28px;
        font-weight: 700;
        color: {theme.text};
    }}
    QListWidget#navList {{
        background: transparent;
        border: none;
        color: {theme.sidebar_text};
        outline: none;
        padding: 2px;
    }}
    QListWidget#navList::item {{
        border-radius: 14px;
        padding: 12px 14px;
        margin: 4px 0;
    }}
    QListWidget#navList::item:selected {{
        background: {theme.sidebar_selected_bg};
        color: {theme.sidebar_selected_text};
        font-weight: 700;
    }}
    QListWidget#navList::item:hover:!selected {{
        background: {theme.sidebar_hover};
    }}
    QPushButton, QToolButton {{
        background: {theme.button_bg};
        border: none;
        border-radius: 12px;
        padding: 10px 16px;
        color: {theme.button_text};
        font-weight: 600;
        outline: none;
    }}
    QPushButton:hover, QToolButton:hover {{
        background: {theme.button_hover};
    }}
    QPushButton:focus, QToolButton:focus {{
        outline: none;
    }}
    QPushButton[kind="primary"] {{
        background: {theme.primary_bg};
        color: {theme.primary_text};
    }}
    QPushButton[kind="primary"]:hover {{
        background: {theme.primary_hover};
    }}
    QPushButton[kind="accent"] {{
        background: {theme.accent_bg};
        color: {theme.accent_text};
    }}
    QPushButton[kind="accent"]:hover {{
        background: {theme.accent_hover};
    }}
    QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QPlainTextEdit {{
        background: {theme.input_bg};
        border: 1px solid {theme.input_border};
        border-radius: 12px;
        padding: 8px 10px;
        color: {theme.input_text};
        selection-background-color: {theme.selection_bg};
        selection-color: {theme.selection_text};
    }}
    QListWidget, QTableWidget, QListView, QTreeView {{
        background: {theme.input_bg};
        border: 1px solid {theme.input_border};
        border-radius: 12px;
        color: {theme.input_text};
        selection-background-color: {theme.selection_bg};
        selection-color: {theme.selection_text};
        outline: none;
    }}
    QSpinBox, QTimeEdit, QDateEdit {{
        padding-right: 42px;
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus, QPlainTextEdit:focus {{
        border: 1px solid {theme.accent_bg};
        outline: none;
    }}
    QComboBox {{
        padding-right: 34px;
    }}
    QComboBox::drop-down, QDateEdit::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border: none;
        border-left: 1px solid {theme.input_border};
        border-top-right-radius: 12px;
        border-bottom-right-radius: 12px;
        background: transparent;
    }}
    QComboBox::down-arrow, QDateEdit::down-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid {theme.muted_text};
    }}
    QSpinBox::up-button, QTimeEdit::up-button, QDateEdit::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 24px;
        border: none;
        border-left: 1px solid {theme.input_border};
        border-top-right-radius: 12px;
        background: {theme.button_bg};
        margin: 1px 1px 0 0;
    }}
    QSpinBox::down-button, QTimeEdit::down-button, QDateEdit::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 24px;
        border: none;
        border-left: 1px solid {theme.input_border};
        border-bottom-right-radius: 12px;
        background: {theme.button_bg};
        margin: 0 1px 1px 0;
    }}
    QSpinBox::up-button:hover, QTimeEdit::up-button:hover, QDateEdit::up-button:hover,
    QSpinBox::down-button:hover, QTimeEdit::down-button:hover, QDateEdit::down-button:hover {{
        background: {theme.button_hover};
    }}
    QSpinBox::up-arrow, QTimeEdit::up-arrow, QDateEdit::up-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 6px solid {theme.muted_text};
    }}
    QSpinBox::down-arrow, QTimeEdit::down-arrow, QDateEdit::down-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid {theme.muted_text};
    }}
    QComboBox QAbstractItemView, QDateEdit QCalendarWidget, QCalendarWidget QWidget {{
        background: {theme.card_bg};
        color: {theme.text};
        border: 1px solid {theme.card_border};
        selection-background-color: {theme.selection_bg};
        selection-color: {theme.selection_text};
    }}
    QComboBox QAbstractItemView {{
        padding: 4px 0;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 32px;
        padding: 8px 12px;
        border: none;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: {theme.button_hover};
        color: {theme.text};
    }}
    QComboBox QAbstractItemView::item:selected {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
    }}
    QComboBox QAbstractItemView::item:selected:hover {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
    }}
    QCalendarWidget QToolButton {{
        background: {theme.button_bg};
        color: {theme.button_text};
        border-radius: 10px;
        padding: 6px;
    }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background: {theme.header_bg};
        border-bottom: 1px solid {theme.card_border};
    }}
    QCalendarWidget QTableView {{
        background: {theme.card_bg};
        alternate-background-color: {theme.card_bg};
        selection-background-color: {theme.selection_bg};
        selection-color: {theme.selection_text};
        outline: none;
    }}
    QCalendarWidget QMenu {{
        background: {theme.card_bg};
        color: {theme.text};
    }}
    QCalendarWidget QSpinBox {{
        min-width: 72px;
    }}
    QCheckBox {{
        spacing: 10px;
        color: {theme.text};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 6px;
        border: 1px solid {theme.input_border};
        background: {theme.input_bg};
    }}
    QCheckBox::indicator:hover {{
        border: 1px solid {theme.accent_bg};
    }}
    QCheckBox::indicator:checked {{
        background: {theme.accent_bg};
        border: 1px solid {theme.accent_bg};
    }}
    QSlider::groove:horizontal {{
        height: 8px;
        border-radius: 4px;
        background: {theme.table_grid};
    }}
    QSlider::sub-page:horizontal {{
        border-radius: 4px;
        background: {theme.accent_bg};
    }}
    QSlider::handle:horizontal {{
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
        background: {theme.card_bg};
        border: 2px solid {theme.accent_bg};
    }}
    QSlider::handle:horizontal:hover {{
        background: {theme.header_bg};
    }}
    QTableWidget {{
        background: {theme.input_bg};
        gridline-color: {theme.table_grid};
        alternate-background-color: {theme.header_bg};
        outline: none;
        padding: 0;
    }}
    QTableWidget::item {{
        border: none;
        padding: 8px 10px;
    }}
    QTableWidget::item:hover {{
        background: {theme.button_hover};
        color: {theme.text};
    }}
    QTableWidget::item:selected {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
    }}
    QTableWidget::item:selected:hover {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
    }}
    QTableCornerButton::section {{
        background: {theme.table_header_bg};
        border: none;
    }}
    QHeaderView::section {{
        background: {theme.table_header_bg};
        color: {theme.table_header_text};
        border: none;
        padding: 10px;
        font-weight: 700;
    }}
    QListView::item, QListWidget::item, QTreeView::item {{
        padding: 8px 12px;
        border-radius: 8px;
        margin: 2px 4px;
    }}
    QListView::item:hover, QListWidget::item:hover, QTreeView::item:hover {{
        background: {theme.button_hover};
        color: {theme.text};
    }}
    QListView::item:selected, QListWidget::item:selected, QTreeView::item:selected {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
    }}
    QListView::item:selected:hover, QListWidget::item:selected:hover, QTreeView::item:selected:hover {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
    }}
    QListWidget#recommendationList {{
        padding: 8px;
    }}
    QListWidget#recommendationList::item {{
        background: {theme.input_bg};
        border: 1px solid {theme.input_border};
        border-radius: 12px;
        padding: 10px 12px;
        margin: 3px 0;
    }}
    QListWidget#recommendationList::item:hover {{
        background: {theme.button_hover};
        color: {theme.text};
        border: 1px solid {theme.accent_bg};
    }}
    QListWidget#recommendationList::item:selected {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
        border: 1px solid {theme.selection_bg};
    }}
    QListWidget#recommendationList::item:selected:hover {{
        background: {theme.selection_bg};
        color: {theme.selection_text};
        border: 1px solid {theme.selection_bg};
    }}
    QPlainTextEdit#reportText {{
        font-family: Consolas;
        font-size: 12px;
    }}
    QScrollBar:vertical {{
        background: {theme.card_bg};
        width: 12px;
        margin: 6px 0 6px 0;
        border-radius: 6px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {theme.input_border};
        min-height: 34px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {theme.accent_bg};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
        border: none;
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: {theme.card_bg};
        height: 12px;
        margin: 0 6px 0 6px;
        border-radius: 6px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {theme.input_border};
        min-width: 34px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {theme.accent_bg};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
        border: none;
        background: transparent;
    }}
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
    }}
    QAbstractScrollArea:focus, QScrollBar:focus {{
        outline: none;
    }}
    QStatusBar {{
        background: {theme.status_bg};
        color: {theme.status_text};
        border-top: 1px solid {theme.card_border};
        padding: 4px 10px;
    }}
    QToolTip {{
        background: {theme.card_bg};
        color: {theme.text};
        border: 1px solid {theme.card_border};
        padding: 6px 8px;
    }}
    """