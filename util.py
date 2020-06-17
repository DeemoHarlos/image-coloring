import numpy as np
import colorsys
import logging
import scipy.sparse
from scipy.sparse.linalg import spsolve, lsqr

# affinity functions, calculate weights of pixels in a window by their intensity.
def affinity_a(w):
	nbs = np.array(w.neighbors)
	sY = nbs[:,2]
	cY = w.center[2]
	diff = sY - cY
	sig = np.var(np.append(sY, cY))
	if sig < 1e-6:
		sig = 1e-6  
	wrs = np.exp(- np.power(diff,2) / (sig * 2.0))
	wrs = - wrs / np.sum(wrs)
	nbs[:,2] = wrs
	return nbs

# translate (row,col) to/from sequential number
def to_seq(r, c, rows):
	return c * rows + r

def fr_seq(seq, rows):
	r = seq % rows
	c = int((seq - r) / rows)
	return (r, c)

# combine 3 channels of YUV to a RGB photo: n x n x 3 array
def yuv_channels_to_rgb(cY, cU, cV, pic_yuv):
	pic_rows, pic_cols = pic_yuv.shape[0], pic_yuv.shape[1]
	ansRGB = [colorsys.yiq_to_rgb(cY[i],cU[i],cV[i]) for i in range(len(pic_yuv[:, :, 0].reshape(-1)))]
	ansRGB = np.array(ansRGB)
	pic_ansRGB = np.zeros(pic_yuv.shape)
	pic_ansRGB[:,:,0] = ansRGB[:,0].reshape(pic_rows, pic_cols, order='F')
	pic_ansRGB[:,:,1] = ansRGB[:,1].reshape(pic_rows, pic_cols, order='F')
	pic_ansRGB[:,:,2] = ansRGB[:,2].reshape(pic_rows, pic_cols, order='F')
	return pic_ansRGB

def init_logger():
	FORMAT = '%(asctime)-15s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)
	logger = logging.getLogger()
	return logger

def Spsolve(matA, b_u, b_v):
	ansU = spsolve(matA, b_u)
	ansV = spsolve(matA, b_v)
	return ansU, ansV

def jacobi(A, b, x, n, verbose=False):
	D = A.diagonal()
	R = A - scipy.sparse.diags(D)
	for i in range(n):
		x = (b - R.dot(x)) / D
	return x