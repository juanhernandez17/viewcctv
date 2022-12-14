from enum import auto
from pathlib import Path
import sys
import math
import platform
import threading
from time import sleep
import vlc
from itertools import cycle

# For PyQt5 :
from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut, QWidget, QListWidget, QListWidgetItem, QFileDialog
from PyQt5 import QtWidgets, QtGui, QtCore
import qdarktheme
from PyQt5.QtGui import QKeySequence


class PlaylistWindow(QWidget):
	lSignal = QtCore.pyqtSignal(list)

	def __init__(self, filename):
		super(PlaylistWindow, self).__init__()

		self.filename = filename
		self.layout = QtWidgets.QVBoxLayout()
		self.label = QtWidgets.QLabel("Playlist Window")
		self.layout.addWidget(self.label)
		self.setLayout(self.layout)
		self.loadStreams()

		# Right Click Menu
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.right_menu)

	def right_menu(self, pos):
		menu = QtWidgets.QMenu()

		# Add menu options
		addAll_option = menu.addAction('Add All')
		# goodbye_option = menu.addAction('GoodBye')
		# exit_option = menu.addAction('Exit')

		# Menu option events
		addAll_option.triggered.connect(self.addAll)
		# goodbye_option.triggered.connect(lambda: print('Goodbye'))
		# exit_option.triggered.connect(lambda: exit())

		# Position
		menu.exec_(self.mapToGlobal(pos))

	def addAll(self):
		its = [self.wlist.item(i).text() for i in range(self.wlist.count())]
		if len(its):
			self.lSignal.emit(its)

	def loadStreams(self):
		self.label.deleteLater()
		self.wlist = QListWidget()
		with Path(self.filename).open('r') as rl:
			for stream in rl.readlines():
				if not stream.startswith('#') and len(stream.strip()):
					QListWidgetItem(stream.strip(), self.wlist)
		self.layout.addWidget(self.wlist)
		self.wlist.doubleClicked.connect(self.sendStream)

	def sendStream(self):
		if self.wlist.currentItem():
			self.lSignal.emit([self.wlist.currentItem().text()])

# Each Stream gets a widget with the stream url as the header
class WinFrams(QtWidgets.QWidget):
	def __init__(self, parent=None, title="", mediaplayer=None):
		super(WinFrams, self).__init__(parent)

		self.layout = QtWidgets.QVBoxLayout()
		self.mediaplayer = mediaplayer
		self.name = QtWidgets.QLabel(parent=self)
		self.name.setFixedHeight(15)
		self.name.setText(title)
		# self.name.setContentsMargins(0, 0, 0, 0)

		self.name.setAlignment(QtCore.Qt.AlignCenter)

		self.video = QtWidgets.QWidget()

		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
		self.layout.addWidget(self.name)

		self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
		self.volumeslider.setMaximum(100)
		self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
		self.volumeslider.setToolTip("Volume")
		self.layout.addWidget(self.volumeslider)
		self.volumeslider.valueChanged.connect(self.setVolume)

		self.layout.addWidget(self.video)

		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.right_menu)

	def right_menu(self, pos):
		menu = QtWidgets.QMenu()

		# Add menu options
		hide_option = menu.addAction('hide name')
		goodbye_option = menu.addAction('GoodBye')
		exit_option = menu.addAction('Close')

		# Menu option events
		hide_option.triggered.connect(lambda: self.name.setHidden(True))
		goodbye_option.triggered.connect(lambda: print('Goodbye'))
		exit_option.triggered.connect(self.deleteStream)

		# Position
		menu.exec_(self.mapToGlobal(pos))

	def deleteStream(self):
		self.setParent(None)
		self.mediaplayer.release()

	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.HoverEnter:
			self.onHovered()
		return super(WinFrams, self).eventFilter(obj, event)

	def onHovered(self):
		print("hovered")

	def winId(self):
		return self.video.winId()

	def setVolume(self, Volume):
		self.mediaplayer.audio_set_volume(Volume)

	# TODO: maybe add ability to move streams around
	def mouseMoveEvent(self, e):
		if e.buttons() == QtCore.Qt.LeftButton:
			drag = QtGui.QDrag(self)
			mime = QtCore.QMimeData()
			drag.setMimeData(mime)
			drag.exec_(QtCore.Qt.MoveAction)

