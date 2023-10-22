from enum import auto
from pathlib import Path
import sys
import math
import platform
import threading
from time import sleep
import vlc
from itertools import cycle
from math import sqrt,ceil
# For PyQt5 :
from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut, QWidget, QFrame, QListWidgetItem, QFileDialog, QVBoxLayout
from PyQt5 import QtWidgets, QtGui, QtCore
import qdarktheme
from PyQt5.QtGui import QKeySequence
import pywinstyles

def chunks(lst, n):
	for i in range(0, len(lst), n):
		yield lst[i:i + n]


class PlaylistWindow(QtWidgets.QDialog):
	lSignal = QtCore.pyqtSignal(list)

	def __init__(self, filename,parent=None):
		super().__init__(parent)

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
		self.wlist = QtWidgets.QListWidget()
		with Path(self.filename).open('r') as rl:
			for stream in rl.readlines():
				if not stream.startswith('#') and len(stream.strip()):
					QListWidgetItem(stream.strip(), self.wlist)
		self.layout.addWidget(self.wlist)
		self.wlist.doubleClicked.connect(self.sendStream)

	def sendStream(self):
		if self.wlist.currentItem():
			self.lSignal.emit([self.wlist.currentItem().text()])

class PlayerHeader(QtWidgets.QWidget): #1

	def __init__(self, parent):
		super().__init__(parent)
		self.layout = QtWidgets.QHBoxLayout(self)
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.playpause = QtWidgets.QPushButton('Pause',self)
		self.playpause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
		self.layout.addWidget(self.playpause)
		self.stop = QtWidgets.QPushButton('Stop',self)
		self.stop.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
		self.layout.addWidget(self.stop)
		self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
		self.layout.addWidget(self.volumeslider)
		self.volumeslider.setMaximum(100)

	def update_position(self): 
		if hasattr(self.parent(), 'viewport'):
			parent_rect = self.parent().viewport().rect()
		else:
			parent_rect = self.parent().rect()

		if not parent_rect:
			return

		self.playpause.setFixedHeight(self.height())
		self.stop.setFixedHeight(self.height())
		self.setGeometry(0, 0, parent_rect.width(), self.height())

	def resizeEvent(self, event): #2
		super().resizeEvent(event)
		self.update_position()

	def mousePressEvent(self, event): #4
		print('pessed')
		# self.parent().floatingButtonClicked.emit()

class ViewWidget(QWidget):
	layoutSignal = QtCore.pyqtSignal()
	def changeLayout(self):
		self.layoutSignal.emit()

class ListWidget(ViewWidget):
	def __init__(self,parent):
		super().__init__(parent)
		self.layout = QtWidgets.QGridLayout()
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
  
	def display(self,labels):
		self.labels = list(labels.values())
		for x in self.labels: self.layout.addWidget(x)

class GridWidget(ViewWidget):
	def __init__(self,parent):
		super().__init__(parent)
		self.layout = QtWidgets.QGridLayout()
		self.layout.setSpacing(0)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)
	def display(self,labels):
		self.labels = list(labels.values())
		sz = ceil(sqrt(len(self.labels)))
		gn = list(chunks(self.labels,sz))
		for row in range(len(gn)):
			for column in range(len(gn[row])):
				self.layout.addWidget(gn[row][column],row+1,column)

class WinFrame(QFrame):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.paddingLeft = 5
		self.paddingTop = 51

	def update_position(self,headersize=0): 
		if hasattr(self.parent(), 'viewport'):
			parent_rect = self.parent().viewport().rect()
		else:
			parent_rect = self.parent().rect()

		if not parent_rect:
			return
		self.setGeometry(0, headersize, parent_rect.width(), parent_rect.height()-headersize)

	def resizeEvent(self, event): #2
		super().resizeEvent(event)
		# self.update_position()

class Player(QWidget):
	playerDelete = QtCore.pyqtSignal(str)
	
	def __init__(self, parent=None):
		super().__init__(parent)
		self.paddinTop = 0
		self.mrl = None
		self.mediaplayer = None
		self.media = None
		self.streamurl = None
		self.player = WinFrame(self)
		self.title = PlayerHeader(self)
		self.title.volumeslider.valueChanged.connect(self.setVolume)
		self.title.playpause.clicked.connect(self.playPause)
		self.title.stop.clicked.connect(self.stop)
		self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.right_menu)

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
		hide_option = menu.addAction('hide name')
		goodbye_option = menu.addAction('GoodBye')
		aspect_option = menu.addMenu(aspectmenu)
		exit_option = menu.addAction('Close')

		# Menu option events
		hide_option.triggered.connect(self.removeHeader)
		# goodbye_option.triggered.connect(lambda: print('Goodbye'))
		exit_option.triggered.connect(self.deleteStream)

		# Position
		menu.exec_(self.mapToGlobal(pos))

	def setAspect(self,aspect):
		self.mediaplayer.video_set_aspect_ratio(aspect)

	def removeHeader(self):
		self.title.setFixedHeight(0)
		self.player.update_position()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.title.update_position() #4
		if self.player:
			self.player.update_position(self.title.height()) #4
  
	def setVolume(self, Volume):
		if self.mediaplayer:
			self.mediaplayer.audio_set_volume(Volume)

	def stop(self):
		self.mediaplayer.stop()

	def playPause(self):
		"""Toggle play/pause status
		"""
		if self.mediaplayer.is_playing():
			self.mediaplayer.pause()
			self.title.playpause.setText("Play")
			self.title.playpause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
		else:
			if self.mediaplayer.play() == -1:
				return
			self.mediaplayer.play()
			self.title.playpause.setText("Pause")
			self.title.playpause.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

	def deleteStream(self):
		self.playerDelete.emit(self.mrl)
		self.setParent(None)
		self.__del__()

	def __del__(self):
		self.mediaplayer.release()

