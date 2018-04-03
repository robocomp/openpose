/*
 * Copyright 2018 <copyright holder> <email>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// ------------------------- OpenPose Library Tutorial - Wrapper - Example 2 - Synchronous -------------------------
// Synchronous mode: ideal for performance. The user can add his own frames producer / post-processor / consumer to the OpenPose wrapper or use the
// default ones.

// This example shows the user how to use the OpenPose wrapper class:
    // 1. User reads images
    // 2. Extract and render keypoint / heatmap / PAF of that image
    // 3. Save the results on disk
    // 4. User displays the rendered pose
    // Everything in a multi-thread scenario
// In addition to the previous OpenPose modules, we also need to use:
    // 1. `core` module:
        // For the Array<float> class that the `pose` module needs
        // For the Datum struct that the `thread` module sends between the queues
    // 2. `utilities` module: for the error & logging functions, i.e. op::error & op::log respectively
// This file should only be used for the user to take specific examples.

#ifndef OPENPOSE_H
#define OPENPOSE_H

// C++ std library dependencies
#include <chrono> // `std::chrono::` functions and classes, e.g. std::chrono::milliseconds
#include <thread> // std::this_thread
#include <iostream>
#include <gflags/gflags.h>
#include <openpose/headers.hpp>
#include <openpose/core/headers.hpp>
#include <openpose/pose/headers.hpp>
#include <openpose/utilities/headers.hpp>
#include <openpose/gui/headers.hpp>
#include <openpose/filestream/headers.hpp>

#include "cola.h"


struct UserDatum : public op::Datum
{
    bool boolThatUserNeedsForSomeReason;
    UserDatum(const bool boolThatUserNeedsForSomeReason_ = false) :
        boolThatUserNeedsForSomeReason{boolThatUserNeedsForSomeReason_}
    {};
};

// The W-classes can be implemented either as a template or as simple classes given
// that the user usually knows which kind of data he will move between the queues,
// in this case we assume a std::shared_ptr of a std::vector of UserDatum

// This worker will just read and return all the jpg files in a directory
class WUserInput : public op::WorkerProducer<std::shared_ptr<std::vector<UserDatum>>>
{
public:
    WUserInput(const std::shared_ptr<Cola> &cola_) 
    {
	  cola = cola_;
    };
    
    void initializationOnThread() 
	{
	}

    std::shared_ptr<std::vector<UserDatum>> workProducer()
    {
	  //std::cout << __FUNCTION__ << " 1 " << std::endl;
	  try	  
	  {
		auto datumsPtr = std::make_shared<std::vector<UserDatum>>();
		datumsPtr->emplace_back();
		auto& datum = datumsPtr->at(0);
		
		// Check shared queue 
		if(cola->isWaiting())
		{
			datum.cvInputData = cola->getImage();
			
			if (datum.cvInputData.empty())
				datumsPtr = nullptr;
		}
		else
 		{
 			std::this_thread::sleep_for(1ms);
 			datumsPtr = nullptr;
 		}
	
		//if (datum.cvInputData.empty())
		//	datumsPtr = nullptr;
		
		return datumsPtr;
	  } 
	  catch (const std::exception& e)
	  {
		  op::log("Some kind of unexpected error happened.");
		  this->stop();
		  op::error(e.what(), __LINE__, __FUNCTION__, __FILE__);
		  return nullptr;
	  }
    }

  private:
    const std::vector<std::string> mImageFiles;
    unsigned long long mCounter;
	cv::VideoCapture cap;
	cv::Mat frame;
	std::shared_ptr<Cola> cola;
};

class WUserPostProcessing : public op::Worker<std::shared_ptr<std::vector<UserDatum>>>
{
public:
    WUserPostProcessing()
    {
        // User's constructor here
    }

    void initializationOnThread() {}

    void work(std::shared_ptr<std::vector<UserDatum>>& datumsPtr)
    {
     	std::this_thread::sleep_for(1ms);
    }
};

// This worker will just read and return all the jpg files in a directory
class WUserOutput : public op::WorkerConsumer<std::shared_ptr<std::vector<UserDatum>>>
{
public:
	WUserOutput(const std::shared_ptr<Cola> &cola_) 
    {
	  cola = cola_;
    };
    void initializationOnThread() {}

    void workConsumer(const std::shared_ptr<std::vector<UserDatum>>& datumsPtr)
    {
        try
        {
             if (datumsPtr != nullptr && !datumsPtr->empty())
             {
				 
				const auto& poseKeypoints = datumsPtr->at(0).poseKeypoints;
				//std::cout << __FUNCTION__ << "keypoints " << poseKeypoints.getSize(1) <<  std::endl;
				RoboCompOpenposeServer::People people;  
			
				const std::string part_names[]{"nose","neck","lsh","lelbow","lwrist","rsh","relbow","rwrist","lhip","lknee","lfoot","rhip","rknee",
					"rfoot","leye","reye","lear","rear"};
					
                for (auto pers = 0 ; pers < poseKeypoints.getSize(0) ; pers++)
                {
					RoboCompOpenposeServer::Person person;  
					for (auto bodyPart = 0 ; bodyPart < poseKeypoints.getSize(1) ; bodyPart++)
                    {
						RoboCompOpenposeServer::KeyPoint kp{(int)poseKeypoints[{pers, bodyPart, 0}], (int)poseKeypoints[{pers, bodyPart, 1}], poseKeypoints[{pers, bodyPart, 2}]};
						person.body.emplace(part_names[bodyPart], kp);
                     }
					people.emplace_back(person);
                 }
                 
				cola->movePeople(std::forward<std::vector<RoboCompOpenposeServer::Person>>(people));
            }
            else
				std::this_thread::sleep_for(1ms);
        }
        catch (const std::exception& e)
        {
            op::log("Some kind of unexpected error happened.");
            this->stop();
            op::error(e.what(), __LINE__, __FUNCTION__, __FILE__);
        }
    }
private:
	std::shared_ptr<Cola> cola;
};

class Openpose
{
	public:
		void init();
		void setCola(const std::shared_ptr<Cola> &cola_)		{ cola = cola_;};
	private:
		std::shared_ptr<Cola> cola;
};
#endif // OPENPOSE_H



