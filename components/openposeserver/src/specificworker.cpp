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
#include "specificworker.h"

/**
* \brief Default constructor
*/
SpecificWorker::SpecificWorker(MapPrx& mprx) : GenericWorker(mprx)
{
}

/**
* \brief Default destructor
*/
SpecificWorker::~SpecificWorker()
{
}

bool SpecificWorker::setParams(RoboCompCommonBehavior::ParameterList params)
{
	cola = std::make_shared<Cola>();
	openpose.setCola(cola);
	
	futur = std::async(std::launch::async, &Openpose::init, openpose);
	timer.start(Period);
	//futur.wait();
	return true;
}

void SpecificWorker::compute()
{
	//futur.wait();
}

void SpecificWorker::FPS()
{
	static uint cont = 0;
	static std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
	
	std::chrono::steady_clock::time_point end= std::chrono::steady_clock::now();
	cont++;
	//std::cout << "Time " << std::chrono::duration_cast<std::chrono::milliseconds>(end-begin).count() << " " << std::endl;
	if (std::chrono::duration_cast<std::chrono::seconds>(end - begin).count() > 5)
	{	
		std::cout << "FPS " << cont / 5  << std::endl;
		cont = 0;
		begin = std::chrono::steady_clock::now();
	}
}

////////////////////////////////////////////////////////////////////
////////////// SERVANT /////////////////////////////////////////////
////////////////////////////////////////////////////////////////////

People SpecificWorker::processImage(const RoboCompOpenposeServer::TImage &img)
{
	//std::cout << __FUNCTION__  << "new image" <<  std::endl;
	cola->copyImg(img);
	while(!cola->isReady()) { std::this_thread::sleep_for(1ms); };
	FPS();;
  	return cola->getPose();
}


