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
import itertools
from flask import Flask, render_template, Response


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
			camera2 = params["Camera2"]
			camera3 = params["Camera3"]
			camera4 = params["Camera4"]
			camera5 = params["Camera5"]
			
			if camera0 == "webcam":
				camera0 = 0
			if camera1 == "webcam":
				camera1 = 0
			if camera2 == "webcam":
				camera2 = 0
			if camera3 == "webcam":
				camera3 = 0
			if camera4 == "webcam":
				camera4 = 0
			if camera5 == "webcam":
				camera5 = 0

		except:
			traceback.print_exc()
			print "Error reading config params"
			sys.exit()

		#self.cap = cv2.VideoCapture(camera)
		print camera0, camera1
		self.stream0 = requests.get(camera0, stream=True)
		self.stream1 = requests.get(camera1, stream=True)
		self.stream2 = requests.get(camera2, stream=True)
		self.stream3 = requests.get(camera3, stream=True)
		self.stream4 = requests.get(camera4, stream=True)
		self.stream5 = requests.get(camera5, stream=True)
		
		
		
		#if (self.cap.isOpened()== False): 
			#print("Error opening video stream or file")
		return True

	@QtCore.Slot()
	def compute(self):
			#print 'SpecificWorker.compute...'
			#ret, frame = self.cap.read()
			ret0, frame0 = self.readImg(self.stream0)
			ret1, frame1 = self.readImg(self.stream1)
			ret2, frame2 = self.readImg(self.stream2)
			ret3, frame3 = self.readImg(self.stream3)
			ret4, frame4 = self.readImg(self.stream4)
			ret5, frame5 = self.readImg(self.stream5)
			try:
				imgs = []
				#frame a frame0, jose
				img = TImage(frame0.shape[1], frame0.shape[0], 3, ())
				
				img.image = frame0.data
				people0 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people0, frame0) )

				img.image = frame1.data
				people1 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people1, frame1) )
				
				img.image = frame2.data
				people2 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people2, frame2) )
				
				img.image = frame3.data
				people3 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people3, frame3) )
				
				img.image = frame4.data
				people4 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people4, frame4) )
				
				img.image = frame5.data
				people5 = self.openposeserver_proxy.processImage(img)
				imgs.append( self.drawPose(people5, frame5) )
				
				imggrid = self.drawGrid(3,2, imgs)
				cv2.imshow('OpenPose',imggrid)
				ret, jpeg = cv2.imencode('.jpg', imggrid)
				self.jpegResult = jpeg.tobytes()
				
			except Ice.Exception, e:
				traceback.print_exc()
				print e
			
			#return True

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
		#return jose
		return img
		
	def drawLine(self, body, img, one, two):
		if (body[one].x != 0 or body[one].y != 0) and (body[two].x != 0 or body[two].y != 0):
			color = np.random.random_integers(0,255,3)
			cv2.line(img, (body[one].x,body[one].y), (body[two].x, body[two].y), color, 2)
			

	def readImg(self, stream):
		bytes = ''
		# stream a stream0, jose
		for chunk in stream.iter_content(chunk_size=1024):
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
		for j in range(0,5):
			if any(i.shape != imgs[j].shape for i in imgs[1:]):
				raise ValueError('Not all images have the same shape.')
			img_h, img_w, img_c = imgs[j].shape
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
