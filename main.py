import os, sys
# import numpy as np # Actually can be omitted
import cv2
from PyQt5 import Qt, QtCore, QtGui, QtWidgets as Qw, uic
from qimage2ndarray import array2qimage as np2qimg
# Also import the actual function!

class UI(Qw.QMainWindow):
	def __init__(self):
		# initial GUI
		super(UI, self).__init__()
		uic.loadUi('gui.ui', self)

		# get the canvas
		self.canvas_image  = self.findChild(Qw.QLabel, 'canvas_image' )
		self.canvas_color  = self.findChild(Qw.QLabel, 'canvas_color' )
		self.canvas_result = self.findChild(Qw.QLabel, 'canvas_result')

		# link the widgets to function
		self.findChild(Qw.QPushButton, 'convertButton').clicked.connect(self.generate)
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

	# core function, produces result and displays its preview in the result canvas
	def generate(self):
		if self.image is None or self.color is None:
			return self.showError('Image or Color is missing!')
		self.result = self.color.copy() # Substitute this line with the actual function
		qimg = np2qimg(self.result).rgbSwapped() # swap R & B due to QImage issues
		self.drawImage(qimg, self.canvas_result)

	# imports image (grayscale)
	def importImage(self, e):
		imagePath, _ = Qw.QFileDialog.getOpenFileName(self, "Import Image",
			os.getcwd(),'Grayscale Image (*.png *.jpg *.jpeg *.bmp)')
		if imagePath:
			self.image = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
			if self.image is None:
				return self.showError('Unsupported File!')
			qimg = np2qimg(self.image)
			self.drawImage(qimg, self.canvas_image)

	# imports coloring (with alpha channel, only PNG)
	def importColor(self, e):
		imagePath, _ = Qw.QFileDialog.getOpenFileName(self, "Import Color",
			os.getcwd(),'RGBA Image (*.png)')
		if imagePath:
			self.color = cv2.imread(imagePath, cv2.IMREAD_UNCHANGED)
			if self.color is None:
				return self.showError('Unsupported File!')
			qimg = np2qimg(self.color).rgbSwapped() # swap R & B due to QImage issues
			self.drawImage(qimg, self.canvas_color)

	# exports the result with respect to current preview in result canvas
	def exportResult(self, e):
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