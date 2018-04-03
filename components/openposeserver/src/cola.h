/*
 *    Copyright (C)2018 by YOUR NAME HERE
 *
 *    This file is part of RoboComp
 *
 *    RoboComp is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    RoboComp is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
 */

/**
       \brief
       @author authorname
*/

#ifndef COLA_H
#define COLA_H

#include "genericworker.h"
#include <mutex>
#include <atomic>
#include <chrono>
#include <iostream>
#include <thread>
#include <ctime>
#include <opencv2/core/core.hpp>

class Cola
{
	public:
		Cola();
		void copyImg(const RoboCompOpenposeServer::TImage &img_);
		RoboCompOpenposeServer::People getPose();
		bool isWaiting() const ;
		bool isReady() const;
		cv::Mat& getImage();
		void movePeople(RoboCompOpenposeServer::People&& people_);

	private:
		cv::Mat img;
		RoboCompOpenposeServer::People people;
		std::atomic<bool> waiting{false};
		std::atomic<bool> ready{false};
		mutable std::mutex mutex;
};

#endif
