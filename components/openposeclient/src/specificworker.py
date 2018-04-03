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
			camera = params["Camera"]
			if camera == "webcam":
				camera = 0

		except:
			traceback.print_exc()
			print "Error reading config params"
			sys.exit()

		self.cap = cv2.VideoCapture(0)
		
		if (self.cap.isOpened()== False): 
			print("Error opening video stream or file")
		return True

	@QtCore.Slot()
	def compute(self):
		print 'SpecificWorker.compute...'
		ret, frame = self.cap.read()
		try:
			img = TImage(frame.shape[1], frame.shape[0], 3, ())
			img.image = frame.data
			people = self.openposeserver_proxy.processImage(img)
			print people
			self.drawPose(people, frame)
			
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
				
		cv2.imshow('OpenPose',img)
		
	def drawLine(self, body, img, one, two):
		if (body[one].x != 0 or body[one].y != 0) and (body[two].x != 0 or body[two].y != 0):
			color = np.random.random_integers(0,255,3)
			cv2.line(img, (body[one].x,body[one].y), (body[two].x, body[two].y), color, 2)
			
			
			
			
			
