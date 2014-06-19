#! /usr/bin/python

import sys
import urllib2
import urllib
import thread
import pygst
pygst.require("0.10")
import gst
import json
import random
import cookielib
import keybinder
from PyQt4 import QtCore,QtGui

app = QtGui.QApplication(sys.argv)
cookie = cookielib.CookieJar()

class ClickableLable(QtGui.QLabel):
    captchaClicked = QtCore.pyqtSignal()
    def mouseReleaseEvent(self,event):
        self.captchaClicked.emit()

class LoginClass(QtGui.QDialog):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        usernameLabel = QtGui.QLabel('username:')
        passwdLabel = QtGui.QLabel('password:')
        idcodeLabel = QtGui.QLabel('idcode:   ')
        self.usernameText= QtGui.QLineEdit()
        self.usernameText.setFixedSize(150,24)
        self.passwdText = QtGui.QLineEdit()
        self.passwdText.setFixedSize(150,24)
        self.passwdText.setEchoMode(QtGui.QLineEdit.Password)
        self.idcodeText = QtGui.QLineEdit()
        self.idcodeText.setFixedSize(60,24)
        self.idcodePic = ClickableLable()
        self.idcodePic.setFixedSize(70,24)
        self.idcodePic.setScaledContents(True)
        self.idcodePic.captchaClicked.connect(self.getCaptcha)
        self.feedBack = QtGui.QLabel()

        button = QtGui.QPushButton('submit')
        button.clicked.connect(self.onSubmitClick)

        layout = QtGui.QVBoxLayout()
        contentLayout = QtGui.QHBoxLayout()
        labelLayout = QtGui.QVBoxLayout()
        editLayout = QtGui.QVBoxLayout()
        captchaLayout = QtGui.QHBoxLayout()
        submitLayout = QtGui.QHBoxLayout()

        spacer = QtGui.QLabel()
        spacer.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

        labelLayout.addWidget(usernameLabel)
        labelLayout.addWidget(passwdLabel)
        labelLayout.addWidget(idcodeLabel)
        captchaLayout.addWidget(self.idcodeText)
        captchaLayout.addWidget(spacer)
        captchaLayout.addWidget(self.idcodePic)
        editLayout.addWidget(self.usernameText)
        editLayout.addWidget(self.passwdText)
        editLayout.addLayout(captchaLayout)
        contentLayout.addLayout(labelLayout)
        contentLayout.addLayout(editLayout)
        submitLayout.addWidget(self.feedBack)
        submitLayout.addWidget(spacer)
        submitLayout.addWidget(button)

        layout.addLayout(contentLayout)
        layout.addLayout(submitLayout)
        self.setLayout(layout)
        self.getCaptcha()

    def closeEvent(self,event):
        self.reject()
    def getCaptchaInThread(self):
        thread.start_new_thread(self.getCaptcha,())

    def getCaptcha(self):
        image,self.captcha_id = HttpRequest().getCaptchaRequest()
        self.idcodePic.setPixmap(image)

    def onSubmitClick(self):
        url = 'http://douban.fm/j/login'
        body = {'task': 'sync_channel_list', 'source': 'radio', 'captcha_solution': self.idcodeText.text(), 'alias': self.usernameText.text(), 'form_password': self.passwdText.text(), 'captcha_id': self.captcha_id }
        content = HttpRequest().loginRequest(url,body)
        if json.loads(content)['r'] == 0:
            self.accept()
        else:
            self.feedBack.setText(json.loads(content)['err_msg'])
            self.getCaptcha()

class MainWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.player = Player()
        self.length = 1
        self.like = 0
        layout = QtGui.QHBoxLayout()
        mainLayout = QtGui.QVBoxLayout()
        self.processBar = QtGui.QProgressBar()
        self.processBar.setValue(0)
        self.processBar.setTextVisible(False)
        self.processBar.setFixedHeight(5)
        self.pic = QtGui.QLabel()
        self.pic.setFixedSize(150,150)
        self.pic.setScaledContents(True)
        self.pic.setPixmap(QtGui.QPixmap('./dbfm.png'))
        buttonLayout = QtGui.QVBoxLayout()
        self.playButton = QtGui.QPushButton("(&P)pause")
        nextButton = QtGui.QPushButton("(&N)next")
        self.likeButton =QtGui.QPushButton('(&L)like')
        hateButton = QtGui.QPushButton('(&H)hate')
        self.playButton.clicked.connect(self.onPlayButtonClick)
        nextButton.clicked.connect(self.onNextButtonClick)
        self.likeButton.clicked.connect(self.likes)
        hateButton.clicked.connect(self.hate)
        buttonLayout.addWidget(self.playButton)
        buttonLayout.addWidget(nextButton)
        buttonLayout.addWidget(self.likeButton)
        buttonLayout.addWidget(hateButton)
        icon = QtGui.QIcon('./dbfm.png')
        self.setWindowIcon(icon)
        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.activated.connect(self.showMainWindow)
        trayIconMenu = QtGui.QMenu(self)
        minimizeAction = QtGui.QAction('minisize', self,triggered=self.hide)
        restoreAction = QtGui.QAction('restore', self,triggered=self.showNormal)
        quitAction = QtGui.QAction('exit', self,triggered=QtGui.qApp.quit)
        self.likeAction = QtGui.QAction('like',self,triggered=self.likes)
        self.playAction = QtGui.QAction('pause',self,triggered=self.onPlayButtonClick)
        nextAction = QtGui.QAction('next',self,triggered=self.onNextButtonClick)

        trayIconMenu.addAction(self.playAction)
        trayIconMenu.addAction(nextAction)
        trayIconMenu.addAction(self.likeAction)
        trayIconMenu.addSeparator()
        trayIconMenu.addAction(minimizeAction)
        trayIconMenu.addAction(restoreAction)
        trayIconMenu.addSeparator()
        trayIconMenu.addAction(quitAction)
        self.trayIcon.setContextMenu(trayIconMenu)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setToolTip('douban FM')
        self.trayIcon.show()

        keybinder.bind('<Ctrl>n',self.onNextButtonClick)
        keybinder.bind('<Ctrl>r',self.justLike)
        keybinder.bind('<Ctrl>b',self.hate)
        keybinder.bind('<Ctrl>p',self.onPlayButtonClick)
        keybinder.bind('<Ctrl>t',self.showNormal)

        layout.addWidget(self.pic)
        layout.addLayout(buttonLayout)
        mainLayout.addLayout(layout)
        mainLayout.addWidget(self.processBar)
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.test)
        timer.start(1000)
        self.setLayout(mainLayout)
        self.play()

    def showMainWindow(self,mode):
        if mode == 2:
            if self.isVisible() == True:
                self.setVisible(False)
            else:
                self.setVisible(True)
                self.move((QtGui.QApplication.desktop().width()-main.width())/2,(QtGui.QApplication.desktop().height()-main.height())/2)

    def closeEvent(self,event):
        self.setVisible(False)
        event.ignore()

    def getRandom(self):
        r = str(hex(int(random.random()*1E17)))
        return r[2:12]

    def play(self):
        firstPlayUrl = "http://douban.fm/j/mine/playlist?type=n&sid=&pt=0.0&channel=0&pb=64&from=mainsite&r=%s" % self.getRandom()
        self.getMusic(firstPlayUrl)

    def onPlayButtonClick(self):
        if self.playButton.text() == '(&P)play':
            self.playButton.setText('(&P)pause')
            self.playAction.setText('pause')
            self.player.onPlay()
        else:
            self.playButton.setText('(&P)play')
            self.playAction.setText('play')
            self.player.onPause()

    def likes(self):
        if self.likeButton.text() == '(&L)like':
            self.likeButton.setText('(&L)dislike')
            self.likeAction.setText('dislike')
            likeUrl = "http://douban.fm/j/mine/playlist?type=r&sid=%s&pt=%s&channel=0&pb=64&from=mainsite&r=%s" % (str(self.sid),  str(self.player.getPosition()), self.getRandom())
        else:
            self.likeButton.setText('(&L)like')
            self.likeAction.setText('like')
            likeUrl = "http://douban.fm/j/mine/playlist?type=u&sid=%s&pt=%s&channel=0&pb=64&from=mainsite&r=%s" % (str(self.sid),  str(self.player.getPosition()), self.getRandom())
        HttpRequest().getRequest(likeUrl)

    def justLike(self):
        self.likeButton.setText('(&L)dislike')
        self.likeAction.setText('dislike')
        likeUrl = "http://douban.fm/j/mine/playlist?type=r&sid=%s&pt=%s&channel=0&pb=64&from=mainsite&r=%s" % (str(self.sid),  str(self.player.getPosition()), self.getRandom())
        HttpRequest().getRequest(likeUrl)

    def hate(self):
        hateUrl = "http://douban.fm/j/mine/playlist?type=b&sid=%s&pt=%s&channel=0&pb=64&from=mainsite&r=%s" % (str(self.sid),  str(self.player.getPosition()), self.getRandom())
        self.getMusic(hateUrl)

    def onNextButtonClick(self):
        nextUrl = "http://douban.fm/j/mine/playlist?type=s&sid=%s&pt=%s&channel=0&pb=64&from=mainsite&r=%s" % (str(self.sid),  str(self.player.getPosition()), self.getRandom())
        self.getMusic(nextUrl)

    def getMusic(self,url):
        self.player.onStop()
        title,artist,url,picture,self.sid,self.length,self.like = HttpRequest().analisysMusic(url)
        if self.like == 0:
            self.likeButton.setText('(&L)like')
            self.likeAction.setText('like')
        else:
            self.likeButton.setText('(&L)dislike')
            self.likeAction.setText('dislike')
        self.setPic(picture)
        self.setTitle(artist,title)
        self.player.loadMusic(url)
        self.player.onPlay()


    def setTitle(self,artist,title):
        self.setWindowTitle(artist + '-' + title)
        self.trayIcon.setToolTip('douban FM\n' + artist + '-' + title)
        self.trayIcon.showMessage('douban FM',artist + '-' + title)

    def setPic(self,url):
        self.pic.setPixmap(HttpRequest().getImageRequest(url))

    def setPicInThread(self,url):
        thread.start_new_thread(self.setPic,(url,))

    def test(self):
        self.player.queryPosition()
        self.processBar.setValue(self.player.getPosition()/self.length*100)
        if self.player.getPosition() >= self.length:
            self.player.onStop()
            nextUrl = "http://douban.fm/j/mine/playlist?type=p&sid=%s&pt=%s&channel=0&pb=64&from=mainsite&r=%s" % (str(self.sid), str(self.length) , self.getRandom())
            self.getMusic(nextUrl)


