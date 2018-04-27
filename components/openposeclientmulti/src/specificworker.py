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

class Cap(threading.Thread):
	def __init__(self, camera, myqueue):
		super(Cap,self).__init__()
		self.stream = requests.get(camera, stream=True)
		self.myqueue = myqueue
		if self.stream.status_code is not 200:
			print "Error connecting to stream ", camera
			sys.exit(1)
		
	def run(self):
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
					self.myqueue.put(img)	
					
#######################################################################					

class SpecificWorker(GenericWorker):

	def __init__(self, proxy_map):
		super(SpecificWorker, self).__init__(proxy_map)
		self.myqueue0 = Queue.Queue()
		self.myqueue1 = Queue.Queue()
		self.myqueue2 = Queue.Queue()
		self.myqueue3 = Queue.Queue()
		self.myqueue4 = Queue.Queue()
		self.myqueue5 = Queue.Queue()

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

		self.stream0 = requests.get(camera0, stream=True)
		self.stream1 = requests.get(camera1, stream=True)
		self.stream2 = requests.get(camera2, stream=True)
		self.stream3 = requests.get(camera3, stream=True)
		self.stream4 = requests.get(camera4, stream=True)
		self.stream5 = requests.get(camera5, stream=True)
		
		self.fgbg0 = cv2.createBackgroundSubtractorMOG2()
		self.fgbg1 = cv2.createBackgroundSubtractorMOG2()
		self.fgbg2 = cv2.createBackgroundSubtractorMOG2()
		self.fgbg3 = cv2.createBackgroundSubtractorMOG2()
		self.fgbg4 = cv2.createBackgroundSubtractorMOG2()
		self.fgbg5 = cv2.createBackgroundSubtractorMOG2()
		
		#self.cap0 = Cap(camera0, self.myqueue0)
		#self.cap0.start()
		#self.cap1 = Cap(camera1, self.myqueue1)
		#self.cap1.start()
		#self.cap2 = Cap(camera2, self.myqueue2)
		#self.cap2.start()
		#self.cap3 = Cap(camera3, self.myqueue3)
		#self.cap3.start()
		#self.cap4 = Cap(camera4, self.myqueue4)
		#self.cap4.start()
		#self.cap5 = Cap(camera5, self.myqueue5)
		#self.cap5.start()
		
		self.img = ['f']
		self.flask = MyFlask('flask', self.img)
		self.flask.start()
		
		self.timer.timeout.connect(self.compute)
		self.Period = 5
		self.timer.start(self.Period)
		
		self.imgs = [0,1,2,3,4,5]
		return True

	@QtCore.Slot()
	def compute(self):
			
			inicio = time.time()
			
			kernel = np.ones((5,5),np.uint8)
			
			ret0, frame0 = self.readImg(self.stream0)
			fgmask0 = self.fgbg0.apply(frame0)
			erode = cv2.erode(fgmask0, kernel, iterations = 2)
			dilate0 = cv2.dilate(erode, kernel, iterations = 2)
				
			ret1, frame1 = self.readImg(self.stream1)
			fgmask1 = self.fgbg1.apply(frame1)
			erode = cv2.erode(fgmask1, kernel, iterations = 2)
			dilate1 = cv2.dilate(erode, kernel, iterations = 2)
			
			ret2, frame2 = self.readImg(self.stream2)
			fgmask2 = self.fgbg2.apply(frame2)
			erode = cv2.erode(fgmask2, kernel, iterations = 2)
			dilate2 = cv2.dilate(erode, kernel, iterations = 2)
			
			ret3, frame3 = self.readImg(self.stream3)
			fgmask3 = self.fgbg3.apply(frame3)
			erode = cv2.erode(fgmask3, kernel, iterations = 2)
			dilate3 = cv2.dilate(erode, kernel, iterations = 2)
			
			ret4, frame4 = self.readImg(self.stream4)
			fgmask4 = self.fgbg4.apply(frame4)
			erode = cv2.erode(fgmask4, kernel, iterations = 2)
			dilate4 = cv2.dilate(erode, kernel, iterations = 2)
			
			ret5, frame5 = self.readImg(self.stream5)
			fgmask5 = self.fgbg5.apply(frame5)
			erode = cv2.erode(fgmask5, kernel, iterations = 2)
			dilate5 = cv2.dilate(erode, kernel, iterations = 2)
		
			
			#frame0 = self.myqueue0.get()			
			#frame1 = self.myqueue1.get()
			#frame2 = self.myqueue2.get()
			#frame3 = self.myqueue3.get()
			#frame4 = self.myqueue4.get()
			#frame5 = self.myqueue5.get()
			
			try:
				img = TImage(frame0.shape[1], frame0.shape[0], 3, ())
				if cv2.countNonZero(dilate0) > 100:
					img.image = frame0.data
					people0 = self.openposeserver_proxy.processImage(img)
					self.imgs[0] = self.drawPose(people0, frame0) 

				if cv2.countNonZero(dilate1) > 100:
					img.image = frame1.data
					people1 = self.openposeserver_proxy.processImage(img)
					self.imgs[1] = self.drawPose(people1, frame1)
				
				if cv2.countNonZero(dilate2) > 100:
					img.image = frame2.data
					people2 = self.openposeserver_proxy.processImage(img)
					self.imgs[2] = self.drawPose(people2, frame2) 
					
				if cv2.countNonZero(dilate3) > 100:
					img.image = frame3.data
					people3 = self.openposeserver_proxy.processImage(img)
					self.imgs[3] = self.drawPose(people3, frame3)
				
				if cv2.countNonZero(dilate4) > 100:
					img.image = frame4.data
					people4 = self.openposeserver_proxy.processImage(img)
					self.imgs[4] =  self.drawPose(people4, frame4)
				
				if cv2.countNonZero(dilate5) > 100:
					img.image = frame5.data
					people5 = self.openposeserver_proxy.processImage(img)
					self.imgs[5] = self.drawPose(people5, frame5)
				
				imggrid = self.drawGrid(3,2, self.imgs)
				textImg = np.zeros(imggrid.shape, np.uint8 );
				cv2.putText(textImg, "NOT RECORDING", (textImg.shape[1]/2 - 450, textImg.shape[0]/2), cv2.FONT_HERSHEY_SIMPLEX, 4.0, (20,20,20), 4);
				cv2.rotate(textImg, -45, textImg);
				imggrid = imggrid + textImg;
				ret, jpeg = cv2.imencode('.jpg', imggrid)
				self.img[0] = jpeg.tobytes()
				
				ms = int((time.time() - inicio) * 1000)
				print "elapsed", ms, " ms. FPS: ", int(1000/ms)
				
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
