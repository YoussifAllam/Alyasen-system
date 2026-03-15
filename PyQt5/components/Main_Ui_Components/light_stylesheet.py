def load_light_theme():
    """Returns the QSS stylesheet for the entire application in light theme."""
    return """
        #mainContainer {
             background-color: #ECEBDE;
             border: 1px solid #C1BAA1;
        }
        /*#! --- Sidebar Styles --- */
        #sidebar {
            background-color: #819A91;
            max-width: 220px;
        }
        #sidebarTitle {
            color: #000000; font-size: 24px; font-weight: bold;
        }
        #sidebar QPushButton {
            color: #000000; background-color: transparent; border: none; padding: 12px;
            font-size: 15px; text-align: left; padding-left: 15px; border-radius: 8px;
        }
        #sidebar QPushButton:hover { background-color: #A7C1A8; }
        #sidebar QPushButton#active {
            background-color: #D1D8BE; color: #819A91; font-weight: bold;
        }

        #userName { color: #ECEBDE; font-weight: bold;font-size: 16px;  }

        /*#! --- Main Content & Dashboard Styles --- */
        #mainContent {
            background-color: #ECEBDE; color: #5A5548;
        }
        #mainHeader { font-size: 26px; font-weight: bold; color: #819A91; }
        #mainSubheader { font-size: 14px; color: #A59D84; }

        #dashboardScrollArea {
            border: none;
            background-color: transparent;
        }

        #card {
            background-color: #EEEFE0;
            border: 1px solid #D7D3BF;
            border-radius: 8px;
            padding: 15px;
        }
        #kpiTitle { font-size: 14px; font-weight: bold; color: #819A91; }
        #kpiValue { font-size: 26px; font-weight: 900; color: #5A5548; }
        #kpiSubtitle { font-size: 12px; color: #A59D84; }
        #cardTitle { font-size: 17px; font-weight: bold; color: #819A91; }

        QProgressBar {
            background-color: #D7D3BF; border-radius: 4px; height: 8px;
        }
        QProgressBar::chunk {
            background-color: #819A91; border-radius: 4px;
        }
        QProgressBar#warningProgressBar::chunk {
            background-color: #A7C1A8;
        }

        /*#! --- Chart Styles --- */
        #salesBar { background-color: #819A91; border-radius: 4px; }
        #expenseBar { background-color: #A59D84; border-radius: 4px; }
        #donutCenterText { font-size: 36px; font-weight: 900; color: #819A91; }
        #legendLabel { font-size: 15px; font-weight: bold; }

        /*#! --- GroupBox and Form Styles --- */
        QGroupBox {
            background-color: #EEEFE0; border: 1px solid #D7D3BF; border-radius: 8px;
            margin-top: 10px; padding: 20px; font-size: 16px; font-weight: bold; color: #819A91;
        }
        QGroupBox::title {
            subcontrol-origin: margin; subcontrol-position: top right; padding: 0 10px;
        }
        QLabel { color: #5A5548; font-size: 18px; }
        QLineEdit, QDateEdit, QTextEdit, QComboBox {
            background-color: #ffffff; border: 1px solid #D7D3BF; border-radius: 6px;
            padding: 10px; color: #5A5548; font-size: 18px;
        }
        QLineEdit:focus, QDateEdit:focus, QTextEdit:focus, QComboBox:focus { border-color: #819A91; }

        /*#! NEW: Styles for the ComboBox dropdown list */
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
             background-color: #ffffff;
             border: 1px solid #D7D3BF;
             selection-background-color: #EEEFE0;
             color: #5A5548;
             padding: 5px;
        }

        /*#! --- NEW: Report Panel Styles --- */
        #reportItemCard {
            background-color: #ECEBDE;
            border: 1px solid #D7D3BF;
            border-radius: 8px;
            padding: 15px;
        }
        #reportItemLabel {
            font-size: 16px;
            font-weight: bold;
        }
        #reportItemValue {
            font-size: 22px;
            font-weight: bold;
            border: none;
            background-color: transparent;
        }

        /*#! --- NEW: Styles for the Calendar Popup --- */
        QDateEdit QCalendarWidget QWidget#qt_calendar_navigationbar {
            background-color: #EEEFE0;
        }
        QDateEdit QCalendarWidget QToolButton {
            color: #819A91;
            font-size: 14px;
            background-color: #EEEFE0;
            border: none;
            margin: 5px;
            border-radius: 4px;
        }
        QDateEdit QCalendarWidget QToolButton:hover {
            background-color: #D7D3BF;
        }
        QDateEdit QCalendarWidget QMenu {
            background-color: #EEEFE0;
            color: #819A91;
        }
        QDateEdit QCalendarWidget QMenu::item:selected {
            background-color: #D7D3BF;
        }
        QDateEdit QCalendarWidget QTableView {
            background-color: #ffffff;
            gridline-color: #D7D3BF;
        }
        QDateEdit QCalendarWidget QHeaderView::section {
            background-color: #EEEFE0;
            color: #A59D84;
            padding: 5px;
            border: none;
        }
        QDateEdit QCalendarWidget QTableView::item {
            color: #5A5548;
            background-color: transparent;
            border-radius: 4px;
        }
        QDateEdit QCalendarWidget QTableView::item:selected {
            background-color: #D7D3BF;
            color: #5A5548;
        }
        QDateEdit QCalendarWidget QTableView::item:disabled {
            color: #C1BAA1;
        }

        /*#! --- Generic Button Styles --- */
        QPushButton {
            background-color: #D7D3BF; color: #5A5548; border: 1px solid #C1BAA1;
            border-radius: 6px; padding: 10px 20px; font-size: 14px; font-weight: bold;
        }
        QPushButton:hover { background-color: #C1BAA1; }
        QPushButton#primaryButton { background-color: #819A91; color: #ffffff; border: none; }
        QPushButton#primaryButton:hover { background-color: #6B857C; }
        QPushButton#successButton { background-color: #A7C1A8; color: white; border: none; }
        QPushButton#successButton:hover { background-color: #95AE96; }
        QPushButton#dangerButton { background-color: #A59D84; color: white; border: none; }
        QPushButton#dangerButton:hover { background-color: #8F8770; }

        /*#! --- Custom Dialog Styles --- */
       QDialog {
            background-color: transparent;
            border: none;
        }

        #dialogContainer {
            background-color: #EEEFE0;
            border: 1px solid #C1BAA1;
            border-radius: 8px;
        }
        #dialogTitleBar {
            background-color: #ECEBDE;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }


        /*#! --- Table Styles --- */
        QTableWidget {
            background-color: #EEEFE0;
            border: 1px solid #D7D3BF;
            border-radius: 8px;
            alternate-background-color: #ffffff;
            gridline-color: #D7D3BF;
            color: #5A5548;
            font-size: 18px;
        }

        /*#! --- NEW: ScrollBar Styles --- */
        QScrollBar:horizontal {
            border: none;
            background: #ECEBDE;
            height: 12px;
            margin: 0px 15px 0 15px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal {
            background: #819A91;
            min-width: 20px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #6B857C;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        QScrollBar:vertical {
            border: none;
            background: #ECEBDE;
            width: 12px;
            margin: 15px 0 15px 0;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #819A91;
            min-height: 20px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #6B857C;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }

        /*#! Hides the vertical row numbers */
        QTableWidget::vertical-header {
            width: 0px;
        }
        QHeaderView::section:vertical {
            width: 0px;
            max-width: 0px;
            border: none;
            padding: 0px;
            margin: 0px;
        }

        QTableWidget::vertical-header {
            width: 0px;
            max-width: 0px;
            border: none;
        }

        QHeaderView::section {
            background-color: #D7D3BF;
            color: #5A5548;
            padding: 10px;
            border: none;
            font-weight: bold;
            border-bottom: 1px solid #C1BAA1;
            font-size: 18px;
        }

        /*#! FIXED: Proper item styling with centering */
        QTableWidget::item {
            padding: 8px; /*#! Reduced padding for better centering */
            border: none;
            font-size: 18px;
            text-align: center; /*#! Horizontal centering */
        }

        /*#! Ensure proper vertical centering */
        QTableWidget::item {
            padding-top: 12px;
            padding-bottom: 12px;
        }

        QTableWidget::item:selected {
            background-color: #A7C1A8;
            color: #ffffff;
        }

        /*#! Alternative: More specific centering approach */
        QTableWidget QTableCornerButton::section {
            background-color: #D7D3BF;
        }

        /*#! --- Login/Signup Window Styles --- */
        #loginCard {
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
            stop:0 rgba(236, 235, 222, 0.9), stop:1 rgba(215, 211, 191, 0.95));
            border-radius: 20px;
            border: 1px solid #C1BAA1;
        }
        #titleLabel {
            font-size: 36px;
            font-weight: bold;
            color: #819A91;
        }
        #subtitleLabel {
            font-size: 18px;
            color: #5A5548;
        }
        #inputField {
            background-color: #ffffff;
            border: 1px solid #D7D3BF;
            border-radius: 8px;
            padding: 16px;
            color: #5A5548;
            font-size: 18px;
        }
        QLineEdit[echoMode="2"] {
            padding-left: 40px;
        }
        #inputField:focus {
            border-color: #819A91;
        }
        #loginButton {
            background-color: #819A91;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 16px;
            font-size: 18px;
            font-weight: bold;
        }
        #loginButton:hover {
            background-color: #6B857C;
        }

        QPushButton#linkButton {
            background-color: transparent;
            border: none;
            color: #A59D84;
            font-size: 14px;
            text-align: center;
            padding: 5px;
        }
        QPushButton#linkButton:hover {
            text-decoration: underline;
            color: #819A91;
        }

        /*#! --- Checkbox Styles --- */
        QCheckBox#rememberMeCheckbox, QCheckBox#filterCheckbox,
        QCheckBox#reportFieldCheckbox, QCheckBox#vacationcheckbox {
            font-size: 18px;
            color: #5A5548;
            spacing: 10px;
        }
        QCheckBox#rememberMeCheckbox::indicator, QCheckBox#filterCheckbox::indicator,
        QCheckBox#reportFieldCheckbox::indicator, QCheckBox#vacationcheckbox::indicator {
            width: 18px;
            height: 18px;
            background-color: #ffffff;
            border: 1px solid #D7D3BF;
            border-radius: 5px;
        }
        QCheckBox#rememberMeCheckbox::indicator:hover, QCheckBox#filterCheckbox::indicator:hover,
        QCheckBox#reportFieldCheckbox::indicator:hover, QCheckBox#vacationcheckbox::indicator:hover {
            border: 1px solid #819A91;
        }
        QCheckBox#rememberMeCheckbox::indicator:checked, QCheckBox#filterCheckbox::indicator:checked,
        QCheckBox#reportFieldCheckbox::indicator:checked, QCheckBox#vacationcheckbox::indicator:checked {
            background-color: #819A91;
            border: 1px solid #819A91;
        }

        /*#! --- New Sign-up & Dialog Styles --- */
        #userTypeLabel {
            font-size: 16px;
            color: #5A5548;
            font-weight: bold;
            margin-top: 10px;
        }
        #userTypeButton {
            padding: 14px;
            font-size: 16px;
        }
        #userTypeButton:checked {
            background-color: #819A91;
            border-color: #819A91;
            color: #ffffff;
        }

        /*#! --- NEW: Custom Title Bar Styles --- */
        #titleBar {
            background-color: #ECEBDE;
            height: 40px;
            border-bottom: 1px solid #D7D3BF;
        }
        #titleBarText {
            color: #5A5548;
            font-size: 15px;
            font-weight: bold;
        }
        QPushButton#titleBarButton {
            background-color: transparent;
            border: none;
            width: 45px;
            height: 40px;
            border-radius: 0px;
        }
        QPushButton#titleBarButton:hover {
            background-color: #D7D3BF;
        }
        QPushButton#closeButton {
             background-color: transparent;
            border: none;
            width: 45px;
            height: 40px;
            border-radius: 0px;
        }
        QPushButton#closeButton:hover {
            background-color: #A59D84;
        }
    """
