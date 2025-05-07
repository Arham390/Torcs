import msgParser
import carState
import carControl
import csv
import math
import numpy as np
from datetime import datetime

class Driver(object):
    def __init__(self, stage):
        self.stage = stage
        self.parser = msgParser.MsgParser()
        self.state = carState.CarState()
        self.control = carControl.CarControl()
        self.steer_lock = 0.785398
        self.max_speed = 300  # Maximum target speed
        self.csv_filename = "telemetry_data.csv"
        self.init_csv()
        
        # Parameters for the controller
        self.prev_track_pos = 0
        self.prev_angle = 0
        self.stuck_time = 0
        self.stuck_threshold = 100  # Number of steps to consider the car stuck
        self.last_speed = 0
        self.recovery_mode = False
        
        # PID controller parameters
        self.prev_error = 0
        self.integral = 0
        self.kp = 0.7  # Proportional gain
        self.ki = 0.05  # Integral gain
        self.kd = 3.0  # Derivative gain
        
        # Target racing line (0 = center, -1 = left edge, 1 = right edge)
        self.target_pos = 0.0
        
        # Learning data
        self.track_memory = {}  # Store track segment data to learn optimal racing line
        self.learning_rate = 0.1
        
        # Track analysis
        self.track_full_data = []  # Store full track data once we complete a lap
        self.lap_completed = False
        self.prev_dist = 0
        self.track_length = 0
        
        # Race strategy
        self.overtaking = False
        self.overtake_side = 0  # -1: left, 1: right
        
        # Speed prediction for corners
        self.future_angles = []

    def init_csv(self):
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Timestamp", "SpeedX", "SpeedY", "SpeedZ",
                "TrackPos", "Angle", "Accel", "Brake", 
                "Gear", "RPM", "CurrentLapTime", "TargetSpeed",
                "SteerAngle", "TrackSensors"
            ])
    
    def log_data(self, target_speed):
        data = [
            datetime.now(),
            self.state.getSpeedX(), self.state.getSpeedY(), self.state.getSpeedZ(),
            self.state.getTrackPos(),  
            self.state.getAngle(),
            self.control.getAccel(),
            self.control.getBrake(),
            self.state.getGear(),
            self.state.getRpm(),
            self.state.getCurLapTime(),
            target_speed,
            self.control.getSteer(),
            self.state.getTrack()
        ]
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def init(self):
        """
        Initialize angles for track sensors
        Returns a string with the initialization parameters
        """
        self.angles = [0 for _ in range(19)]
        for i in range(5):
            self.angles[i] = -90 + i * 15
            self.angles[18 - i] = 90 - i * 15
        for i in range(5, 9):
            self.angles[i] = -20 + (i-5) * 5
            self.angles[18 - i] = 20 - (i-5) * 5
        return self.parser.stringify({'init': self.angles})
    
    def drive(self, msg):
        """
        Main driving function, controls the car based on sensor data
        """
        self.state.setFromMsg(msg)
        
        # Check if the car is stuck
        self.check_stuck()
        
        if self.recovery_mode:
            # Execute recovery maneuver if stuck
            self.execute_recovery()
        else:
            # Normal driving
            self.autonomous_drive()
        
        # Get current distance for lap completion detection
        curr_dist = self.state.getDistFromStart()
        if self.prev_dist > curr_dist and self.prev_dist > 100:
            # Lap completed, we've crossed the start/finish line
            self.lap_completed = True
            self.track_length = self.prev_dist
        self.prev_dist = curr_dist
        
        # Update track memory with current segment data
        self.update_track_memory()
        
        # Log telemetry data
        target_speed = self.calculate_target_speed()
        self.log_data(target_speed)
        
        # Save previous state for PID controller
        self.prev_track_pos = self.state.getTrackPos()
        self.prev_angle = self.state.getAngle()
        
        return self.control.toMsg()
    
    def autonomous_drive(self):
        """
        Main autonomous driving logic
        """
        # Get sensor data
        track_pos = self.state.getTrackPos()  # Position on track (-1 left edge, 0 center, 1 right edge)
        angle = self.state.getAngle()         # Angle between car and track axis, radians
        speed = self.state.getSpeedX()        # Speed in x-direction (forward)
        track = self.state.getTrack()         # Array of 19 range finder sensors
        opponents = self.state.getOpponents() # Array of 36 opponent sensors
        
        # Calculate steering using PID controller
        steer = self.calculate_steering(track_pos, angle, track)
        
        # Calculate target speed based on track curvature and opponent positions
        target_speed = self.calculate_target_speed()
        
        # Set acceleration and braking
        accel, brake = self.calculate_throttle_brake(speed, target_speed)
        
        # Calculate optimal gear
        gear = self.calculate_gear(speed)
        
        # Check for opponents and adjust control if needed
        steer, accel, brake = self.avoid_opponents(steer, accel, brake, opponents)
        
        # Apply control values
        self.control.setSteer(steer)
        self.control.setAccel(accel)
        self.control.setBrake(brake)
        self.control.setGear(gear)
    
    def calculate_steering(self, track_pos, angle, sensors):
        """
        Calculate steering using PID controller
        """
        # Analyze upcoming track
        self.analyze_track_ahead(sensors)
        
        # Calculate target position on track (racing line)
        target_pos = self.calculate_target_position(sensors)
        
        # Calculate error (difference between current and target position)
        error = track_pos - target_pos
        
        # PID controller
        self.integral = self.integral + error
        derivative = error - self.prev_error
        self.prev_error = error
        
        # Apply PID gains
        steer = self.kp * error + self.ki * self.integral + self.kd * derivative
        
        # Add angle compensation
        steer += angle * 1.5
        
        # Limit steering to valid range
        steer = max(-1.0, min(1.0, steer))
        
        return steer
    
    def calculate_target_position(self, sensors):
        """
        Calculate the optimal position on the track (racing line)
        Returns a value between -1 (left edge) and 1 (right edge)
        """
        # Default to center
        target = 0.0
        
        # If we have learned this track segment before, use that data
        dist = self.state.getDistFromStart()
        segment_id = int(dist / 10)  # Divide track into 10-meter segments
        
        if segment_id in self.track_memory:
            return self.track_memory[segment_id]['target_pos']
        
        # Otherwise calculate based on track curvature
        # Find the longest distance sensor reading
        max_idx = np.argmax(sensors)
        
        if max_idx < 9:
            # Track curves to the right, so move to the left
            target = -0.3
        elif max_idx > 9:
            # Track curves to the left, so move to the right
            target = 0.3
        else:
            # Straight ahead, stay in center
            target = 0.0
            
        # Adjust for upcoming corners
        if len(self.future_angles) > 0:
            avg_angle = sum(self.future_angles) / len(self.future_angles)
            # If there's a consistent curve ahead, move to the inside of the turn
            if abs(avg_angle) > 0.2:
                target = -0.5 if avg_angle > 0 else 0.5
        
        return target
    
    def analyze_track_ahead(self, sensors):
        """
        Analyze the track ahead to predict corners and adjust racing line
        """
        left_sensors = sensors[:9]
        right_sensors = sensors[10:]
        center_sensor = sensors[9]
        
        # Calculate asymmetry to detect curves
        left_avg = sum(left_sensors) / len(left_sensors)
        right_avg = sum(right_sensors) / len(right_sensors)
        
        # Positive means track curves left, negative means track curves right
        curve_direction = left_avg - right_avg
        
        # Store angles for future planning
        self.future_angles.append(curve_direction)
        if len(self.future_angles) > 10:
            self.future_angles.pop(0)
    
    def calculate_target_speed(self):
        """
        Calculate target speed based on track curvature
        """
        # Get sensors and speed
        sensors = self.state.getTrack()
        speed = self.state.getSpeedX()
        
        # Look for closest distances on left and right to estimate track width
        left_dist = min(sensors[:8]) 
        right_dist = min(sensors[11:])
        center_dist = sensors[9]
        
        # Calculate minimum sensor value excluding straight ahead
        # This helps estimate the sharpness of upcoming turns
        side_sensors = sensors[:8] + sensors[10:]
        min_dist = min(side_sensors)
        
        # Estimate curvature based on sensor asymmetry
        left_avg = sum(sensors[:8]) / 8
        right_avg = sum(sensors[10:]) / 9
        asymmetry = abs(left_avg - right_avg)
        
        # Base speed on the curvature and track conditions
        base_speed = self.max_speed
        
        # Reduce speed for curves
        if asymmetry > 30:
            # Sharp curve
            base_speed = 80
        elif asymmetry > 15:
            # Medium curve
            base_speed = 120
        elif asymmetry > 5:
            # Slight curve
            base_speed = 200
        
        # Further adjust speed based on the minimum sensor distance
        # If any obstacle is very close, reduce speed
        if min_dist < 10:
            base_speed = min(base_speed, 60)
        elif min_dist < 20:
            base_speed = min(base_speed, 100)
        
        # Adjust for track position - slow down if near edges
        track_pos = abs(self.state.getTrackPos())
        if track_pos > 0.9:
            base_speed *= 0.7  # Slow down significantly near edges
        elif track_pos > 0.7:
            base_speed *= 0.85  # Slow down moderately when getting close to edges
        
        return base_speed
    
    def calculate_throttle_brake(self, speed, target_speed):
        """
        Calculate throttle and brake values based on current and target speed
        """
        # Calculate speed error
        speed_error = target_speed - speed
        
        # Simple proportional controller
        accel = speed_error / 100
        
        # Apply limits
        accel = max(0.0, min(1.0, accel))
        
        # When target speed is lower than current speed, apply brakes
        if speed_error < -10:
            brake = -speed_error / 100
            brake = max(0.0, min(1.0, brake))
            accel = 0.0
        else:
            brake = 0.0
        
        # Safety - apply brakes if going too fast
        if speed > self.max_speed * 1.1:
            brake = 0.3
            accel = 0.0
        
        return accel, brake
    
    def calculate_gear(self, speed):
        """
        Calculate optimal gear based on speed and RPM
        """
        rpm = self.state.getRpm()
        gear = self.state.getGear()
        
        # If we're going backwards or stopped
        if gear < 0:
            return -1
        if gear == 0:
            return 1
        
        # Shift up when RPM is high
        if rpm > 8000 and gear < 6:
            gear += 1
        # Shift down when RPM is low
        elif rpm < 3000 and gear > 1:
            gear -= 1
        # Special case for first gear
        elif gear == 1 and speed < 5:
            gear = 1
        
        return gear
    
    def avoid_opponents(self, steer, accel, brake, opponents):
        """
        Adjust controls to avoid opponents
        """
        # Find the closest opponent in front
        min_dist_front = 200
        opponent_pos = 0
        
        # Front opponents (indices 0-10 and 26-36)
        front_opponents = opponents[:10] + opponents[26:]
        if min(front_opponents) < min_dist_front:
            idx = np.argmin(front_opponents)
            if idx > 10:  # Adjust index for the second slice
                idx += 16
            min_dist_front = opponents[idx]
            # Calculate relative position (-1: left, 1: right)
            opponent_pos = (idx - 18) / 18
        
        # If opponent is close in front
        if min_dist_front < 30:
            # Decide which side to overtake
            if not self.overtaking:
                # Start overtaking
                self.overtaking = True
                # Choose the side with more space
                left_space = min(opponents[15:18])
                right_space = min(opponents[19:22])
                self.overtake_side = -1 if left_space > right_space else 1
            
            # Adjust steering to move away from the opponent
            overtake_adjust = self.overtake_side * 0.3
            steer += overtake_adjust
            
            # Slightly reduce speed while overtaking
            accel *= 0.9
        else:
            # Not overtaking anymore
            self.overtaking = False
        
        # Emergency braking if opponent is very close
        if min_dist_front < 10 and min_dist_front > 0:
            brake = 0.8
            accel = 0.0
        
        return steer, accel, brake
    
    def check_stuck(self):
        """
        Check if the car is stuck
        """
        speed = self.state.getSpeedX()
        
        # If speed is very low for a number of consecutive steps
        if abs(speed) < 3:
            self.stuck_time += 1
        else:
            self.stuck_time = 0
        
        # If stuck for too long, enter recovery mode
        if self.stuck_time > self.stuck_threshold:
            self.recovery_mode = True
    
    def execute_recovery(self):
        """
        Execute recovery maneuver when car is stuck
        """
        track_pos = self.state.getTrackPos()
        
        # Set reverse gear and apply throttle
        self.control.setGear(-1)
        self.control.setAccel(0.7)
        self.control.setBrake(0.0)
        
        # Steer away from the closest edge
        if track_pos > 0:  # Right side of track
            self.control.setSteer(-1.0)  # Steer left
        else:  # Left side of track
            self.control.setSteer(1.0)   # Steer right
        
        # Exit recovery mode after some steps
        self.stuck_time -= 2
        if self.stuck_time <= 0:
            self.recovery_mode = False
            self.stuck_time = 0
    
    def update_track_memory(self):
        """
        Update memory of the track to improve racing line on next lap
        """
        dist = self.state.getDistFromStart()
        segment_id = int(dist / 10)  # 10-meter segments
        speed = self.state.getSpeedX()
        track_pos = self.state.getTrackPos()
        
        # Store or update data for this track segment
        if segment_id not in self.track_memory:
            self.track_memory[segment_id] = {
                'speeds': [speed],
                'positions': [track_pos],
                'target_pos': track_pos  # Initial target is current position
            }
        else:
            self.track_memory[segment_id]['speeds'].append(speed)
            self.track_memory[segment_id]['positions'].append(track_pos)
            
            # If we've completed a lap, update the target position
            # based on the position that yielded the highest speed
            if self.lap_completed and len(self.track_memory[segment_id]['speeds']) > 1:
                speeds = self.track_memory[segment_id]['speeds']
                positions = self.track_memory[segment_id]['positions']
                
                # Find the position that gave the highest speed
                max_speed_idx = np.argmax(speeds)
                best_pos = positions[max_speed_idx]
                
                # Update target position with learning rate
                current_target = self.track_memory[segment_id]['target_pos']
                new_target = current_target + self.learning_rate * (best_pos - current_target)
                self.track_memory[segment_id]['target_pos'] = new_target

    def onShutDown(self):
        """
        Clean up when the driver is shut down
        """
        pass

    def onRestart(self):
        """
        Reset variables on restart
        """
        self.prev_track_pos = 0
        self.prev_angle = 0
        self.stuck_time = 0
        self.recovery_mode = False
        self.prev_error = 0
        self.integral = 0
        self.track_memory = {}
        self.lap_completed = False
        self.prev_dist = 0
        self.track_length = 0
        self.overtaking = False
        self.future_angles = []