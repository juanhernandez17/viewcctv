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

