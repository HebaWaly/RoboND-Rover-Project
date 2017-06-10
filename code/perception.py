import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

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

# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[0]).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to apply a rotation to pixel positions
def rotate_pix(xpix, ypix, yaw):
    # TODO:
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    # Apply a rotation
    xpix_rotated = xpix * np.cos(yaw_rad) - ypix * np.sin(yaw_rad)
    ypix_rotated = xpix * np.sin(yaw_rad) + ypix * np.cos(yaw_rad)
    # Return the result 
    return xpix_rotated, ypix_rotated

# Define a function to perform a translation
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # TODO:
    # Apply a scaling and a translation
    xpix_translated = np.int_(xpos + xpix_rot/scale)
    ypix_translated = np.int_(ypos + ypix_rot/scale)
    # Return the result  
    return xpix_translated, ypix_translated

# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    if (Rover.roll <= 1.5 or Rover.roll >= 358.5) and (Rover.pitch <= 1.5 or Rover.pitch >= 358.5):
        # Perform perception steps to update Rover()
        # TODO: 
        # NOTE: camera image is coming to you in Rover.img
        # 1) Define source and destination points for perspective transform
        dst_size = 5 
        # Set a bottom offset to account for the fact that the bottom of the image 
        # is not the position of the rover but a bit in front of it
        # this is just a rough guess, feel free to change it!
        bottom_offset = 6
        source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
        destination = np.float32([[Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - bottom_offset],
                          [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - bottom_offset],
                          [Rover.img.shape[1]/2 + dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset], 
                          [Rover.img.shape[1]/2 - dst_size, Rover.img.shape[0] - 2*dst_size - bottom_offset],
                          ])
        # 2) Apply perspective transform
        warped = perspect_transform(Rover.img, source, destination)
        # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
        rocks, obstacles, navig = classify_pixels(warped)
        # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        Rover.vision_image[:,:,0] = obstacles
        Rover.vision_image[:,:,1] = rocks
        Rover.vision_image[:,:,2] = navig

        # 5) Convert map image pixel values to rover-centric coords
        rock_x_rover, rock_y_rover = rover_coords(rocks)
        obstacle_x_rover, obstacle_y_rover = rover_coords(obstacles)
        navig_x_rover, navig_y_rover = rover_coords(navig)
        # 6) Convert rover-centric pixel values to world coordinates
        world_size = 200
        scale = 10
        rock_x_world, rock_y_world = pix_to_world(rock_x_rover, rock_y_rover, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, scale)
        obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_x_rover, obstacle_y_rover, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, scale)
        navig_x_world, navig_y_world = pix_to_world(navig_x_rover, navig_y_rover, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, scale)
        # 7) Update Rover worldmap (to be displayed on right side of screen)
        Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
        Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        Rover.worldmap[navig_y_world, navig_x_world, 2] += 1
        # 8) Convert rover-centric pixel positions to polar coordinates
        dist, angles = to_polar_coords(navig_x_rover, navig_y_rover)

        # update rock angles and dist if it is currently seen by the robot
        if(len(rock_x_rover) > 0):
            Rover.can_see_rock = 1
            Rover.rock_dist, Rover.rock_angles = to_polar_coords(rock_x_rover, rock_y_rover)
        else:
            Rover.can_see_rock = 0
            Rover.rock_angles = None
            Rover.rock_dist = None
        # Update Rover pixel distances and angles
        Rover.nav_dists = dist
        Rover.nav_angles = angles
    
    return Rover