from pathlib import Path

# For PyQt5 :
from PyQt5 import QtWidgets, QtCore

from util import Stream

class PlaylistWindow(QtWidgets.QDialog):
	lSignal = QtCore.pyqtSignal(Stream)

	def __init__(self, filename,parent=None):
		super().__init__(parent)

		self.filename = filename
		self.organizer = QtWidgets.QVBoxLayout()
		self.label = QtWidgets.QLabel("Playlist Window")
		self.organizer.addWidget(self.label)
		self.setLayout(self.organizer)
		self.streams = []
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
		for x in self.streams:self.lSignal.emit(x)

	def loadStreams(self):
		self.label.deleteLater()
		self.wlist = QtWidgets.QListWidget()
		with Path(self.filename).open('r') as rl:
			tmp = None
			for line in rl.readlines():
				if line.startswith('#'):
					tmp = Stream(line)
				elif tmp is not None:
					tmp.stream = line
					self.streams.append(tmp)
					QtWidgets.QListWidgetItem(tmp.stream, self.wlist,1)

		self.organizer.addWidget(self.wlist)
		self.wlist.doubleClicked.connect(self.sendStream)

	def sendStream(self):
		if self.wlist.currentItem():
			self.lSignal.emit(self.streams[self.wlist.currentIndex().row()])