# Grid for the streams to be putin
class GridPlayer(QWidget):
	def __init__(self, parent=None, medias=None):
		super(GridPlayer, self).__init__(parent)
		self.layout = QtWidgets.QGridLayout()

		# remove spacing between objects
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)

		self.setLayout(self.layout)
		self.maxx = 1
		self.maxy = 1
		self.x = 0
		self.y = 0
		for media in medias:
			self.createWidget(media)

	def createWidget(self, media):
		videoframe = WinFrams(mediaplayer=media)
		videoframe.setAutoFillBackground(True)
		media.stop()
		media.set_hwnd(int(videoframe.winId()))
		self.addWid(videoframe)
		media.play()

	# better way of growing the grid size
	def calcSize(self):
		num = self.layout.count() + 1
		root = math.sqrt(num)
		self.maxx = math.ceil(root)
		self.maxy = math.ceil(num / self.maxx)

	# "dumb" way to add new streams to grid, checks every square from top to bottom left to right inserts it at the first open spot
	def addWid(self, widget):
		x = 0
		y = 0
		added = False
		for y in range(self.maxy):
			for x in range(self.maxx):
				if self.layout.itemAtPosition(y, x) == None:
					self.layout.addWidget(widget, y, x)
					added = True
					break
			if added:
				break
		self.calcSize()
		if not added:
			self.addWid(widget)

	def getPlayers(self):
		players = []
		for x in range(self.maxx):
			for y in range(self.maxy):
				w = self.layout.itemAtPosition(y, x)
				if w:
					players.append(w.widget())
				else:
					continue
		return players

# Grid for the streams to be putin
class VerticalPlayer(QWidget):
	def __init__(self, parent=None, medias=None):
		super(VerticalPlayer, self).__init__(parent)
		self.layout = QtWidgets.QGridLayout()

		# remove spacing between objects
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)

		self.setLayout(self.layout)
		for media in medias:
			self.createWidget(media)

	def createWidget(self, media):
		videoframe = WinFrams(mediaplayer=media)
		videoframe.setAutoFillBackground(True)
		media.stop()
		media.set_hwnd(int(videoframe.winId()))
		self.addWid(videoframe)
		media.play()
  
  
	def addWid(self, widget):
		self.layout.addWidget(widget)

	def getPlayers(self):
		players = []
		for x in range(self.layout.count()):
			w = self.layout.itemAt(x)
			if w:
				players.append(w.widget())
			else:
				continue
		return players