class Player(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.player = gst.element_factory_make('playbin','player')
        self.player.set_state(gst.STATE_READY)
        self.position = 0.0

    def onPlay(self):
        self.player.set_state(gst.STATE_PLAYING)

    def onPause(self):
        self.player.set_state(gst.STATE_PAUSED)

    def onStop(self):
        self.player.set_state(gst.STATE_READY)

    def loadMusic(self,url):
        self.player.set_property('uri',url)

    def queryPosition(self):
        excuteState,currentState,lastState = self.player.get_state()
        if currentState == gst.STATE_PLAYING:
            currentPosition,timeFormat = self.player.query_position()
            currentPosition =  currentPosition/1000000000
            self.position = float('%.1f' % currentPosition)

    def getPosition(self):
        return self.position

class HttpRequest():
    def loginRequest(self,url,body):
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
        opener.addheaders = [('Content-type','application/x-www-form-urlencoded')]
        urllib2.install_opener(opener)
        req = urllib2.Request(url,urllib.urlencode(body))
        res = urllib2.urlopen(req)
        return res.read()

    def getRequest(self,url):
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
        urllib2.install_opener(opener)
        res = urllib2.urlopen(url)
        return res.read()

    def getCaptchaRequest(self):
        url = 'http://douban.fm/j/new_captcha'
        content = self.getRequest(url)
        captcha_id =  str(content).replace('"','')
        url = 'http://douban.fm/misc/captcha?size=m&id=%s' % captcha_id
        return self.getImageRequest(url),captcha_id

    def getImageRequest(self,url):
        content = self.getRequest(url)
        file = open('./temp.jpg','w')
        file.write(content)
        file.close()
        image = QtGui.QPixmap('./temp.jpg')
        return image

    def analisysMusic(self,url):
        content = self.getRequest(url)
        jsonmap = json.loads(content)
        select = random.randint(0,4)
        title = jsonmap['song'][select]['title']
        artist= jsonmap['song'][select]['artist']
        url = jsonmap['song'][select]['url']
        picture= jsonmap['song'][select]['picture']
        sid = jsonmap['song'][select]['sid']
        length = jsonmap['song'][select]['length']
        like = jsonmap['song'][select]['like']
        return title,artist,url,picture,sid,length,like



logintest = LoginClass()
if logintest.exec_() == 1:
    main = MainWindow()
    main.show()
    main.move((QtGui.QApplication.desktop().width()-main.width())/2,(QtGui.QApplication.desktop().height()-main.height())/2)
else:
    QtGui.qApp.quit()
sys.exit(app.exec_())
