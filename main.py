import os
import sys
import math
import numpy as np
import cv2
from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic
import qimage2ndarray as qimg2np
# Also import the actual function!

class UI(QtWidgets.QMainWindow):
	def __init__(self):
		super(UI, self).__init__() # Call the inherited classes __init__ method
		uic.loadUi('gui.ui', self) # Load the .ui file

		self.canvas_image  = self.findChild(QtWidgets.QLabel, 'canvas_image' )
		self.canvas_color  = self.findChild(QtWidgets.QLabel, 'canvas_color' )
		self.canvas_result = self.findChild(QtWidgets.QLabel, 'canvas_result')

		self.convertButton = self.findChild(QtWidgets.QPushButton, 'convertButton').clicked.connect(self.generate)
		self.findChild(QtWidgets.QAction, 'import_image' ).triggered.connect(self.importImage )
		self.findChild(QtWidgets.QAction, 'import_color' ).triggered.connect(self.importColor )
		self.findChild(QtWidgets.QAction, 'export_result').triggered.connect(self.exportResult)
		self.canvas_image .mousePressEvent = self.importImage
		self.canvas_color .mousePressEvent = self.importColor
		self.canvas_result.mousePressEvent = self.exportResult

		self.offset = self.rect().topLeft() + self.menuBar.rect().bottomLeft()

		self.image = None
		self.color = None
		self.result = None

		self.show() # Show the GUI

	def initCanvas(self, canvas):
		size = canvas.rect().size()
		pixmap = QtGui.QPixmap(size.width(), size.height())
		pixmap.fill(QtGui.QColor('#00000000'))
		canvas.setPixmap(pixmap)

	def showError(self, msg):
		err = QtWidgets.QErrorMessage(self)
		err.setWindowModality(QtCore.Qt.WindowModal)
		err.showMessage(msg)
		return

	def drawImage(self, img, canvas):
		self.initCanvas(canvas)
		size = canvas.rect().size()
		scaled = img.scaled(size, QtCore.Qt.KeepAspectRatio)
		source = QtCore.QRect(0,0,0,0)
		source.setSize(scaled.size())
		target = QtCore.QRect(source)
		offset = (size - scaled.size())/2
		target.moveTopLeft(QtCore.QPoint(offset.width(), offset.height()))
		painter = QtGui.QPainter(canvas.pixmap())
		painter.drawImage(target, scaled, source)
		painter.end()
		self.update()

	def generate(self):
		if self.image is None or self.color is None:
			return self.showError('Image or Color is missing!')
		self.result = self.color.copy() # Substitute this line with the actual function
		qimg = qimg2np.array2qimage(self.result).rgbSwapped()
		self.drawImage(qimg, self.canvas_result)

	def importImage(self, e):
		imagePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Image",
			os.getcwd(),'Grayscale Image (*.png *.jpg *.jpeg *.bmp)')
		if imagePath:
			self.image = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
			if self.image is None:
				return self.showError('Unsupported File!')
			qimg = qimg2np.array2qimage(self.image)
			self.drawImage(qimg, self.canvas_image)

	def importColor(self, e):
		imagePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Color",
			os.getcwd(),'RGBA Image (*.png)')
		if imagePath:
			self.color = cv2.imread(imagePath, cv2.IMREAD_UNCHANGED)
			if self.color is None:
				return self.showError('Unsupported File!')
			qimg = qimg2np.array2qimage(self.color).rgbSwapped()
			self.drawImage(qimg, self.canvas_color)

	def exportResult(self, e):
		if self.result is None:
			self.generate()
		if self.result is None:
			return
		imagePath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save result",
			os.getcwd(),'Image (*.png *.jpg *.jpeg *.bmp)')
		if imagePath:
			cv2.imwrite(imagePath, self.result)

app = QtWidgets.QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = UI() # Create an instance of our class
app.exec_() # Start the application