class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.running = True  # used to stop child threads
		# TODO: maybe remove the stock window frame and make own
		# self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

		# child thread to check if streams stoped and restart them
		self.thread = None

		self.setGeometry(50, 50, 1000, 1080)

		# store vlc instances and player widget instances
		self.medias = []
		self.players = []
		self.layouts = cycle([GridPlayer, VerticalPlayer])
		self.currentlayout = None
		self.centerW = None
  
		self.instance = vlc.Instance()
		self.ref = QtWidgets.QLabel('Wait...', self)

		# keyboard shortcuts used to work but need to update their code since the way the players are loaded has changed
		self.shortcut = QShortcut(QKeySequence("F5"), self)
		# self.shortcut.activated.connect(self.refresh)

		self.setFullscreen = QShortcut(QKeySequence("F11"), self)
		# self.setFullscreen.activated.connect(self.toggleFullScreen)

		menu_bar = self.menuBar()
		# Right Click Menu
		# self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		# self.customContextMenuRequested.connect(self.right_menu)

		# View menu
		view_menu = menu_bar.addMenu("View")

		# Add actions to view menu
		load_action = QtWidgets.QAction("Load", self)
		# refresh_action = QtWidgets.QAction("Refresh", self)
		toggle_action = QtWidgets.QAction("Toggle Layout", self)
		close_action = QtWidgets.QAction("Close App", self)

		view_menu.addAction(load_action)
		# view_menu.addAction(refresh_action)
		view_menu.addAction(toggle_action)
		view_menu.addAction(close_action)

		load_action.triggered.connect(self.loadFile)
		# refresh_action.triggered.connect(self.refresh)
		toggle_action.triggered.connect(self.toggle)
		close_action.triggered.connect(sys.exit)

		self.setWindowTitle("CCTV Player DEF")
		self.show()
		# self.startLoader()
		# self.ref.deleteLater()
		self.StartPlayerLayout()

		# if self.thread == None:
		# 	self.thread = threading.Thread(target=self.checkPlaying)
		# 	self.thread.start()
		if len(sys.argv) == 2:
			self.loadFile(sys.argv[-1], True)

	# TODO
	def right_menu(self, pos):
		menu = QtWidgets.QMenu()

		# Add menu options
		hello_option = menu.addAction('Hello World')
		goodbye_option = menu.addAction('GoodBye')
		exit_option = menu.addAction('Exit')

		# Menu option events
		hello_option.triggered.connect(lambda: print('Hello World'))
		goodbye_option.triggered.connect(lambda: print('Goodbye'))
		exit_option.triggered.connect(lambda: exit())

		# Position
		menu.exec_(self.mapToGlobal(pos))

	# TODO: fix fullscreening currently layout changes from grid to vertical stack
	def toggleFullScreen(self):
		self.ref = QtWidgets.QLabel('Wait...', self)
		if self.isFullScreen():
			self.showNormal()
		else:
			self.setWindowTitle("FullScreening")
			self.setCentralWidget(self.ref)
			self.showFullScreen()

	def startLoader(self):
		self.centerW = QWidget()
		self.setCentralWidget(self.centerW)

		self.mainwid = QtWidgets.QGridLayout()
		self.centerW.setLayout(self.mainwid)

		self.ref = QtWidgets.QLabel('Wait...', self)
		self.show()
		self.mainwid.addWidget(self.ref, 1, 1)

	# TODO: crashes the window - havent implemented new video widget loading
	def refresh(self):
		self.setWindowTitle("Refreshing")
		self.assignPlayers()

	def toggle(self):
		# self.getMedias()
		# self.startLoader()
		self.StartPlayerLayout()

	def getMedias(self):
		self.medias = []
		try:
			players = self.centerW.getPlayers()
			for player in players:
				print(player.mediaplayer.get_media())
				self.medias.append(player.mediaplayer)
		except:
			pass

	def StartPlayerLayout(self):
		oldlay = self.centerW
		if oldlay:
			# oldlay.deleteLater()
			oldlay.setParent(None)
		self.currentlayout = next(self.layouts)
		self.centerW = self.currentlayout(self, self.medias)
		self.setWindowTitle(self.currentlayout.__name__)
		self.setCentralWidget(self.centerW)
		# if oldlay:
		# 	oldlay.deleteLater()

	# lags the program out
	def addStreamSafe(self, source):
		self.addthread = threading.Thread(
			target=self.addStream, args=(source,))
		self.addthread.start()

	def addStream(self, sources):
		for source in sources:
			if source == None and source == '':
				continue
			try:
				media = self.instance.media_new(source)
				mediaplayer = self.instance.media_player_new()
				mediaplayer.set_media(media)
				self.centerW.createWidget(mediaplayer)
				mediaplayer.play()
				self.medias.append(mediaplayer)
			except:
				pass

	# loads playlist file into a playlist window
	def loadFile(self, file_name=None, autoload=False):
		if file_name == False or not Path(file_name).exists():
			file_name, _ = QFileDialog.getOpenFileName(
				self, 'Playlist Data', r"", "")
			if Path(file_name).is_file():
				self.plw = PlaylistWindow(file_name)
				self.plw.lSignal.connect(self.addStream)
				self.plw.show()
		elif Path(file_name).exists() and autoload:
			line = Path(file_name).read_text()
			self.addStream(line.strip().split('\n'))

	# old way of loading video instances
	def gatherStreams(self):
		self.medias = []
		if len(self.medias):
			return
		for x in range(1):
			media = self.instance.media_new(x)
			mediaplayer = self.instance.media_player_new()
			mediaplayer.set_media(media)
			self.medias.append(mediaplayer)

	# WIP new way to load player widgets
	def assignPlayers(self):
		for media in self.medias:
			if platform.system() == "Darwin":  # for MacOS
				videoframe = QtWidgets.QMacCocoaViewContainer(0)
			else:
				videoframe = QtWidgets.QFrame()
			videoframe.setAutoFillBackground(True)
			if media.is_playing():
				media.stop()
			media.set_hwnd(int(videoframe.winId()))
			media.play()
			self.centerW.layout.addWidget(videoframe)
			self.players.append(videoframe)

	# Clears the layout from player widgets
	def deletePlayers(self,):
		for i in reversed(range(self.centerW.layout.count())):
			self.centerW.layout.itemAt(i).widget().setParent(None)
		self.players = []

	# delete vlc player instances
	def releaseStreams(self):
		for video in self.medias:
			video.release()
		self.medias = []

	# communicates the program was closed with the thread
	def closeEvent(self, event):
		self.running = False
		event.accept()

	# Thread to check streams are running and restart them if not
	def checkPlaying(self):
		while self.running:
			try:
				# using this method to get the players makes it easier to close streams
				players = self.centerW.getPlayers()
				print(f'[{threading.get_ident()}] CHECKING {len(players)}')
				for w in players:
					media = w.mediaplayer
					if media and not media.is_playing():
						print(f'Restarting {media.get_media().get_mrl()}')
						media.stop()
						sleep(1)
						media.play()
				sleep(3)
			except:
				if self.running:
					sleep(10)
		self.thread = None

	# TODO might use this to allow the moving of player widgets within the Grid
	def dragEnterEvent(self, e):
		e.accept()

	def dropEvent(self, e):
		pos = e.pos()
		widget = e.source()

		for n in range(self.centerW.layout.count()):
			# Get the widget at each index in turn.
			w = self.centerW.layout.itemAt(n).widget()
			if pos.x() < w.x() + w.size().width() // 2:
				# We didn't drag past this widget.
				# insert to the left of it.
				self.centerW.layout.insertWidget(n-1, widget)
				break

		e.accept()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyleSheet(qdarktheme.load_stylesheet())
	w = MainWindow()
	threading.active_count()
	sys.exit(app.exec_())
