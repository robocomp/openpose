
import cv2
import requests
import numpy as np
import time

camera1 = 'http://158.49.247.68:5900/mjpg/video.mjpg'
camera2 = 'http://10.253.247.102:88/cgi-bin/CGIStream.cgi?cmd=GetMJStream&usr=admin&pwd=opticalflow'
camera3 = 'http://10.253.247.108:88/cgi-bin/CGIStream.cgi?cmd=GetMJStream&usr=admin&pwd=opticalflow'
camera4 = 'http://10.253.247.179:88/cgi-bin/CGIStream.cgi?cmd=GetMJStream&usr=admin&pwd=opticalflow'
camera5 = 'http://158.49.247.240:88/cgi-bin/CGIStream.cgi?cmd=GetMJStream&usr=admin&pwd=opticalflow'


r = requests.get(camera4, stream=True)
while True:
	if(r.status_code == 200):
		bytes = bytes()
		for chunk in r.iter_content(chunk_size=1024):
			bytes += chunk
			a = bytes.find(b'\xff\xd8')
			b = bytes.find(b'\xff\xd9')
			if a != -1 and b != -1:
				jpg = bytes[a:b+2]
				bytes = bytes[b+2:]
				i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
				cv2.imshow('i', i)
				if cv2.waitKey(1) == 27:
					exit(0)		
	else:
		print("Received unexpected status code {}".format(r.status_code))
