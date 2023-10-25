from pathlib import Path
import sys
import vlc
from itertools import cycle
from math import sqrt,ceil
# For PyQt5 :
from PyQt5 import QtWidgets, QtGui, QtCore
import qdarktheme
import pywinstyles
from player import Player
from stream import Stream
from playlist import PlaylistWindow

class ViewWidget(QtWidgets.QWidget):
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

class MainWindow(QtWidgets.QMainWindow):

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("CCTV Player")
		self.headersize = cycle([0,30])
		self.frames = {}
		self.centerWidget = None
		self.vlc_instance = vlc.Instance()
		self.setGeometry(50, 50, 300, 380)
		self.refreshShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F5"), self)
		# self.refreshShortcut.activated.connect(self.refresh)
		self.fullscreenShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F11"), self)
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
			file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
				self, 'Playlist Data', r"", "")
			if Path(file_name).is_file():
				self.plw = PlaylistWindow(file_name,self)
				self.plw.lSignal.connect(self.loadStream)
				self.plw.show()
		elif Path(file_name).exists() and autoload:
			with Path(file_name).open('r') as rl:
				tmp = None
				for line in rl.readlines():
					if line.startswith('#'):
						tmp = Stream(line.strip())
					elif tmp is not None:
						tmp.stream = line.strip()
						self.loadStream(tmp)
						tmp = None

	def changeLayout(self):
		self.centerWidget = next(self.layouts)(self)
		self.centerWidget.layoutSignal.connect(self.changeLayout)
		if len(self.frames) > 0:
			self.centerWidget.display(self.frames)
		else:
			self.loadFile()
		self.setCentralWidget(self.centerWidget)

	def loadStream(self,streamurl):
		frame = Player(self)
		mediaplayer = self.vlc_instance.media_player_new()
		mediaplayer.video_set_mouse_input(False)
		mediaplayer.video_set_key_input(False)
		mediaplayer.set_hwnd(int(frame.player.winId()))
		media = self.vlc_instance.media_new(streamurl.stream)
		frame.mrl = media.get_mrl()
		mediaplayer.set_media(media)
		mediaplayer.play()
		frame.mediaplayer = mediaplayer
		frame.media = media
		frame.streamurl = streamurl
		frame.title.volumeslider.setValue(mediaplayer.audio_get_volume())
		frame.playerDelete.connect(self.deleteStream)
		
		self.frames[streamurl.stream] = frame
		if self.centerWidget:
			self.centerWidget.display(self.frames)

	def refresh(self):
		videos = []
		for x in self.frames.values():
			videos.append(x.streamurl)
			x.setParent(None)
			self.centerWidget.layout.removeWidget(x)
			del x
		self.frames = {}
		for x in videos:self.loadStream(x)


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

def chunks(lst, n):
	for i in range(0, len(lst), n):
		yield lst[i:i + n]

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	app.setStyleSheet(qdarktheme.load_stylesheet())
	w = MainWindow()
	pywinstyles.apply_style(w,"dark")
	sys.exit(app.exec_())
