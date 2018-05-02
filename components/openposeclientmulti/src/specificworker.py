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
from flask import Flask, render_template, Response
import cv2
import numpy as np
import requests
import threading
import Queue
import itertools
from PySide import QtGui, QtCore
from genericworker import *

sys.path.append('/opt/robocomp/lib')
#import librobocomp_qmat
#import librobocomp_osgviewer
#import librobocomp_innermodel
        
cola = []        
        
class Action(object):
	def __init__(self, img):
		self.img = img
	def __call__(self, *args):
		def generate():
			#print len(self.img[0])
			while (True):
				time.sleep(0.05)
				yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + self.img[0] + b'\r\n\r\n')
		return Response(generate(),  mimetype='multipart/x-mixed-replace; boundary=frame')
        
class MyFlask(threading.Thread):
	app = None
	def __init__(self, name, img):
		threading.Thread.__init__(self)
		self.app = Flask(name)
		self.img = img
		self.app.add_url_rule('/', '/', Action(self.img))
		self.app.add_url_rule('/video_feed', 'video', Action(self.img))
	
	def run(self):
		time.sleep(3)
		self.app.run(host='0.0.0.0', port=8080, threaded=True)


#####################################################################

#class Cap(threading.Thread):
	#def __init__(self, camera, myqueue):
		#super(Cap,self).__init__()
		#self.stream = requests.get(camera, stream=True)
		#self.myqueue = myqueue
		#if self.stream.status_code is not 200:
			#print "Error connecting to stream ", camera
			#sys.exit(1)
		
	#def run(self):
		#byte = bytes()
		#for chunk in self.stream.iter_content(chunk_size=1024):
			#byte += chunk
			#a = byte.find(b'\xff\xd8')
			#b = byte.find(b'\xff\xd9')
			#if a != -1 and b != -1:
				#jpg = byte[a:b+2]
				#byte = byte[b+2:]
				#if len(jpg) > 0:
					#img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
					#self.myqueue.put(img)	
	
#class Cap(threading.Thread):
	#def __init__(self, camera, img):
		#super(Cap,self).__init__()
		#self.stream = requests.get(camera, stream=True)
		#self.img = img
		#if self.stream.status_code is not 200:
			#print "Error connecting to stream ", camera
			#sys.exit(1)
		
	#def run(self):
		#byte = bytes()
		#ready[0] = False
		#for chunk in self.stream.iter_content(chunk_size=1024):
			#byte += chunk
			#a = byte.find(b'\xff\xd8')
			#b = byte.find(b'\xff\xd9')
			#if a != -1 and b != -1:
				#jpg = byte[a:b+2]
				#byte = byte[b+2:]
				#if len(jpg) > 0:
					#img[0] = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
					#ready[0] = True
					
	
#######################################################################					

class SpecificWorker(GenericWorker):

	def __init__(self, proxy_map):
		super(SpecificWorker, self).__init__(proxy_map)

	def setParams(self, params):
		self.cameras = []
		try:
			for r in range(0,100):
				camera = "Camera" + str(r)
				self.cameras.append( params[camera] )
		except:
			print "Cameras: "
			for c in self.cameras:
				print "\t ", c
		
		self.streams = []
		self.fgbgs = []
		for c in self.cameras:
			self.streams.append( requests.get(c, stream=True))
			self.fgbgs.append( cv2.createBackgroundSubtractorMOG2() )
		
		#Flask
		self.imgToFlask = [None]	#to pass to Flask
		self.flask = MyFlask('flask', self.imgToFlask)
		self.flask.start()
		
		self.timer.timeout.connect(self.compute)
		self.Period = 5
		self.timer.start(self.Period)
		
		self.imgs = [None] * len(self.cameras)
		return True

	@QtCore.Slot()
	def compute(self):
			
			inicio = time.time()
			kernel = np.ones((5,5),np.uint8)
			
			try:
				for c in range(len(self.cameras)):
					ret, frame = self.readImg(self.streams[c])
					fgmask = self.fgbgs[c].apply(frame)
					erode = cv2.erode(fgmask, kernel, iterations = 2)
					dilate = cv2.dilate(erode, kernel, iterations = 2)
					if cv2.countNonZero(dilate) > 100:
						img = TImage(frame.shape[1], frame.shape[0], 3, frame.data)
						people = self.openposeserver_proxy.processImage(img)
						self.imgs[c] = self.drawPose(people, frame) 

			except Ice.Exception, e:
				traceback.print_exc()
				print e
				
			imggrid = self.drawGrid(3,2, self.imgs)
			textImg = np.zeros(imggrid.shape, np.uint8 );
			cv2.putText(textImg, "NOT RECORDING", (textImg.shape[1]/2 - 500, textImg.shape[0]/2), cv2.FONT_HERSHEY_SIMPLEX, 4.0, (30,30,30), 4);
			#cv2.rotate(textImg, -45, textImg);
			imggrid = imggrid + textImg;
			ret, jpeg = cv2.imencode('.jpg', imggrid)
			self.imgToFlask[0] = jpeg.tobytes()
			
			ms = int((time.time() - inicio) * 1000)
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
		#return jose
		return img
		
	def drawLine(self, body, img, one, two, color):
		if (body[one].x != 0 or body[one].y != 0) and (body[two].x != 0 or body[two].y != 0):
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
