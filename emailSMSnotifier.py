import sys, time, re, threading, pickle

from PyQt4 import QtCore, QtGui
from authDialog_ui import Ui_MainWindow
from gcal import Calendar
import libgmail
import gdata, sip, ClientCookie

authFile = "auth.bin" # Storing auth data
sentFile = "sent.bin" # Storing sent messages data

class checkSendMessages(threading.Thread):
    def run(self):
        self.sent = {}
        try: 
            file_pi = open(sentFile, 'r')
            sentData = pickle.load(file_pi)
            file_pi.close()
            if sentData:
                self.sent = sentData
        except:
            pass
        self.email = ''
        self.password = ''
        
        self.sendMessages()   
    def sendMessages(self):
        global authFile
        
        if not self.email and not self.password:
            file_pi = open(authFile, 'r')
            authData = pickle.load(file_pi)
            file_pi.close()
            self.email = authData['email']
            self.password = authData['password']
        try:
            gmail = Gmail()
            gmail.login(self.email, self.password)
        except Exception:
            print "Login failure!"
            
        unread = gmail.getInbox()
        
        
        for message_id, subject in unread.iteritems():
            if not self.sent.has_key(message_id):
                account = self.email.split('@')[0]
                self.sent[message_id] = subject
                
                file_pi = open(sentFile, 'w')
                pickle.dump(self.sent, file_pi)
                file_pi.close()
                
                calendar = Calendar(account, self.password)
                event = calendar._InsertEvent(title = subject)
                try:
                    calendar._AddReminder(event)
                except :
                    time.sleep(2)
                    calendar._AddReminder(event)
                time.sleep(70)
                calendar._DeleteEvent(event)
        time.sleep(10)
        self.sendMessages()
        
class Gmail():
    def __init__(self):
        self.unread = {}
    def login(self, email, password):
        self.email = email
        self.password = password
        self.ga = libgmail.GmailAccount(self.email, self.password)
        self.ga.login()
    def getInbox(self):
        folder = self.ga.getMessagesByFolder('inbox')
        for thread in folder:
#            print thread.authors
            m = re.compile("^\\\u003cb\\\u003e(.*)\\\u003c/b\\\u003e$").search(thread.subject)
            if m and not self.unread.has_key(thread.id):
                    self.unread[thread.id] =  m.group(1)
        return self.unread

class SysTray(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.quitAction = QtGui.QAction(self.tr("&Quit"), self)
        QtCore.QObject.connect(self.quitAction, QtCore.SIGNAL("triggered()"), QtGui.qApp, QtCore.SLOT("quit()"))
        
        self.loginAction = QtGui.QAction(self.tr("&Login"), self)
        QtCore.QObject.connect(self.loginAction, QtCore.SIGNAL("triggered()"), self.displayDialog)
                
        self.trayIconMenu = QtGui.QMenu(self)
        self.trayIconMenu.addAction(self.loginAction)
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QtGui.QIcon('icon_small.gif'))
        self.trayIcon.show()
    def displayDialog(self):
        self.dialog = AuthDialog()
        self.dialog.show()

class AuthDialog(QtGui.QMainWindow):
        def __init__(self, parent=None):
            QtGui.QWidget.__init__(self, parent)
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            try: 
                file_pi = open(authFile, 'r')
                authData = pickle.load(file_pi)
                file_pi.close()
                if authData:
                    self.ui.lineEmail.setText(authData['email'])
                    self.ui.linePassword.setText(authData['password'])
            except:
                pass                
            QtCore.QObject.connect(self.ui.connectButton,QtCore.SIGNAL("clicked()"),self._connect)
        def _connect(self):
            
            email = self.ui.lineEmail.text()
            password = self.ui.linePassword.text()
            
            if email == '':
                self.ui.lineEmail.setFocus()
            elif password == '':
                self.ui.linePassword.setFocus()
            else:
                authData = {'email': str(email), 'password': str(password)}
                #try: # Checking if we can auth.
                file_pi = open(authFile, 'w')
                pickle.dump(authData, file_pi)
                file_pi.close()
                checkSendMessages().start()
                self.hide()
                #except Exception:
                 #   E
                  #  self.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Login failed! Try again!", None, QtGui.QApplication.UnicodeUTF8))
                  #  time.sleep(1)
                  #  self.setWindowTitle(QtGui.QApplication.translate("MainWindow", "", None, QtGui.QApplication.UnicodeUTF8))
                   # self.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Email SMS Notifier", None, QtGui.QApplication.UnicodeUTF8))
if __name__ == "__main__":
        app = QtGui.QApplication(sys.argv)
        myApp = AuthDialog() # Display login dialog
        myApp.show()
        myTray = SysTray() #Display system tray
        sys.exit(app.exec_())