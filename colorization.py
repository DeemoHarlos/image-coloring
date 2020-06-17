# import packages
import numpy as np
import sys
import matplotlib.pyplot as plt
import colorsys
import scipy
import cv2 
import logging
from scipy.sparse import csr_matrix

from util import * 

# the window class, find the neighbor pixels around the center.
class WindowNeighbor:
	def __init__(self, width, center, pic, swf):
		# center is a list of [row, col, Y_intensity]
		self.center = [center[0], center[1], pic[center][0]]
		self.width = width
		self.neighbors = None
		self.constraint = (1 + width) ** 2
		self.find_neighbors(pic, swf)
		self.mean = None
		self.var = None

	# Use side window filtering to deal with color leakage on edge problem 
	# window width = 1, window size(3 * 3)
	def create_sub_windows(self, ix_r_min, ix_r_max, ix_c_min, ix_c_max):
		# [r_min, r_max, c_min, c_max]
		tl = np.array([ix_r_min, self.center[0] + 1, ix_c_min, self.center[1] + 1])
		bl = np.array([ix_r_min, self.center[0] + 1, self.center[1], ix_c_max])
		tr = np.array([self.center[0], ix_r_max, ix_c_min, self.center[1] + 1])
		br = np.array([self.center[0], ix_r_max, self.center[1], ix_c_max])
		t = np.array([ix_r_min, ix_r_max, ix_c_min, self.center[1] + 1])
		b = np.array([ix_r_min, ix_r_max, self.center[1], ix_c_max])
		r = np.array([self.center[0], ix_r_max, ix_c_min, ix_c_max])
		l = np.array([ix_r_min, self.center[0] + 1, ix_c_min, ix_c_max])
		sub_windows = [tl, bl, tr, br, t, b, r, l]
		return sub_windows

	def find_neighbors(self, pic, swf):
		self.neighbors = []
		ix_r_min = max(0, self.center[0] - self.width)
		ix_r_max = min(pic.shape[0], self.center[0] + self.width + 1)
		ix_c_min = max(0, self.center[1] - self.width)
		ix_c_max = min(pic.shape[1], self.center[1] + self.width + 1)
		if swf:
			sub_windows = self.create_sub_windows(ix_r_min, ix_r_max, ix_c_min, ix_c_max)
			self._min = float("inf")
			for _window in sub_windows:
				rl, rr, cl, cr = _window[0], _window[1], _window[2], _window[3]
				# if length = 1 means only center is picked
				if len(pic[rl:rr, cl:cr, 0].reshape(-1)) < self.constraint:
					continue
				distance = np.abs(np.mean(pic[rl:rr, cl:cr, 0]) - pic[self.center[0], self.center[1], 0])
				if distance <= self._min:
					self._min = distance
					window = _window
			rl, rr, cl, cr = window[0], window[1], window[2], window[3]
		else:
			rl, rr, cl, cr = ix_r_min, ix_r_max, ix_c_min, ix_c_max
		for r in range(rl, rr):
			for c in range(cl, cr):
				if r == self.center[0] and c == self.center[1]:
					continue
				self.neighbors.append([r,c,pic[r,c,0]])    

	def __str__(self):
		return 'windows c=(%d, %d, %f) size: %d' % (self.center[0], self.center[1], self.center[2], len(self.neighbors))

def Colorization(pic_o_rgb, pic_m_rgb, window_size = None, swf = False, jcb = False, iteration = 5000):
	log = init_logger()
	np.set_printoptions(precision=8, suppress=True)
	# Different default window size for swf and non-swf
	if     swf and window_size is None: window_size = 5
	if not swf and window_size is None: window_size = 3
	if window_size % 2 != 1:
		log.info("window size should be odd number!!")
		raise ValueError
	wd_width = (window_size - 1) // 2
	# pic_o_rgb = cv2.imread(path_pic)
	pic_o_rgb = cv2.cvtColor(pic_o_rgb, cv2.COLOR_BGR2RGB)
	pic_o = pic_o_rgb.astype(float)/255
	# pic_m_rgb = cv2.imread(path_pic_marked)
	pic_m_rgb = cv2.cvtColor(pic_m_rgb, cv2.COLOR_BGR2RGB)
	pic_m = pic_m_rgb.astype(float)/255

	(pic_rows, pic_cols, _) = pic_o.shape
	pic_size = pic_rows * pic_cols
	channel_Y,_,_ = colorsys.rgb_to_yiq(pic_o[:,:,0],pic_o[:,:,1],pic_o[:,:,2])
	_,channel_U,channel_V = colorsys.rgb_to_yiq(pic_m[:,:,0],pic_m[:,:,1],pic_m[:,:,2])

	map_colored = (abs(channel_U) + abs(channel_V)) > 0.0001

	pic_yuv = np.dstack((channel_Y, channel_U, channel_V))
	weightData = []
	num_pixel_bw = 0

	# build the weight matrix for each window.
	for c in range(pic_cols):
		for r in range(pic_rows):
			res = []
			w = WindowNeighbor(wd_width, (r,c), pic_yuv, swf)
			if not map_colored[r,c]:
				weights = affinity_a(w)
				for e in weights:
					# 0: center coordinate, 1: (weight e row, weight e col), 2: weight
					weightData.append([w.center,(e[0],e[1]), e[2]])
			# 0: center coordinate, 1: (center row, center col), 2: weight
			weightData.append([w.center, (w.center[0],w.center[1]), 1.])

	sp_idx_rc_data = [[to_seq(e[0][0], e[0][1], pic_rows), to_seq(e[1][0], e[1][1], pic_rows), e[2]] for e in weightData]
	sp_idx_rc = np.array(sp_idx_rc_data, dtype=np.integer)[:,0:2]
	sp_data = np.array(sp_idx_rc_data, dtype=np.float64)[:,2]
	matA = csr_matrix((sp_data, (sp_idx_rc[:,0], sp_idx_rc[:,1])), shape=(pic_size, pic_size))

	#set b vector
	b_u = np.zeros(pic_size)
	b_v = np.zeros(pic_size)
	idx_colored = np.nonzero(map_colored.reshape(pic_size, order='F'))
	pic_u_flat = pic_yuv[:,:,1].reshape(pic_size, order='F')
	b_u[idx_colored] = pic_u_flat[idx_colored]

	pic_v_flat = pic_yuv[:,:,2].reshape(pic_size, order='F')
	b_v[idx_colored] = pic_v_flat[idx_colored]

	# Solve Ax = b 
	ansY = pic_yuv[:,:,0].reshape(pic_size, order='F')
	log.info('Optimizing Ax=b')
	if jcb:
		ansU = jacobi(matA, b_u, x=np.zeros(matA.shape[0]), n = iteration)
		ansV = jacobi(matA, b_v, x=np.zeros(matA.shape[0]), n = iteration)
	else:
		ansU, ansV = Spsolve(matA, b_u, b_v) 
	log.info('Optimized Ax=b')

	# concate ansY, ansU, ansV and transform image from YUV to RGB
	pic_ans = yuv_channels_to_rgb(ansY,ansU,ansV, pic_yuv)
	return pic_ans * 255
