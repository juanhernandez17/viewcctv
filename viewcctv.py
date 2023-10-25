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
from util import Stream, chunks
from playlist import PlaylistWindow

class ViewWidget(QtWidgets.QWidget):
	def __init__(self,parent):
		super().__init__(parent)
		self.widgets = []

	def clear(self):
		for x in self.widgets:
			self.organizer.removeWidget(x)
		# self.organizer.addWidget(tmp)
		# self.show()

class ListWidget(ViewWidget):
	def __init__(self,parent):
		super().__init__(parent)
		self.organizer = QtWidgets.QGridLayout()
		self.organizer.setSpacing(0)
		self.organizer.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.organizer)
  
	def display(self,labels):
		self.clear()
		self.widgets = list(labels.values())
		if len(labels) == 0: return
		for x in self.widgets: self.organizer.addWidget(x)

class GridWidget(ViewWidget):
	def __init__(self,parent):
		super().__init__(parent)
		self.organizer = QtWidgets.QGridLayout()
		self.organizer.setSpacing(0)
		self.organizer.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.organizer)

	def display(self,labels):
		self.clear()
		self.widgets = list(labels.values())
		if len(labels) == 0: return
		sz = ceil(sqrt(len(self.widgets)))
		gn = list(chunks(self.widgets,sz))
		for row in range(len(gn)):
			for column in range(len(gn[row])):
				self.organizer.addWidget(gn[row][column],row,column)


class MainWindow(QtWidgets.QMainWindow):

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("CCTV Player")
		self.setStyleSheet('background-color:black')
		# self.setStyleSheet('background-color:red')
		self.frames = {}
		self.centerWidget = None
		self.vlc_instance = vlc.Instance()
		self.setGeometry(50, 50, 300, 380)
		self.loadShortcuts()
		self.loadHeader()
		self.layouts = cycle([GridWidget,ListWidget])
		self.changeLayout()
		self.show()

		if len(sys.argv) == 2:
			self.loadFile(sys.argv[-1], True)

	def loadShortcuts(self):
		self.refreshShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F5"), self)
		self.refreshShortcut.activated.connect(self.refresh)
		self.fullscreenShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F11"), self)
		self.fullscreenShortcut.activated.connect(self.toggleFullScreen)

	def loadHeader(self):
		self.menu_bar = self.menuBar()
		# View menu
		view_menu = self.menu_bar.addMenu("View")

		# Add actions to view menu
		load_action = QtWidgets.QAction("Load", self)
		refresh_action = QtWidgets.QAction("Refresh", self)
		toggle_action = QtWidgets.QAction("Toggle Layout", self)
		close_action = QtWidgets.QAction("Close App", self)

		view_menu.addAction(load_action)
		view_menu.addAction(refresh_action)
		view_menu.addAction(toggle_action)
		view_menu.addAction(close_action)

		load_action.triggered.connect(lambda :self.loadFile())
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
		if self.centerWidget:
			self.centerWidget.deleteLater()
		self.centerWidget = next(self.layouts)(self)
		if len(self.frames) > 0:
			self.centerWidget.display(self.frames)
		self.setCentralWidget(self.centerWidget)

	def loadStream(self,streamurl):
		mediaplayer = self.vlc_instance.media_player_new()
		media = self.vlc_instance.media_new(streamurl.stream)
		frame = Player(media,mediaplayer,self)
		frame.streamurl = streamurl
		frame.playerDelete.connect(self.deleteStream)
		
		
		self.frames[streamurl.stream] = frame
		if self.centerWidget:
			self.centerWidget.display(self.frames)

	def refresh(self):
		videos = [x.streamurl for x in self.frames.values()]
		self.centerWidget.clear()
		for x in self.frames.copy().values():x.deleteStream()
		self.frames = {}
		for x in videos:self.loadStream(x)

	def deleteStream(self,mrl):
		self.frames.pop(mrl)
		self.centerWidget.display(self.frames)

	def toggleFullScreen(self):
		if self.isFullScreen():
			for x in self.frames.values():x.header.show()
			self.menu_bar.show()
			self.showNormal()
		else:
			for x in self.frames.values():x.header.hide()
			self.menu_bar.hide()
			self.showFullScreen()

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	app.setStyleSheet(qdarktheme.load_stylesheet())
	w = MainWindow()
	pywinstyles.apply_style(w,"dark")
	sys.exit(app.exec_())
