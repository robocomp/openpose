#
# Copyright (C) 2018 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#
import sys, os, traceback, time
import cv2
import numpy as np
import requests
import thread

from PySide import QtGui, QtCore
from genericworker import *

sys.path.append('/opt/robocomp/lib')
import librobocomp_qmat
import librobocomp_osgviewer
import librobocomp_innermodel

class SpecificWorker(GenericWorker):
	def __init__(self, proxy_map):
		super(SpecificWorker, self).__init__(proxy_map)
		self.timer.timeout.connect(self.compute)
		self.Period = 50
		self.timer.start(self.Period)

	def setParams(self, params):
		try:
			camera0 = params["Camera0"]
			camera1 = params["Camera1"]
			
			if camera == "webcam":
				camera = 0

		except:
			traceback.print_exc()
			print "Error reading config params"
			sys.exit()

		#self.cap = cv2.VideoCapture(camera)
		self.stream0 = requests.get(camera0, stream=True)
		self.stream1 = requests.get(camera1, stream=True)
		
		#if (self.cap.isOpened()== False): 
			#print("Error opening video stream or file")
					
		return True

	@QtCore.Slot()
	def compute(self):
			print 'SpecificWorker.compute...'
			#ret, frame = self.cap.read()
			ret0, frame0 = self.readImg(self.stream0)
			ret1, frame1 = self.readImg(self.stream1)
			
			
			try:
				imgs = ()
				img = TImage(frame.shape[1], frame.shape[0], 3, ())
				img.image = frame0.data
				people0 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people, frame0) )
				
				img.image = frame1.data
				people1 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people, frame1) )
				
				imggrid = self.drawGrid(2,1, imgs)
				cv2.imshow('OpenPose',imggrid)
				
			except Ice.Exception, e:
				traceback.print_exc()
				print e

			return True

	def drawPose(self, people, img):
		for person in people:
			body = person.body
			if len(body) == 18:
				for v in body.values():
					if v.x != 0 or v.y != 0:
						color = np.random.random_integers(0,255,3)
						cv2.circle(img,(v.x, v.y), 3, color , -1)
				
				#"nose","neck","lsh","lwrist","lelbow","rsh","relbow","rwrist","lhip","lknee","lfoot","rhip","rknee","rfoot","leye","reye","lear","rear";
				
				self.drawLine(body, img, "leye", "nose")
				self.drawLine(body, img, "reye", "nose")
				self.drawLine(body, img, "nose", "neck")
				self.drawLine(body, img, "lear", "leye")
				self.drawLine(body, img, "rear", "reye")
				self.drawLine(body, img, "neck", "rsh")
				self.drawLine(body, img, "neck", "lsh")
				self.drawLine(body, img, "rsh", "relbow")
				self.drawLine(body, img, "relbow", "rwrist")
				self.drawLine(body, img, "lsh", "lelbow")
				self.drawLine(body, img, "lelbow", "lwrist")
				self.drawLine(body, img, "neck", "lhip")
				self.drawLine(body, img, "neck", "rhip")
				self.drawLine(body, img, "rhip", "rknee")
				self.drawLine(body, img, "rknee", "rfoot")
				self.drawLine(body, img, "lhip", "lknee")
				self.drawLine(body, img, "lknee", "lfoot")
				
		 #cv2.imshow('OpenPose',img)
		
	def drawLine(self, body, img, one, two):
		if (body[one].x != 0 or body[one].y != 0) and (body[two].x != 0 or body[two].y != 0):
			color = np.random.random_integers(0,255,3)
			cv2.line(img, (body[one].x,body[one].y), (body[two].x, body[two].y), color, 2)
			

	def readImg(self, stream):
		bytes = ''
		for chunk in self.stream.iter_content(chunk_size=1024):
			bytes += chunk
			a = bytes.find(b'\xff\xd8')
			b = bytes.find(b'\xff\xd9')
			if a != -1 and b != -1:
				jpg = bytes[a:b+2]
				bytes = bytes[b+2:]
				if len(jpg) > 0:
					img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
					return True, img
		
	def drawGrid(self, w, h, imgs):
		n = w*h
		if any(i.shape != imgs[0].shape for i in imgs[1:]):
			raise ValueError('Not all images have the same shape.')
		img_h, img_w, img_c = imgs[0].shape
		m_x = 0
		m_y = 0
		imgmatrix = np.zeros((img_h * h + m_y * (h - 1),img_w * w + m_x * (w - 1),img_c),np.uint8)
		#doble comentario
		# imgmatrix.fill(255)    
		positions = itertools.product(range(w), range(h))
		for (x_i, y_i), img in itertools.izip(positions, imgs):
			x = x_i * (img_w + m_x)
			y = y_i * (img_h + m_y)
			imgmatrix[y:y+img_h, x:x+img_w, :] = img

		return imgmatrix
