# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'authDialog_ui.ui'
#
# Created: Wed Jul 23 22:40:47 2008
#      by: PyQt4 UI code generator 4.4.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(311,141)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon_small.gif"),QtGui.QIcon.Normal,QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setGeometry(QtCore.QRect(0,0,311,141))
        self.centralwidget.setObjectName("centralwidget")
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(10,10,291,121))
        self.widget.setObjectName("widget")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_3 = QtGui.QLabel(self.widget)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_3.addWidget(self.label_3)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(self.widget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label,0,0,1,1)
        self.lineEmail = QtGui.QLineEdit(self.widget)
        #self.lineEmail.setEnabled(False)
        #self.lineEmail.setReadOnly(True)
        self.lineEmail.setObjectName("lineEmail")
        self.gridLayout.addWidget(self.lineEmail,0,1,1,1)
        self.label_2 = QtGui.QLabel(self.widget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2,1,0,1,1)
        self.linePassword = QtGui.QLineEdit(self.widget)
        self.linePassword.setEchoMode(QtGui.QLineEdit.Password)
        self.linePassword.setObjectName("linePassword")
        self.gridLayout.addWidget(self.linePassword,1,1,1,1)
        self.verticalLayout_3.addLayout(self.gridLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.connectButton = QtGui.QPushButton(self.widget)
        self.connectButton.setObjectName("connectButton")
        self.horizontalLayout_2.addWidget(self.connectButton)
        self.exitButton = QtGui.QPushButton(self.widget)
        self.exitButton.setObjectName("exitButton")
        self.horizontalLayout_2.addWidget(self.exitButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.connectButton,QtCore.SIGNAL("clicked()"),self.linePassword.setFocus)
        QtCore.QObject.connect(self.exitButton,QtCore.SIGNAL("clicked()"),MainWindow.hide)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Email SMS Notifier", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "Enter your google account information", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Email:", None, QtGui.QApplication.UnicodeUTF8))
        self.lineEmail.setToolTip(QtGui.QApplication.translate("MainWindow", "Change of email is not available in this version", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Password:", None, QtGui.QApplication.UnicodeUTF8))
        self.connectButton.setText(QtGui.QApplication.translate("MainWindow", "Connect", None, QtGui.QApplication.UnicodeUTF8))
        self.exitButton.setText(QtGui.QApplication.translate("MainWindow", "Hide", None, QtGui.QApplication.UnicodeUTF8))