class MainWindow(QMainWindow):

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("CCTV Player")
		self.headersize = cycle([0,30])
		self.frames = {}
		self.centerWidget = None
		self.vlc_instance = vlc.Instance()
		self.setGeometry(50, 50, 300, 380)
		self.refreshShortcut = QShortcut(QKeySequence("F5"), self)
		# self.refreshShortcut.activated.connect(self.refresh)
		self.fullscreenShortcut = QShortcut(QKeySequence("F11"), self)
		self.fullscreenShortcut.activated.connect(self.toggleFullScreen)
		self.loadHeader()
		self.layouts = cycle([GridWidget,ListWidget])
		self.changeLayout()
		self.show()

		if len(sys.argv) == 2:
			self.loadFile(sys.argv[-1], True)
	def loadHeader(self):
		menu_bar = self.menuBar()
		# View menu
		view_menu = menu_bar.addMenu("View")

		# Add actions to view menu
		load_action = QtWidgets.QAction("Load", self)
		refresh_action = QtWidgets.QAction("Refresh", self)
		toggle_action = QtWidgets.QAction("Toggle Layout", self)
		close_action = QtWidgets.QAction("Close App", self)

		view_menu.addAction(load_action)
		view_menu.addAction(refresh_action)
		view_menu.addAction(toggle_action)
		view_menu.addAction(close_action)

		load_action.triggered.connect(self.loadFile)
		refresh_action.triggered.connect(self.refresh)
		toggle_action.triggered.connect(self.changeLayout)
		close_action.triggered.connect(sys.exit)
		
	# loads playlist file into a playlist window
	def loadFile(self, file_name=None, autoload=False):
		if file_name is None or not Path(file_name).exists():
			file_name, _ = QFileDialog.getOpenFileName(
				self, 'Playlist Data', r"", "")
			if Path(file_name).is_file():
				self.plw = PlaylistWindow(file_name,self)
				self.plw.lSignal.connect(self.loadStreams)
				self.plw.show()
		elif Path(file_name).exists() and autoload:
			line = Path(file_name).read_text()
			self.loadStreams(line.strip().split('\n'))

	def changeLayout(self):
		self.centerWidget = next(self.layouts)(self)
		self.centerWidget.layoutSignal.connect(self.changeLayout)
		if len(self.frames) > 0:
			self.centerWidget.display(self.frames)
		else:
			self.loadFile()
		self.setCentralWidget(self.centerWidget)

	def loadStreams(self,videos:list):
		for x in videos:
			if not x.startswith('#'):
				self.loadStream(x)

	def loadStream(self,streamurl):
		frame = Player(self)
		mediaplayer = self.vlc_instance.media_player_new()
		mediaplayer.set_hwnd(int(frame.player.winId()))
		media = self.vlc_instance.media_new(streamurl)
		frame.mrl = media.get_mrl()
		mediaplayer.set_media(media)
		mediaplayer.play()
		frame.mediaplayer = mediaplayer
		frame.media = media
		frame.streamurl = streamurl
		frame.title.volumeslider.setValue(mediaplayer.audio_get_volume())
		frame.playerDelete.connect(self.deleteStream)
		
		self.frames[streamurl] = frame
		if self.centerWidget:
			self.centerWidget.display(self.frames)

	def refresh(self):
		videos = []
		for x in self.frames.values():
			videos.append(x.mrl)
			x.setParent(None)
			self.centerWidget.layout.removeWidget(x)
			del x
		self.frames = {}
		self.loadStreams(videos)

	def deleteStream(self,mrl):
		instance = self.frames.pop(mrl)
		# instance.setParent(None)
		self.centerWidget.layout.removeWidget(instance)
		# del instance
  
	def toggleHeaders(self):
		sz = next(self.headersize)
		for x in self.frames.values():
			print(x.title.height())
			x.title.setFixedHeight(sz)
			x.player.update_position()

	def toggleFullScreen(self):
		if self.isFullScreen():
			self.toggleHeaders()
			self.showNormal()
		else:
			self.toggleHeaders()
			self.showFullScreen()
if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyleSheet(qdarktheme.load_stylesheet())
	w = MainWindow()
	pywinstyles.apply_style(w,"dark")
	sys.exit(app.exec_())
