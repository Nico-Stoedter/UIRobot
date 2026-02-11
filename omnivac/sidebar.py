# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sidebar.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QStackedWidget, QVBoxLayout,
    QWidget)
from omnivac import resource_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1640, 1020)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.icon_only_widget = QWidget(self.centralwidget)
        self.icon_only_widget.setObjectName(u"icon_only_widget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.icon_only_widget.sizePolicy().hasHeightForWidth())
        self.icon_only_widget.setSizePolicy(sizePolicy)
        self.icon_only_widget.setMaximumSize(QSize(100, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.icon_only_widget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.sidbar_label = QLabel(self.icon_only_widget)
        self.sidbar_label.setObjectName(u"sidbar_label")
        self.sidbar_label.setMinimumSize(QSize(50, 50))
        self.sidbar_label.setMaximumSize(QSize(50, 50))
        self.sidbar_label.setPixmap(QPixmap(u"icon/omnivac.ico"))
        self.sidbar_label.setScaledContents(True)

        self.horizontalLayout.addWidget(self.sidbar_label)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.comport_btn = QPushButton(self.icon_only_widget)
        self.comport_btn.setObjectName(u"comport_btn")
        icon = QIcon()
        icon.addFile(u":/icon/icon/settings-10-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.comport_btn.setIcon(icon)
        self.comport_btn.setIconSize(QSize(20, 20))
        self.comport_btn.setCheckable(True)
        self.comport_btn.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.comport_btn)

        self.motor_btn = QPushButton(self.icon_only_widget)
        self.motor_btn.setObjectName(u"motor_btn")
        icon1 = QIcon()
        icon1.addFile(u":/icon/icon/dashboard-2-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.motor_btn.setIcon(icon1)
        self.motor_btn.setIconSize(QSize(20, 20))
        self.motor_btn.setCheckable(True)
        self.motor_btn.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.motor_btn)

        self.reset_btn = QPushButton(self.icon_only_widget)
        self.reset_btn.setObjectName(u"reset_btn")
        icon2 = QIcon()
        icon2.addFile(u"icon/icons8-neustart-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.reset_btn.setIcon(icon2)
        self.reset_btn.setIconSize(QSize(20, 20))
        self.reset_btn.setCheckable(True)
        self.reset_btn.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.reset_btn)

        self.help_btn = QPushButton(self.icon_only_widget)
        self.help_btn.setObjectName(u"help_btn")
        icon3 = QIcon()
        icon3.addFile(u":/icon/icon/help-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.help_btn.setIcon(icon3)
        self.help_btn.setIconSize(QSize(20, 20))
        self.help_btn.setCheckable(True)
        self.help_btn.setAutoExclusive(True)

        self.verticalLayout.addWidget(self.help_btn)

        self.enable_all_btn = QPushButton(self.icon_only_widget)
        self.enable_all_btn.setObjectName(u"enable_all_btn")
        icon4 = QIcon()
        icon4.addFile(u"icon/icons8-abschalttaste-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.enable_all_btn.setIcon(icon4)
        self.enable_all_btn.setIconSize(QSize(20, 20))
        self.enable_all_btn.setCheckable(False)
        self.enable_all_btn.setAutoExclusive(False)

        self.verticalLayout.addWidget(self.enable_all_btn)

        self.disable_all_btn = QPushButton(self.icon_only_widget)
        self.disable_all_btn.setObjectName(u"disable_all_btn")
        icon5 = QIcon()
        icon5.addFile(u"icon/icons8-power-off-button-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.disable_all_btn.setIcon(icon5)
        self.disable_all_btn.setIconSize(QSize(20, 20))
        self.disable_all_btn.setCheckable(False)
        self.disable_all_btn.setAutoExclusive(False)

        self.verticalLayout.addWidget(self.disable_all_btn)

        self.stop_btn = QPushButton(self.icon_only_widget)
        self.stop_btn.setObjectName(u"stop_btn")
        icon6 = QIcon()
        icon6.addFile(u"icon/error-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.stop_btn.setIcon(icon6)
        self.stop_btn.setIconSize(QSize(20, 20))
        self.stop_btn.setCheckable(False)
        self.stop_btn.setAutoExclusive(False)

        self.verticalLayout.addWidget(self.stop_btn)


        self.verticalLayout_3.addLayout(self.verticalLayout)

        self.verticalSpacer = QSpacerItem(20, 415, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.exit_btn = QPushButton(self.icon_only_widget)
        self.exit_btn.setObjectName(u"exit_btn")
        self.exit_btn.setIconSize(QSize(20, 20))
        self.exit_btn.setCheckable(True)
        self.exit_btn.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.exit_btn)


        self.horizontalLayout_3.addWidget(self.icon_only_widget)

        self.full_menu_widget = QWidget(self.centralwidget)
        self.full_menu_widget.setObjectName(u"full_menu_widget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.full_menu_widget.sizePolicy().hasHeightForWidth())
        self.full_menu_widget.setSizePolicy(sizePolicy1)
        self.full_menu_widget.setMaximumSize(QSize(200, 16777215))
        self.verticalLayout_4 = QVBoxLayout(self.full_menu_widget)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, -1)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.sidbar_label2_1 = QLabel(self.full_menu_widget)
        self.sidbar_label2_1.setObjectName(u"sidbar_label2_1")
        self.sidbar_label2_1.setMinimumSize(QSize(40, 40))
        self.sidbar_label2_1.setMaximumSize(QSize(40, 40))
        self.sidbar_label2_1.setPixmap(QPixmap(u"icon/omnivac.ico"))
        self.sidbar_label2_1.setScaledContents(True)

        self.horizontalLayout_2.addWidget(self.sidbar_label2_1)

        self.sidebar_label_2_2 = QLabel(self.full_menu_widget)
        self.sidebar_label_2_2.setObjectName(u"sidebar_label_2_2")
        font = QFont()
        font.setPointSize(15)
        self.sidebar_label_2_2.setFont(font)
        self.sidebar_label_2_2.setScaledContents(True)

        self.horizontalLayout_2.addWidget(self.sidebar_label_2_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_2)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.comport_btn2 = QPushButton(self.full_menu_widget)
        self.comport_btn2.setObjectName(u"comport_btn2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.comport_btn2.sizePolicy().hasHeightForWidth())
        self.comport_btn2.setSizePolicy(sizePolicy2)
        self.comport_btn2.setMaximumSize(QSize(16777215, 80))
        self.comport_btn2.setIcon(icon)
        self.comport_btn2.setIconSize(QSize(16, 16))
        self.comport_btn2.setCheckable(True)
        self.comport_btn2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.comport_btn2)

        self.motor_btn2 = QPushButton(self.full_menu_widget)
        self.motor_btn2.setObjectName(u"motor_btn2")
        sizePolicy2.setHeightForWidth(self.motor_btn2.sizePolicy().hasHeightForWidth())
        self.motor_btn2.setSizePolicy(sizePolicy2)
        self.motor_btn2.setMaximumSize(QSize(16777215, 80))
        self.motor_btn2.setIcon(icon1)
        self.motor_btn2.setIconSize(QSize(16, 16))
        self.motor_btn2.setCheckable(True)
        self.motor_btn2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.motor_btn2)

        self.reset_btn2 = QPushButton(self.full_menu_widget)
        self.reset_btn2.setObjectName(u"reset_btn2")
        sizePolicy2.setHeightForWidth(self.reset_btn2.sizePolicy().hasHeightForWidth())
        self.reset_btn2.setSizePolicy(sizePolicy2)
        self.reset_btn2.setMinimumSize(QSize(0, 50))
        self.reset_btn2.setMaximumSize(QSize(16777215, 80))
        self.reset_btn2.setIcon(icon2)
        self.reset_btn2.setCheckable(True)
        self.reset_btn2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.reset_btn2)

        self.help_btn2 = QPushButton(self.full_menu_widget)
        self.help_btn2.setObjectName(u"help_btn2")
        sizePolicy2.setHeightForWidth(self.help_btn2.sizePolicy().hasHeightForWidth())
        self.help_btn2.setSizePolicy(sizePolicy2)
        self.help_btn2.setMinimumSize(QSize(100, 50))
        self.help_btn2.setMaximumSize(QSize(16777215, 80))
        self.help_btn2.setIcon(icon3)
        self.help_btn2.setIconSize(QSize(16, 16))
        self.help_btn2.setCheckable(True)
        self.help_btn2.setAutoExclusive(True)

        self.verticalLayout_2.addWidget(self.help_btn2)

        self.enable_all_btn2 = QPushButton(self.full_menu_widget)
        self.enable_all_btn2.setObjectName(u"enable_all_btn2")
        sizePolicy2.setHeightForWidth(self.enable_all_btn2.sizePolicy().hasHeightForWidth())
        self.enable_all_btn2.setSizePolicy(sizePolicy2)
        self.enable_all_btn2.setMinimumSize(QSize(0, 50))
        self.enable_all_btn2.setMaximumSize(QSize(16777215, 80))
        self.enable_all_btn2.setIcon(icon4)
        self.enable_all_btn2.setCheckable(False)
        self.enable_all_btn2.setAutoExclusive(False)

        self.verticalLayout_2.addWidget(self.enable_all_btn2)

        self.disable_all_btn2 = QPushButton(self.full_menu_widget)
        self.disable_all_btn2.setObjectName(u"disable_all_btn2")
        sizePolicy2.setHeightForWidth(self.disable_all_btn2.sizePolicy().hasHeightForWidth())
        self.disable_all_btn2.setSizePolicy(sizePolicy2)
        self.disable_all_btn2.setMinimumSize(QSize(0, 50))
        self.disable_all_btn2.setMaximumSize(QSize(16777215, 80))
        self.disable_all_btn2.setIcon(icon5)
        self.disable_all_btn2.setCheckable(False)
        self.disable_all_btn2.setAutoExclusive(False)

        self.verticalLayout_2.addWidget(self.disable_all_btn2)

        self.stop_btn2 = QPushButton(self.full_menu_widget)
        self.stop_btn2.setObjectName(u"stop_btn2")
        sizePolicy2.setHeightForWidth(self.stop_btn2.sizePolicy().hasHeightForWidth())
        self.stop_btn2.setSizePolicy(sizePolicy2)
        self.stop_btn2.setMinimumSize(QSize(0, 50))
        self.stop_btn2.setMaximumSize(QSize(16777215, 80))
        self.stop_btn2.setIcon(icon6)
        self.stop_btn2.setCheckable(False)
        self.stop_btn2.setAutoExclusive(False)

        self.verticalLayout_2.addWidget(self.stop_btn2)


        self.verticalLayout_4.addLayout(self.verticalLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 432, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.exit_btn2 = QPushButton(self.full_menu_widget)
        self.exit_btn2.setObjectName(u"exit_btn2")
        self.exit_btn2.setIconSize(QSize(14, 14))
        self.exit_btn2.setCheckable(True)
        self.exit_btn2.setAutoExclusive(True)

        self.verticalLayout_4.addWidget(self.exit_btn2)


        self.horizontalLayout_3.addWidget(self.full_menu_widget)

        self.display_widget = QWidget(self.centralwidget)
        self.display_widget.setObjectName(u"display_widget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(4)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.display_widget.sizePolicy().hasHeightForWidth())
        self.display_widget.setSizePolicy(sizePolicy3)
        self.verticalLayout_5 = QVBoxLayout(self.display_widget)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.widget = QWidget(self.display_widget)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout_4 = QHBoxLayout(self.widget)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.menu_btn = QPushButton(self.widget)
        self.menu_btn.setObjectName(u"menu_btn")
        icon7 = QIcon()
        icon7.addFile(u":/icon/icon/menu-4-32.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.menu_btn.setIcon(icon7)
        self.menu_btn.setIconSize(QSize(14, 14))
        self.menu_btn.setCheckable(True)
        self.menu_btn.setAutoExclusive(True)

        self.horizontalLayout_4.addWidget(self.menu_btn)

        self.horizontalSpacer_2 = QSpacerItem(974, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)


        self.verticalLayout_5.addWidget(self.widget)

        self.stackedWidget = QStackedWidget(self.display_widget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setAutoFillBackground(True)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.verticalLayout_9 = QVBoxLayout(self.page)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalSpacer_4 = QSpacerItem(20, 180, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_7.addItem(self.verticalSpacer_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_8 = QSpacerItem(168, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_8)

        self.combo_port = QComboBox(self.page)
        self.combo_port.setObjectName(u"combo_port")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.combo_port.sizePolicy().hasHeightForWidth())
        self.combo_port.setSizePolicy(sizePolicy4)
        self.combo_port.setMaximumSize(QSize(200, 100))
        self.combo_port.setSizeIncrement(QSize(0, 0))

        self.horizontalLayout_5.addWidget(self.combo_port)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer)

        self.combo_baud = QComboBox(self.page)
        self.combo_baud.setObjectName(u"combo_baud")
        sizePolicy4.setHeightForWidth(self.combo_baud.sizePolicy().hasHeightForWidth())
        self.combo_baud.setSizePolicy(sizePolicy4)
        self.combo_baud.setMaximumSize(QSize(200, 100))

        self.horizontalLayout_5.addWidget(self.combo_baud)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.combo_byte = QComboBox(self.page)
        self.combo_byte.setObjectName(u"combo_byte")
        sizePolicy4.setHeightForWidth(self.combo_byte.sizePolicy().hasHeightForWidth())
        self.combo_byte.setSizePolicy(sizePolicy4)
        self.combo_byte.setMaximumSize(QSize(200, 100))

        self.horizontalLayout_5.addWidget(self.combo_byte)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)

        self.combo_parity = QComboBox(self.page)
        self.combo_parity.setObjectName(u"combo_parity")
        sizePolicy4.setHeightForWidth(self.combo_parity.sizePolicy().hasHeightForWidth())
        self.combo_parity.setSizePolicy(sizePolicy4)
        self.combo_parity.setMaximumSize(QSize(200, 100))

        self.horizontalLayout_5.addWidget(self.combo_parity)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_5)

        self.combo_stop = QComboBox(self.page)
        self.combo_stop.setObjectName(u"combo_stop")
        sizePolicy4.setHeightForWidth(self.combo_stop.sizePolicy().hasHeightForWidth())
        self.combo_stop.setSizePolicy(sizePolicy4)
        self.combo_stop.setMaximumSize(QSize(200, 100))

        self.horizontalLayout_5.addWidget(self.combo_stop)

        self.horizontalSpacer_9 = QSpacerItem(168, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_9)


        self.verticalLayout_7.addLayout(self.horizontalLayout_5)

        self.verticalSpacer_3 = QSpacerItem(20, 50, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_7.addItem(self.verticalSpacer_3)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer_6 = QSpacerItem(380, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_6)

        self.btn_connect = QPushButton(self.page)
        self.btn_connect.setObjectName(u"btn_connect")
        self.btn_connect.setMaximumSize(QSize(200, 100))

        self.horizontalLayout_6.addWidget(self.btn_connect)

        self.horizontalSpacer_7 = QSpacerItem(380, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_7)


        self.verticalLayout_7.addLayout(self.horizontalLayout_6)

        self.verticalSpacer_14 = QSpacerItem(20, 320, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_7.addItem(self.verticalSpacer_14)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")

        self.verticalLayout_7.addLayout(self.horizontalLayout_13)


        self.verticalLayout_9.addLayout(self.verticalLayout_7)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.gridLayout_3 = QGridLayout(self.page_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.scrollArea = QScrollArea(self.page_2)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1275, 915))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout_3.addWidget(self.scrollArea, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.page_2)
        self.page_4 = QWidget()
        self.page_4.setObjectName(u"page_4")
        self.stackedWidget.addWidget(self.page_4)
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.gridLayout_2 = QGridLayout(self.page_3)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.scrollArea_2 = QScrollArea(self.page_3)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 1300, 915))
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)

        self.gridLayout_2.addWidget(self.scrollArea_2, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.page_3)

        self.verticalLayout_5.addWidget(self.stackedWidget)


        self.horizontalLayout_3.addWidget(self.display_widget)


        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.menu_btn.toggled.connect(self.icon_only_widget.setVisible)
        self.menu_btn.toggled.connect(self.full_menu_widget.setHidden)
        self.comport_btn.toggled.connect(self.comport_btn2.setChecked)
        self.motor_btn.toggled.connect(self.motor_btn2.setChecked)
        self.help_btn.toggled.connect(self.help_btn2.setChecked)
        self.comport_btn2.toggled.connect(self.comport_btn.setChecked)
        self.motor_btn2.toggled.connect(self.motor_btn.setChecked)
        self.help_btn2.toggled.connect(self.help_btn.setChecked)
        self.exit_btn2.clicked.connect(MainWindow.close)
        self.exit_btn.clicked.connect(MainWindow.close)
        self.exit_btn2.clicked.connect(MainWindow.close)
        self.reset_btn.toggled.connect(self.reset_btn2.setChecked)
        self.reset_btn2.toggled.connect(self.reset_btn.setChecked)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.sidbar_label.setText("")
        self.comport_btn.setText("")
        self.motor_btn.setText("")
        self.reset_btn.setText("")
        self.help_btn.setText("")
        self.enable_all_btn.setText("")
        self.disable_all_btn.setText("")
        self.stop_btn.setText("")
        self.exit_btn.setText("")
        self.sidbar_label2_1.setText("")
        self.sidebar_label_2_2.setText(QCoreApplication.translate("MainWindow", u"Sidebar", None))
        self.comport_btn2.setText(QCoreApplication.translate("MainWindow", u"Comport", None))
        self.motor_btn2.setText(QCoreApplication.translate("MainWindow", u"Motor", None))
        self.reset_btn2.setText(QCoreApplication.translate("MainWindow", u"Reset", None))
        self.help_btn2.setText(QCoreApplication.translate("MainWindow", u"Help", None))
        self.enable_all_btn2.setText(QCoreApplication.translate("MainWindow", u"Enable All", None))
        self.disable_all_btn2.setText(QCoreApplication.translate("MainWindow", u"Disable All", None))
        self.stop_btn2.setText(QCoreApplication.translate("MainWindow", u"STOP", None))
        self.exit_btn2.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.menu_btn.setText("")
        self.btn_connect.setText(QCoreApplication.translate("MainWindow", u"Connect", None))
    # retranslateUi

