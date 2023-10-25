# For PyQt5 :
from PyQt5 import QtGui, QtWidgets, QtCore
import vlc

class PlayerHeader(QtWidgets.QWidget): #1

	def __init__(self, parent):
		super().__init__(parent)
		self.organizer = QtWidgets.QHBoxLayout(self)
		self.setStyleSheet(r'QPushButton{color:green}')
		self.organizer.setSpacing(0)
		self.organizer.setContentsMargins(0, 0, 0, 0)
		self.playpause = QtWidgets.QPushButton('Pause',self)
		self.setMaximumHeight(self.playpause.height())
		self.playpause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
		self.organizer.addWidget(self.playpause)
		self.stop = QtWidgets.QPushButton('Stop',self)
		self.stop.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
		self.organizer.addWidget(self.stop)
		self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
		self.organizer.addWidget(self.volumeslider)
		self.volumeslider.setMaximum(100)

	# def update_position(self): 
	# 	if hasattr(self.parent(), 'viewport'):
	# 		parent_rect = self.parent().viewport().rect()
	# 	else:
	# 		parent_rect = self.parent().rect()

	# 	if not parent_rect:
	# 		return

	# 	self.playpause.setFixedHeight(self.height())
	# 	self.stop.setFixedHeight(self.height())
	# 	self.setGeometry(0, 0, parent_rect.width(), self.height())

	# def resizeEvent(self, event): #2
	# 	super().resizeEvent(event)
	# 	self.update_position()

	# def mousePressEvent(self, event): #4
	# 	print('pessed')
		# self.parent().floatingButtonClicked.emit()


class WinFrame(QtWidgets.QFrame):
	def __init__(self, parent=None):
		super().__init__(parent)
		# self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
		# self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

	# def update_position(self,headersize=0): 
	# 	if hasattr(self.parent(), 'viewport'):
	# 		parent_rect = self.parent().viewport().rect()
	# 	else:
	# 		parent_rect = self.parent().rect()

	# 	if not parent_rect:
	# 		return
	# 	self.setGeometry(0, headersize, parent_rect.width(), parent_rect.height()-headersize)

	# def resizeEvent(self, event): #2
	# 	super().resizeEvent(event)
	# 	self.update_position()

class Player(QtWidgets.QWidget):
	playerDelete = QtCore.pyqtSignal(str)
	
	def __init__(self, media,mediaplayer,parent=None):
		super().__init__(parent)
		# self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
		# self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
		self.media = media
		self.mediaplayer = mediaplayer
		self.mrl = media.get_mrl()
		self.streamurl = None
		self.player = WinFrame(self)
		self.header = PlayerHeader(self)
		# self.header.hide()
		self.header.volumeslider.valueChanged.connect(self.setVolume)
		self.header.playpause.clicked.connect(self.playPause)
		self.header.stop.clicked.connect(self.mediaplayer.stop)
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.right_menu)

		self.organizer = QtWidgets.QVBoxLayout()
		self.organizer.addWidget(self.header)
		self.organizer.addWidget(self.player)
		self.organizer.setSpacing(0)
		self.organizer.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.organizer)
		self.loadMedia()

	def right_menu(self, pos):
		menu = QtWidgets.QMenu()
  
		# create aspect ratio Submenu before adding it to the context menu
		aspectmenu = QtWidgets.QMenu('Aspect')
		aspect169 = aspectmenu.addAction('16:9')
		aspect43 = aspectmenu.addAction('4:3')
		aspectdef = aspectmenu.addAction('Default')
		aspect169.triggered.connect(lambda: self.setAspect('16:9'))
		aspect43.triggered.connect(lambda: self.setAspect('4:3'))
		aspectdef.triggered.connect(lambda: self.setAspect(''))

		# Add menu options
		hide_option = menu.addAction('Toggle Header')
		goodbye_option = menu.addAction('GoodBye')
		aspect_option = menu.addMenu(aspectmenu)
		exit_option = menu.addAction('Close')

		# Menu option events
		hide_option.triggered.connect(self.toggleHeader)
		# goodbye_option.triggered.connect(lambda: print('Goodbye'))
		exit_option.triggered.connect(self.deleteStream)

		# Position
		menu.exec_(self.mapToGlobal(pos))

	def loadMedia(self):

		self.mediaplayer.video_set_mouse_input(False)
		self.mediaplayer.video_set_key_input(False)
		self.mediaplayer.set_hwnd(int(self.player.winId()))
		self.mediaplayer.set_media(self.media)
		self.vlcEventManager = self.mediaplayer.event_manager()
		self.setEventManager()
		self.mediaplayer.play()
		self.header.volumeslider.setValue(self.mediaplayer.audio_get_volume())
  
  
	def setAspect(self,aspect):
		self.mediaplayer.video_set_aspect_ratio(aspect)

	def toggleHeader(self):
		if self.header.isHidden():
			self.header.show()
		else:
			self.header.hide()

	def resizeEvent(self, event):
		super().resizeEvent(event)

	def setEventManager(self):
		self.vlcEventManager.event_attach(vlc.EventType.MediaPlayerPaused,self.playerPaused)
		self.vlcEventManager.event_attach(vlc.EventType.MediaPlayerPlaying,self.playerPlaying)
		self.vlcEventManager.event_attach(vlc.EventType.MediaPlayerStopped,self.playerPaused)
		# sometimes an erro will crash the whole program
		self.vlcEventManager.event_attach(vlc.EventType.MediaPlayerEncounteredError,self.error)

	def setVolume(self, Volume):
		if self.mediaplayer:
			self.mediaplayer.audio_set_volume(Volume)

	def playerPlaying(self,event):
		self.header.playpause.setText("Pause")
		self.header.playpause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))

	def playerPaused(self,event):
		self.header.playpause.setText("Play")
		self.header.playpause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

	def playPause(self):
		if self.mediaplayer.is_playing():
			self.mediaplayer.pause()
		else:
			self.mediaplayer.play()

	def error(self,v):
		self.mediaplayer.stop()
		print(v)

	def deleteStream(self):
		self.mediaplayer.stop()
		self.mediaplayer.release()
		self.header.deleteLater()
		self.player.deleteLater()
		self.playerDelete.emit(self.mrl)
		self.deleteLater()
		pass
