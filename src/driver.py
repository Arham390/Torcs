import msgParser
import carState
import carControl
import keyboard
import csv
import time

class Driver(object):
    '''
    A driver object for the SCRC
    '''

    def __init__(self, stage):
        '''Constructor'''
        self.WARM_UP = 0
        self.QUALIFYING = 1
        self.RACE = 2
        self.UNKNOWN = 3
        self.stage = stage
        
        self.parser = msgParser.MsgParser()
        self.state = carState.CarState()
        self.control = carControl.CarControl()
        
        # Control parameters
        self.steer_step = 0.05  # Gradual steering changes
        self.max_steer = 1.0    # Maximum steering angle
        self.steer = 0.0        # Current steering value
        self.accel = 0.0
        self.brake = 0.0
        self.gear = 1

        # CSV logging setup
        self.csv_file = open('telemetry.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'curLapTime', 'speedX', 'steer', 'accel', 'brake', 'gear',
            'trackPos', 'angle', 'damage', 'rpm', 'distRaced'
        ])

    def update_controls(self):
        """Update controls based on current keyboard state"""
        # Steering
        if keyboard.is_pressed('right'):
            self.steer = max(-self.max_steer, self.steer - self.steer_step)
        elif keyboard.is_pressed('left'):
            self.steer = min(self.max_steer, self.steer + self.steer_step)
        else:
            # Gradually return to center when no input
            if abs(self.steer) > 0.01:
                self.steer *= 0.7
            else:
                self.steer = 0.0

        # Acceleration/Braking
        self.accel = 1.0 if keyboard.is_pressed('up') else 0.0
        self.brake = 1.0 if keyboard.is_pressed('down') else 0.0

        # Gear shifting (momentary press)
        if keyboard.is_pressed('w'):
            self.gear = min(6, self.gear + 1)
            time.sleep(0.1)  # Prevent rapid gear changes
        if keyboard.is_pressed('s'):
            self.gear = max(1, self.gear - 1)
            time.sleep(0.1)

    def init(self):
        '''Return init string with rangefinder angles'''
        self.angles = [0 for _ in range(19)]
        for i in range(5):
            self.angles[i] = -90 + i * 15
            self.angles[18 - i] = 90 - i * 15
        for i in range(5, 9):
            self.angles[i] = -20 + (i-5) * 5
            self.angles[18 - i] = 20 - (i-5) * 5
        return self.parser.stringify({'init': self.angles})

    def drive(self, msg):
        self.state.setFromMsg(msg)
        self.update_controls()  # Update controls before logging
        self.log_telemetry()

        # Apply controls
        self.control.setSteer(self.steer)
        self.control.setAccel(self.accel)
        self.control.setBrake(self.brake)
        self.control.setGear(self.gear)
        self.control.setClutch(0.0)
        self.control.setMeta(0)

        return self.control.toMsg()

    def log_telemetry(self):
        row = [
            self.state.getCurLapTime(),
            self.state.getSpeedX(),
            self.steer,
            self.accel,
            self.brake,
            self.gear,
            self.state.getTrackPos(),
            self.state.getAngle(),
            self.state.getDamage(),
            self.state.getRpm(),
            self.state.getDistRaced()
        ]
        self.csv_writer.writerow(row)
        self.csv_file.flush()

    def onShutDown(self):
        self.csv_file.close()

    def onRestart(self):
        pass