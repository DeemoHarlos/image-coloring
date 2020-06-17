import os, sys

# external packages
import cv2
from PyQt5 import Qt, QtCore, QtGui, QtWidgets as Qw, uic
from qimage2ndarray import array2qimage as np2qimg

# import core function
from colorization import *

class UI(Qw.QMainWindow):
	def __init__(self):
		# initial GUI
		super(UI, self).__init__()
		uic.loadUi('gui.ui', self)

		# get the widgets
		self.canvas_image   = self.findChild(Qw.QLabel     , 'canvas_image' )
		self.canvas_color   = self.findChild(Qw.QLabel     , 'canvas_color' )
		self.canvas_result  = self.findChild(Qw.QLabel     , 'canvas_result')
		self.convert_button = self.findChild(Qw.QPushButton, 'convertButton')
		self.mode_choose    = self.findChild(Qw.QComboBox  , 'mode_choose'  )

		# link the widgets to function
		self.mode_choose.currentIndexChanged.connect(lambda i: self.switchState('ready'))
		self.convert_button.clicked.connect(self.generate)
		self.findChild(Qw.QAction, 'import_image' ).triggered.connect(self.importImage )
		self.findChild(Qw.QAction, 'import_color' ).triggered.connect(self.importColor )
		self.findChild(Qw.QAction, 'export_result').triggered.connect(self.exportResult)
		self.canvas_image .mousePressEvent = self.importImage
		self.canvas_color .mousePressEvent = self.importColor
		self.canvas_result.mousePressEvent = self.exportResult

		# init params
		self.image = None
		self.color = None
		self.result = None
		self.state = 'ready'
		self.error = None

		# Show the GUI
		self.show()

	# initializes canvas
	def initCanvas(self, canvas):
		size = canvas.rect().size()
		pixmap = QtGui.QPixmap(size.width(), size.height())
		pixmap.fill(QtGui.QColor('#00000000'))
		canvas.setPixmap(pixmap)

	# error message dialog
	def showError(self, msg):
		err = Qw.QErrorMessage(self)
		err.setWindowModality(QtCore.Qt.WindowModal)
		err.showMessage(msg)
		return

	# draw a QImage onto a canvas
	def drawImage(self, img, canvas):
		self.initCanvas(canvas)
		# scale to canvas size
		size = canvas.rect().size()
		scaled = img.scaled(size, QtCore.Qt.KeepAspectRatio)
		source = QtCore.QRect(0,0,0,0)
		source.setSize(scaled.size())
		target = QtCore.QRect(source)
		offset = (size - scaled.size())/2
		target.moveTopLeft(QtCore.QPoint(offset.width(), offset.height()))
		# draw the image
		painter = QtGui.QPainter(canvas.pixmap())
		painter.drawImage(target, scaled, source)
		painter.end()
		self.update()

	def switchState(self, st):
		self.state = st
		if st == 'process':
			self.convert_button.setProperty('enabled', False)
			self.mode_choose   .setProperty('enabled', False)
			self.convert_button.setProperty('text', 'CONVERTING')
		else:
			self.convert_button.setProperty('enabled', True)
			self.mode_choose   .setProperty('enabled', True)
		if st == 'done':
			self.convert_button.setProperty('text', 'DONE')
		if st == 'error':
			self.convert_button.setProperty('text', 'ERROR')
		if st == 'ready':
			self.convert_button.setProperty('text', 'CONVERT')

	# core function, produces result and displays its preview in the result canvas
	def generate(self):
		if self.state == 'process':
			return
		if self.image is None or self.color is None:
			return self.showError('Image or Coloring is missing!')
		self.switchState('process')

		def func():
			index = self.mode_choose.currentIndex()
			swf = True if index // 2 else False
			jcb = True if index % 2 else False
			colorFunction = lambda: Colorization(self.image, self.color, swf=swf, jcb=jcb)
			try:
				self.result = colorFunction() # Core function
			except Exception as e:
				self.error = repr(e)
				self.switchState('error')
			else:
				qimg = np2qimg(self.result)
				self.drawImage(qimg, self.canvas_result)
				self.switchState('done')

		def on_finished():
			if self.state == 'error':
				self.showError(self.error)

		# create thread
		thread = QtCore.QThread(self)
		thread.run = func
		thread.finished.connect(on_finished)
		thread.start()

	# imports image (grayscale)
	def importImage(self, e):	
		if self.state == 'process':
			return
		imagePath, _ = Qw.QFileDialog.getOpenFileName(self, "Import Image",
			os.getcwd(),'Grayscale Image (*.png *.jpg *.jpeg *.bmp)')
		if imagePath:
			self.image = cv2.imread(imagePath)
			if self.image is None:
				return self.showError('Unsupported File!')
			self.switchState('ready')
			qimg = np2qimg(self.image).rgbSwapped() # swap R & B due to QImage issues
			self.drawImage(qimg, self.canvas_image)

	# imports coloring (with alpha channel, only PNG)
	def importColor(self, e):
		if self.state == 'process':
			return
		imagePath, _ = Qw.QFileDialog.getOpenFileName(self, "Import Color",
			os.getcwd(),'Coloring Image (*.png *.jpg *.jpeg *.bmp)')
		if imagePath:
			self.color = cv2.imread(imagePath)
			if self.color is None:
				return self.showError('Unsupported File!')
			self.switchState('ready')
			qimg = np2qimg(self.color).rgbSwapped() # swap R & B due to QImage issues
			self.drawImage(qimg, self.canvas_color)

	# exports the result with respect to current preview in result canvas
	def exportResult(self, e):
		if self.state == 'process':
			return
		if self.result is None:
			self.generate() # if there isn't result yet, produce it first
		if self.result is None:
			return
		imagePath, _ = Qw.QFileDialog.getSaveFileName(self, "Save result",
			os.getcwd(),'Image (*.png *.jpg *.jpeg *.bmp)')
		if imagePath:
			cv2.imwrite(imagePath, self.result)

app = Qw.QApplication(sys.argv) # Create an instance of Qw.QApplication
window = UI() # Create an instance of our class
app.exec_() # Start the application