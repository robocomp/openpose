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

# \mainpage RoboComp::openposergbdclient
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
# Just: "${PATH_TO_BINARY}/openposergbdclient --Ice.Config=${PATH_TO_CONFIG_FILE}"
#
# \subsection running_ssec Once running
#
#
#

import sys, traceback, IceStorm, subprocess, threading, time, Queue, os, copy

# Ctrl+c handling
import signal

from PySide import QtGui, QtCore

from specificworker import *


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

	# Topic Manager
	proxy = ic.getProperties().getProperty('TopicManager.Proxy')
	obj = ic.stringToProxy(proxy)
	try:
		topicManager = IceStorm.TopicManagerPrx.checkedCast(obj)
	except Ice.ConnectionRefusedException, e:
		print 'Cannot connect to IceStorm! ('+proxy+')'
		sys.exit(-1)

	# Remote object connection for RGBD
	try:
		proxyString = ic.getProperties().getProperty('RGBDProxy')
		try:
			basePrx = ic.stringToProxy(proxyString)
			rgbd_proxy = RGBDPrx.checkedCast(basePrx)
			mprx["RGBDProxy"] = rgbd_proxy
		except Ice.Exception:
			print 'Cannot connect to the remote object (RGBD)', proxyString
			#traceback.print_exc()
			status = 1
	except Ice.Exception, e:
		print e
		print 'Cannot get RGBDProxy property.'
		status = 1


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


	# Create a proxy to publish a OpenposePublishPeople topic
	topic = False
	try:
		topic = topicManager.retrieve("OpenposePublishPeople")
	except:
		pass
	while not topic:
		try:
			topic = topicManager.retrieve("OpenposePublishPeople")
		except IceStorm.NoSuchTopic:
			try:
				topic = topicManager.create("OpenposePublishPeople")
			except:
				print 'Another client created the OpenposePublishPeople topic? ...'
	pub = topic.getPublisher().ice_oneway()
	openposepublishpeopleTopic = OpenposePublishPeoplePrx.uncheckedCast(pub)
	mprx["OpenposePublishPeoplePub"] = openposepublishpeopleTopic

	if status == 0:
		worker = SpecificWorker(mprx)
		worker.setParams(parameters)

	signal.signal(signal.SIGINT, signal.SIG_DFL)
	app.exec_()

	if ic:
		try:
			ic.destroy()
		except:
			traceback.print_exc()
			status = 1
