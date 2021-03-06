#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

# \mainpage RoboComp::openposeclientmulti
#
# \section intro_sec Introduction
#
# Some information about the component...
#
# \section interface_sec Interface
#
# Descroption of the interface provided...
#
# \section install_sec Installation
#
# \subsection install1_ssec Software depencences
# Software dependences....
#
# \subsection install2_ssec Compile and install
# How to compile/install the component...
#
# \section guide_sec User guide
#
# \subsection config_ssec Configuration file
#
# <p>
# The configuration file...
# </p>
#
# \subsection execution_ssec Execution
#
# Just: "${PATH_TO_BINARY}/openposeclientmulti --Ice.Config=${PATH_TO_CONFIG_FILE}"
#
# \subsection running_ssec Once running
#
#
#

import sys, traceback, IceStorm, subprocess, threading, time, Queue, os, copy

# Ctrl+c handling
import signal
import threading

from PySide import QtGui, QtCore
from specificworker import *
from flask import Flask, render_template, Response
import time


#appp = Flask(__name__)

#@appp.route('/')
#def index():
    #return render_template('index.html')

#def gen():
	#while True:
		##Si no realizamos un sleep, se generan tantos frames por segundo que la maquina no da a basto y hay que reiniciarla
		##Como el server da unos 11 frames de media por segundo, no tiene sentido disminuir el tiempo de sleep, el cual, en 0.8 da 11.X frames por segundo
		#time.sleep(0.08)
		#yield (b'--frame\r\n'
			#b'Content-Type: image/jpeg\r\n\r\n' + worker.jpegResult + b'\r\n\r\n')
	
			
#@appp.route('/video_feed')
#def video_feed():
	#return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

#def ejecutarFlask():
	#time.sleep(3)
	#appp.run(host='0.0.0.0', port=8080, threaded=True)

class CommonBehaviorI(RoboCompCommonBehavior.CommonBehavior):
	def __init__(self, _handler, _communicator):
		self.handler = _handler
		self.communicator = _communicator
	def getFreq(self, current = None):
		self.handler.getFreq()
	def setFreq(self, freq, current = None):
		self.handler.setFreq()
	def timeAwake(self, current = None):
		try:
			return self.handler.timeAwake()
		except:
			print 'Problem getting timeAwake'
	def killYourSelf(self, current = None):
		self.handler.killYourSelf()
	def getAttrList(self, current = None):
		try:
			return self.handler.getAttrList(self.communicator)
		except:
			print 'Problem getting getAttrList'
			traceback.print_exc()
			status = 1
			return


if __name__ == '__main__':
	app = QtCore.QCoreApplication(sys.argv)
	params = copy.deepcopy(sys.argv)
	if len(params) > 1:
		if not params[1].startswith('--Ice.Config='):
			params[1] = '--Ice.Config=' + params[1]
	elif len(params) == 1:
		params.append('--Ice.Config=config')
	ic = Ice.initialize(params)
	status = 0
	mprx = {}
	parameters = {}
	for i in ic.getProperties():
		parameters[str(i)] = str(ic.getProperties().getProperty(i))

	# Remote object connection for OpenposeServer
	try:
		proxyString = ic.getProperties().getProperty('OpenposeServerProxy')
		try:
			basePrx = ic.stringToProxy(proxyString)
			openposeserver_proxy = OpenposeServerPrx.checkedCast(basePrx)
			mprx["OpenposeServerProxy"] = openposeserver_proxy
		except Ice.Exception:
			print 'Cannot connect to the remote object (OpenposeServer)', proxyString
			#traceback.print_exc()
			status = 1
	except Ice.Exception, e:
		print e
		print 'Cannot get OpenposeServerProxy property.'
		status = 1

	if status == 0:
		worker = SpecificWorker(mprx)
		worker.setParams(parameters)
		worker.initCameraThreads();
		
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	#t = threading.Thread(target = ejecutarFlask)
	#t.start()
	time.sleep(1)#Esperamos a que los hilos de las camaras comiencen a leer
	app.exec_()
	
	if ic:
		try:
			ic.destroy()
		except:
			traceback.print_exc()
			status = 1
