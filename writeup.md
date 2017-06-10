## Project: Search and Sample Return
---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[rock]: ./writeup_images/rock.png
[rock_detected]: ./writeup_images/rock_detected.png
[output_video]: ./writeup_images/output_video_screenshot.png
[autonomous]: ./writeup_images/autonomous.png

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.
I've added a new function called: `classify_pixels` which classifies pixels as follows: 
1- Yellow pixels as those between the RGB values `100,100,0` and `255,255,80`
2- Obstacles are those between `0,0,0` and `1600,160,160`
3- Navigables are between `161,161,161` and `255,255,255`

![rock image][rock]
![detected rock][rock_detected]
```
def classify_pixels(img):
    low_yellow = np.array([100, 100, 0], dtype = "uint8")
    high_yellow = np.array([255, 255, 80], dtype = "uint8")
    rocks_pix = cv2.inRange(img, low_yellow, high_yellow)
    
    low_black = np.array([0, 0, 0], dtype = "uint8")
    high_black = np.array([160, 160, 160], dtype = "uint8")
    obstacles_pix = cv2.inRange(img, low_black, high_black)
    
    low_white = np.array([161, 161, 161], dtype = "uint8")
    high_white = np.array([255, 255, 255], dtype = "uint8")
    navig_pix = cv2.inRange(img, low_white, high_white)
    
    return rocks_pix, obstacles_pix, navig_pix
```

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 
```
rocks, obstacles, navig = classify_pixels(warped)
#in rover coordinates
rock_x_rover, rock_y_rover = rover_coords(rocks)
obstacle_x_rover, obstacle_y_rover = rover_coords(obstacles)
navig_x_rover, navig_y_rover = rover_coords(navig)
#in world coordinates
world_size = 200
scale = 10
rock_x_world, rock_y_world = pix_to_world(rock_x_rover, rock_y_rover, data.xpos[data.count], data.ypos[data.count], data.yaw[data.count], world_size, scale)
obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_x_rover, obstacle_y_rover, data.xpos[data.count], data.ypos[data.count], data.yaw[data.count], world_size, scale)
navig_x_world, navig_y_world = pix_to_world(navig_x_rover, navig_y_rover, data.xpos[data.count], data.ypos[data.count], data.yaw[data.count], world_size, scale)

data.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
data.worldmap[rock_y_world, rock_x_world, 1] += 1
data.worldmap[navig_y_world, navig_x_world, 2] += 1
```

![output][output_video]

### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

* perception_step():
1- It reads in the image and checks the Rover's roll and pitch, if they are smaller than 1.5 or greater than 358.5, then it will map the image input on the world map, else it will do nothing, and that's because the accuracy gets pretty low when mapping while those two angles are greater than that.
2- Applies perspective transfor to the image and then color threshold (classify pixels) to identify the objects in the environment (rocks, obstacles and navigable path)
3- After that it updates the rover image with those objects, displayed on the bottom left of the video.
4- Then it converts map image pixel values to rover-centric coordinates, and then to world coordinates.
5- It updates the world map to be displayed on the right side of the screen.
6- Calculates the polar coordinates of the navigable pixels.
7- If the rover can see any rock, it sets a `can_see_rock` flag to true and calculates the polar coordinates of the rock pixels.
* decision_step():
1-If the Rover is in `forward` mode:
  If it can see a rock, it changes to `go_to_rock` mode, if it can't see any more navigable pixels, it changes to `stop` mode, and finally if none of the above conditions happen, it keeps moving in the mean direction of the navigable pixels.
2- If the Rover is in `stop` mode:
  If the Rover is trying to stop but its velocity was still > 0.2, it keeps braking, if the Rover can see a rock and near to it, it keeps braking as well to give it a change to pick it up, if the rover is stuck or can't see enough navigable pixels, it steers by -15, finally if the Rover is stopped and can see enough navigable pixels, it changes to `forward` mode.
3- If the Rover is in `go_to_rock` mode:
  If it's near a sample, it changes to `stop` mode, if it can see a rock, less than 200 meters away, it moves towards the rock. If it can't see the rock anymore, it changes to `forward` mode.



#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

Screen resolution: 800 x 600
Graphics quality: good

Here I'll talk about the approach I took, what techniques I used, what worked and why, where the pipeline might fail and how I might improve it if I were going to pursue this project further.  

![autonomous][autonomous]

The approach I took was to set 3 modes for the Rover, either `forward` to navigate in the direction of the mean of the navigable angles, or `go_to_rock` if the rock is seen by the Rover and it's at least 120 meters away, or `stop` to pickup the rocks or to change direction when the Rover gets stuck.

I've also limited the mapping of the world and images analysis to be only when the pitch and roll anagles are very close to zero, in order to keep the fidelity >= 60

The Rover sometimes gets stuck, which is something I could work on more later, by checking out the time during which the Rover was in either `forward` or `go_to_rock` mode while its speed is zero, and this is a good measure to assume the robot is stuck and switch to `stop` mode, then it will be able to rotate and resume moving.

Crowling the walls was a good idea to help the Rover pickup all the rocks, I'd give it a try as well if I were to pursue the project further
