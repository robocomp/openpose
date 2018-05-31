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
import threading
import Queue
from PySide import QtGui, QtCore
from genericworker import *

sys.path.append('/opt/robocomp/lib')
#import librobocomp_qmat
#import librobocomp_osgviewer
#import librobocomp_innermodel

#class Cap(threading.Thread):
class Cap():
	def __init__(self, camera):
		#super(Cap,self).__init__()
		if camera == "webcam":
			self.cap = cv2.VideoCapture(0)
			self.url = False
		else:
			self.stream = requests.get(camera, stream=True)
			self.url = True
			if self.stream.status_code is not 200:
				print "Error connecting to stream ", camera
				sys.exit(1)
		
	def run(self):
		if self.url:
			byte = bytes()
			for chunk in self.stream.iter_content(chunk_size=1024):
				byte += chunk
				a = byte.find(b'\xff\xd8')
				b = byte.find(b'\xff\xd9')
				if a != -1 and b != -1:
					jpg = byte[a:b+2]
					byte = byte[b+2:]
					if len(jpg) > 0:
						img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
						return img
		else:
			ret, img = self.cap.read()
			return img
				
class SpecificWorker(GenericWorker):
	def __init__(self, proxy_map):
		super(SpecificWorker, self).__init__(proxy_map)
		self.myqueue = Queue.Queue()

	def setParams(self, params):
		try:
			camera = params["Camera"]
			self.cap = Cap(camera)
			#if camera == "webcam":
				#camera = 0
				#self.cap = cv2.VideoCapture(camera)
			#else:
				#self.stream = requests.get(camera, stream=True)
				
			self.fgbg = cv2.createBackgroundSubtractorMOG2()
			self.timer.timeout.connect(self.compute)
			self.Period = 5
			self.timer.start(self.Period)
	
		except:
			traceback.print_exc()
			print "Error reading config params"
			sys.exit()
		

	@QtCore.Slot()
	def compute(self):
			start = time.time()
			
			#frame = self.myqueue.get()
			frame = self.cap.run()
			#ret, frame = self.readImg(self.stream)
			cv2.imshow('OpenPose',frame)
			
			fgmask = self.fgbg.apply(frame)
			kernel = np.ones((5,5),np.uint8)
			erode = cv2.erode(fgmask, kernel, iterations = 2)
			dilate = cv2.dilate(erode, kernel, iterations = 2)
			
			if cv2.countNonZero(dilate) > 100:
				try:
					img = TImage(frame.shape[1], frame.shape[0], 3, ())
					img.image = frame.data
					people = self.openposeserver_proxy.processImage(img)
					self.drawPose(people, frame);				
					cv2.imshow('OpenPose',frame)
					
					try:
						self.openposepublishpeople_proxy.newPeople(0, people)
					except Ice.Exception, e:
						traceback.print_exc()
						print e
						
				except Ice.Exception, e:
					traceback.print_exc()
					print e
					
			ms = int((time.time() - start) * 1000)
			print "elapsed", ms, " ms. FPS: ", int(1000/ms)
			

	def drawPose(self, people, img):
		for person in people:
			color = np.random.random_integers(0,255,3)
			body = person.body
			if len(body) == 18:
				for v in body.values():
					if v.x != 0 or v.y != 0:
						cv2.circle(img,(v.x, v.y), 3, color , -1)
				
				#"nose","neck","lsh","lwrist","lelbow","rsh","relbow","rwrist","lhip","lknee","lfoot","rhip","rknee","rfoot","leye","reye","lear","rear";
				
				self.drawLine(body, img, "leye", "nose", color)
				self.drawLine(body, img, "reye", "nose", color)
				self.drawLine(body, img, "nose", "neck", color)
				self.drawLine(body, img, "lear", "leye", color)
				self.drawLine(body, img, "rear", "reye", color)
				self.drawLine(body, img, "neck", "rsh", color)
				self.drawLine(body, img, "neck", "lsh", color)
				self.drawLine(body, img, "rsh", "relbow", color)
				self.drawLine(body, img, "relbow", "rwrist", color)
				self.drawLine(body, img, "lsh", "lelbow", color)
				self.drawLine(body, img, "lelbow", "lwrist", color)
				self.drawLine(body, img, "neck", "lhip", color)
				self.drawLine(body, img, "neck", "rhip", color)
				self.drawLine(body, img, "rhip", "rknee", color)
				self.drawLine(body, img, "rknee", "rfoot", color)
				self.drawLine(body, img, "lhip", "lknee", color)
				self.drawLine(body, img, "lknee", "lfoot", color)
				
		 #cv2.imshow('OpenPose',img)
		
		
		
	def drawLine(self, body, img, one, two, color):
		if (body[one].x != 0 or body[one].y != 0) and (body[two].x != 0 or body[two].y != 0):
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
