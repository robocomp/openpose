#include "cola.h"

Cola::Cola()
{
// 	img = cv::Mat(480, 640, CV_8UC3);
// 	std::cout << img.rows << std::endl;
}

void Cola::copyImg(const RoboCompOpenposeServer::TImage &img_)
{
	//img.data = (uchar *)(&img_.image[0]);
	//std::cout << img.data.size() << std::endl;
	//memcpy(img.data, &(img_.image[0]), 640*480*3);
	
	//std::lock_guard<std::mutex> ml(mutex);
	auto d = img_.image;
	img = cv::Mat(480,640,CV_8UC3,&d[0]);
	waiting.store(true);
}

RoboCompOpenposeServer::People Cola::getPose()
{
	
	ready.store(false);
	return people;
}

bool Cola::isWaiting() const 
{
	return waiting.load();
}

bool Cola::isReady() const 
{
	return ready.load();
}

cv::Mat& Cola::getImage()
{
	waiting.store(false);
	return std::ref(img);
}

void Cola::movePeople(RoboCompOpenposeServer::People&& people_)
{
	people = std::move(people_);
	ready.store(true);
}
