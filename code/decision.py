import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            #initialize stuck flag
            Rover.stuck = 0
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle
                print('velocity:', Rover.vel, ' is 0? ', Rover.vel == 0)
                if (Rover.steer > 10 or Rover.steer < -10) and Rover.vel == 0:
                    # Rover is stuck
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'
                    Rover.stuck = 1
                    print("inside stuck condition ", Rover.stuck)
                elif Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                if Rover.can_see_rock == 1:
                    print('distance to rock: ', np.mean(Rover.rock_dist))
                if(Rover.can_see_rock == 1 and np.mean(Rover.rock_dist) <= 200):
                    Rover.mode = 'go_to_rock'
                else:   
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if Rover.can_see_rock == 1 and Rover.near_sample == 1:
                    Rover.throttle = 0
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                elif Rover.stuck == 1 or len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # if Rover.can_see_rock == 1:
                    #     rock_angle = np.mean(Rover.rock_angles * 180/np.pi)
                    #     if rock_angle <= 90:
                    #         Rover.steer = -15
                    #     else:
                    #         Rover.steer = 15
                    # else:
                    Rover.steer = -15 
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
        elif Rover.mode == 'go_to_rock':
            if Rover.near_sample:
                Rover.mode = 'stop'
                print('STOPPING')
                print(np.mean(Rover.rock_dist))
            if(Rover.can_see_rock == 1):
                print('distance: ', np.mean(Rover.rock_dist))
            if((Rover.can_see_rock == 1) and (np.mean(Rover.rock_dist) <= 200)):
                if Rover.near_sample:
                    Rover.mode = 'stop'
                    print('STOPPING')
                    print(np.mean(Rover.rock_dist))
                else:
                    # forward logic, should be moved to a separate function
                    if len(Rover.nav_angles) >= Rover.stop_forward:  
                        # if vel is 0 then rover is stuck
                        if Rover.vel == 0:
                            Rover.throttle = 0
                            # Set brake to stored brake value
                            Rover.brake = Rover.brake_set
                            Rover.steer = 0
                            Rover.mode = 'stop'
                        # If mode is forward, navigable terrain looks good 
                        # and velocity is below max, then throttle 
                        elif Rover.vel < Rover.max_vel:
                            # Set throttle value to throttle setting
                            if(np.mean(Rover.rock_dist) <= 60):
                                Rover.throttle = 0.15
                            else:
                                Rover.throttle = Rover.throttle_set
                        else: # Else coast
                            Rover.throttle = 0
                        Rover.brake = 0
                    elif len(Rover.nav_angles) < Rover.stop_forward:
                        # Set mode to "stop" and hit the brakes!
                        Rover.throttle = 0
                        # Set brake to stored brake value
                        Rover.brake = Rover.brake_set
                        Rover.steer = 0
                        Rover.mode = 'stop'
                    #
                    rock_angle = np.mean(Rover.rock_angles * 180/np.pi)
                    Rover.steer = np.clip(rock_angle, -15, 15)
                    print('rock_angle = ', np.mean(Rover.rock_angles * 180/np.pi))
            else:
                Rover.mode = 'forward'
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover

