import msgParser
from msgParser import parse_server_str

class CarState(object):
    '''
    Class that hold all the car state variables
    '''

    def __init__(self):
        '''Constructor'''
        self.parser = msgParser.MsgParser()
        self.sensors = {}  # Ensure sensors is initialized as an empty dict
        self.server_string = {}  # Initialize with an empty dictionary or None if preferred
        self.angle = None
        self.curLapTime = None
        self.damage = None
        self.distFromStart = None
        self.distRaced = None
        self.focus = None
        self.fuel = None
        self.gear = None
        self.last_lap_time = None
        self.opponents = None
        self.racePos = None
        self.rpm = None
        self.speedX = None
        self.speedY = None
        self.speedZ = None
        self.track = None
        self.trackPos = None
        self.wheelSpinVel = None
        self.z = None
    
    def setFromMsg(self, str_sensors, msg=None):
        """
        Set state variables from a message string
        """
        # If msg parameter is provided, parse both
        if msg is not None:
            print(f"Parsing message: {str_sensors[:100]}...")  # Print first 100 chars
            self.sensors = self.parser.parse(str_sensors)
            self.server_string = parse_server_str(msg)
            print(f"Parsed sensors: {self.sensors}")
        else:
            # Original behavior - parse only str_sensors
            self.sensors = self.parser.parse(str_sensors)
            self.server_string = self.sensors  # Use the same dictionary for both
        
        # Process all the sensor data
        try:
            self.setAngleD()
            self.setCurLapTimeD()
            self.setDamageD()
            self.setDistFromStartD()
            self.setDistRacedD()
            self.setFocusD()
            self.setFuelD()
            self.setGearD()
            self.setLastLapTimeD()
            self.setOpponentsD()
            self.setRacePosD()
            self.setRpmD()
            self.setSpeedXD()
            self.setSpeedYD()
            self.setSpeedZD()
            self.setTrackD()
            self.setTrackPosD()
            self.setWheelSpinVelD()
            self.setZD()
        except Exception as e:
            print(f"Error processing sensors: {e}")
    
    def getFloatD(self, name):
        """
        Get a float value from sensors/server_string
        """
        try:
            # First try to get from sensors dictionary
            if name in self.sensors:
                val = self.sensors[name]
            # Then try the server_string dictionary
            elif name in self.server_string:
                val = self.server_string[name]
            else:
                print(f"Warning: {name} not found in any data source")
                return 0.0
                
            # Handle different data types
            if isinstance(val, float):
                return val
            # If val is a list or similar, take the first element
            elif hasattr(val, "__getitem__") and len(val) > 0:
                return float(val[0])
            # Otherwise, convert directly
            else:
                return float(val)
        except Exception as e:
            print(f"Error in getFloatD for {name}: {e}")
            return 0.0
    
    def getFloatListD(self, name):
        """
        Get a list of float values from sensors/server_string
        """
        try:
            # First try sensors dict
            if name in self.sensors:
                val = self.sensors[name]
            # Then try server_string dict
            elif name in self.server_string:
                val = self.server_string[name]
            else:
                print(f"Warning: {name} not found in any data source for list")
                return []
            
            # If value is already a list
            if isinstance(val, list):
                return [float(v) for v in val]
            # If single value, convert to a list with one element
            else:
                return [float(val)]
        except Exception as e:
            print(f"Error in getFloatListD for {name}: {e}")
            return []
    
    def getIntD(self, name):
        """
        Get an integer value from sensors/server_string
        """
        try:
            # First try sensors dict
            if name in self.sensors:
                val = self.sensors[name]
            # Then try server_string dict
            elif name in self.server_string:
                val = self.server_string[name]
            else:
                print(f"Warning: {name} not found in any data source for int")
                return 0

            # Handle different data types
            if isinstance(val, int):
                return val
            # If val is a list, take first element
            elif hasattr(val, "__getitem__") and len(val) > 0:
                return int(val[0])
            # Otherwise convert directly
            else:
                return int(val)
        except Exception as e:
            print(f"Error in getIntD for {name}: {e}")
            return 0
    
    # Setter methods that pull data from sensors
    def setAngleD(self):
        self.angle = self.getFloatD('angle')
    
    def setCurLapTimeD(self):
        self.curLapTime = self.getFloatD('curLapTime')
    
    def setDamageD(self):
        self.damage = self.getFloatD('damage')
    
    def setDistFromStartD(self):
        self.distFromStart = self.getFloatD('distFromStart')
    
    def setDistRacedD(self):
        self.distRaced = self.getFloatD('distRaced')
    
    def setFocusD(self):
        self.focus = self.getFloatListD('focus')
    
    def setFuelD(self):
        self.fuel = self.getFloatD('fuel')
    
    def setGearD(self):
        self.gear = self.getIntD('gear')
    
    def setLastLapTimeD(self):
        self.last_lap_time = self.getFloatD('lastLapTime')
    
    def setOpponentsD(self):
        self.opponents = self.getFloatListD('opponents')
    
    def setRacePosD(self):
        self.racePos = self.getIntD('racePos')
    
    def setRpmD(self):
        self.rpm = self.getFloatD('rpm')
    
    def setSpeedXD(self):
        self.speedX = self.getFloatD('speedX')
    
    def setSpeedYD(self):
        self.speedY = self.getFloatD('speedY')
    
    def setSpeedZD(self):
        self.speedZ = self.getFloatD('speedZ')
    
    def setTrackD(self):
        self.track = self.getFloatListD('track')
    
    def setTrackPosD(self):
        self.trackPos = self.getFloatD('trackPos')
    
    def setWheelSpinVelD(self):
        self.wheelSpinVel = self.getFloatListD('wheelSpinVel')
    
    def setZD(self):
        self.z = self.getFloatD('z')
    
    # Direct setter methods
    def setAngle(self, angle):
        self.angle = angle
    
    def setCurLapTime(self, curLapTime):
        self.curLapTime = curLapTime
    
    def setDamage(self, damage):
        self.damage = damage
    
    def setDistFromStart(self, distFromStart):
        self.distFromStart = distFromStart
    
    def setDistRaced(self, distRaced):
        self.distRaced = distRaced
    
    def setFocus(self, focus):
        self.focus = focus
    
    def setFuel(self, fuel):
        self.fuel = fuel
    
    def setGear(self, gear):
        self.gear = gear
    
    def setLastLapTime(self, last_lap_time):
        self.last_lap_time = last_lap_time
    
    def setOpponents(self, opponents):
        self.opponents = opponents
    
    def setRacePos(self, racePos):
        self.racePos = racePos
    
    def setRpm(self, rpm):
        self.rpm = rpm
    
    def setSpeedX(self, speedX):
        self.speedX = speedX
    
    def setSpeedY(self, speedY):
        self.speedY = speedY
    
    def setSpeedZ(self, speedZ):
        self.speedZ = speedZ
    
    def setTrack(self, track):
        self.track = track
    
    def setTrackPos(self, trackPos):
        self.trackPos = trackPos
    
    def setWheelSpinVel(self, wheelSpinVel):
        self.wheelSpinVel = wheelSpinVel
    
    def setZ(self, z):
        self.z = z
    
    # Getter methods
    def getAngle(self):
        return self.angle
    
    def getCurLapTime(self):
        return self.curLapTime
    
    def getDamage(self):
        return self.damage
    
    def getDistFromStart(self):
        return self.distFromStart
    
    def getDistRaced(self):
        return self.distRaced
    
    def getFocus(self):
        return self.focus
    
    def getFuel(self):
        return self.fuel
    
    def getGear(self):
        return self.gear
    
    def getLastLapTime(self):
        return self.last_lap_time
    
    def getOpponents(self):
        return self.opponents
    
    def getRacePos(self):
        return self.racePos
    
    def getRpm(self):
        return self.rpm
    
    def getSpeedX(self):
        return self.speedX
    
    def getSpeedY(self):
        return self.speedY
    
    def getSpeedZ(self):
        return self.speedZ
    
    def getTrack(self):
        return self.track
    
    def getTrackPos(self):
        return self.trackPos
    
    def getWheelSpinVel(self):
        return self.wheelSpinVel
    
    def getZ(self):
        return self.z
    
    def toMsg(self):
        """
        Convert the current state to a message string
        """
        self.sensors = {}
        
        self.sensors['angle'] = [self.angle]
        self.sensors['curLapTime'] = [self.curLapTime]
        self.sensors['damage'] = [self.damage]
        self.sensors['distFromStart'] = [self.distFromStart]
        self.sensors['distRaced'] = [self.distRaced]
        self.sensors['focus'] = self.focus
        self.sensors['fuel'] = [self.fuel]
        self.sensors['gear'] = [self.gear]
        self.sensors['lastLapTime'] = [self.last_lap_time]
        self.sensors['opponents'] = self.opponents
        self.sensors['racePos'] = [self.racePos]
        self.sensors['rpm'] = [self.rpm]
        self.sensors['speedX'] = [self.speedX]
        self.sensors['speedY'] = [self.speedY]
        self.sensors['speedZ'] = [self.speedZ]
        self.sensors['track'] = self.track
        self.sensors['trackPos'] = [self.trackPos]
        self.sensors['wheelSpinVel'] = self.wheelSpinVel
        self.sensors['z'] = [self.z]
        
        return self.parser.stringify(self.sensors)