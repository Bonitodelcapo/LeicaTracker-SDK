from ast import main
import clr
clr.AddReference("LMF.Tracker.Connection") # Works in case the LMF.Tracker.Connection.dll is in a place where Python
                                           # looks for it (here the same folder as this file. Alternatively adding it to the Search Paths in the project also works.).
from LMF.Tracker import *
from LMF.Tracker.Measurements.Profiles import StationaryMeasurementProfile # Using some C# elements from a different namespace as imported with "import *" above require a separate import
from LMF.Tracker.Enums import EAccuracy, EMeasurementStatus
from LMF.Tracker.MeasurementResults import StationaryMeasurement3D, SingleShotMeasurement3D
from LMF.Tracker.ErrorHandling import LmfException
from System import Enum
import time



class Tracker():
    
    def __init__(self, ipaddress):
        self.Tracker = None
        self.connected = False
        self.ipaddress = ipaddress
        self.trackertype = ""
        self.selectedProfile = "Continuous Time"
        self.Targets = []
        self.droValue1 = 0.0
        self.droValue2 = 0.0
        self.droValue3 = 0.0
        self.stationaryValue1 = 0.0
        self.stationaryValue2 = 0.0
        self.stationaryValue3 = 0.0
    
    def ConnectToTracker(self):
        connection = Connection()
        self.Tracker = connection.Connect(self.ipaddress)

        # DRO and measurements
        self.Tracker.Targets.TargetPositionChanged += self.OnDroTargetPositionArrived
        self.Tracker.Measurement.MeasurementArrived += self.OnMeasurementArrived
        
        for p in self.Tracker.Measurement.Profiles:
            if (p.Name == self.selectedProfile):
                p.Select()
                break
    
    def DisconnectFromTracker(self):     
        self.Tracker.Targets.TargetPositionChanged -= self.OnDroTargetPositionArrived
        self.Tracker.Measurement.MeasurementArrived -= self.OnMeasurementArrived
        self.Tracker.Disconnect()


    def StartMeasurement(self):
        self.Tracker.Measurement.StartMeasurement()
        print("Measuring...")
            

    def StopMeasurement(self):
        self.Tracker.Measurement.StopMeasurement()
        print("..Stop!")


    def OnMeasurementArrived(self, sender, paramMeasurements, paramException):
        for m in paramMeasurements:
            position = m.Position
            self.stationaryValue1 = position.Coordinate1.Value
            self.stationaryValue2 = position.Coordinate2.Value
            self.stationaryValue3 = position.Coordinate3.Value
            print(self.stationaryValue1, self.stationaryValue2, self.stationaryValue3)

    def OnDroTargetPositionArrived(self, sender, paramPosition):
        self.droValue1 = paramPosition.Position.Coordinate1.Value
        self.droValue2 = paramPosition.Position.Coordinate2.Value
        self.droValue3 = paramPosition.Position.Coordinate3.Value
        

def main():
    Device = Tracker("at930simulator")
    Device.ConnectToTracker()

    Device.StartMeasurement()
    time.sleep(10)
    Device.StopMeasurement()

    Device.DisconnectFromTracker()


if __name__ == "__main__":
    main()


