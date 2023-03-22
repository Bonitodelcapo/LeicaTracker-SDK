# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 13:07:40 2023

@author: Blumberg
"""
import clr
clr.AddReference("LMF.Tracker.Connection") # Works in case the LMF.Tracker.Connection.dll is in a place where Python
                                           # looks for it (here the same folder as this file. Alternatively adding it to the Search Paths in the project also works.).
from LMF.Tracker import *
from LMF.Tracker.Measurements.Profiles import StationaryMeasurementProfile # Using some C# elements from a different namespace as imported with "import *" above require a separate import
from LMF.Tracker.Measurements.Profiles import AreaScanProfile # Using some C# elements from a different namespace as imported with "import *" above require a separate import
from LMF.Tracker.Enums import EAccuracy, EMeasurementStatus
from LMF.Tracker.MeasurementResults import StationaryMeasurement3D, SingleShotMeasurement3D
from LMF.Tracker.ErrorHandling import LmfException
from System import Enum
import time

from LMF.Units import *

class trackerReceiver:
    def __init__(self, target='BRR 1.5in'):
        self.Target = target
        self.Simulator = 'at960simulator'
    
    def findTracker(self):
        self.trackers = []
        trackerFinder = TrackerFinder()
        trackerFinder.Refresh
        self.availableTrackers = trackerFinder.Trackers
        print('IP Addresses of found trackers:')
        for t in self.availableTrackers:
            self.trackers.append(t.IPAddress)
            print(t.IPAddress)
        
    def connectTracker(self, simulator=False, ipAddress=None):
        if simulator:
            ipAddress = self.Simulator
            self.connectedTracker = Connection().Connect(ipAddress)
            print(f'Successfully connected to: {ipAddress}')
        elif self.availableTrackers != None:
            self.connectedTracker = Connection().Connect(ipAddress)
            print(f'Successfully connected to: {ipAddress}')
            # Added by Gianluca:
            print(f'Check Model is AT960Tracker:')
            assert isinstance(self.connectedTracker , AT960Tracker)
            print("Succesfull")
        else:
            print('Use simulator or findTracker first!')
        
        # DRO and measurements
        # self.connectedTracker.Targets.TargetPositionChanged += OnDroTargetPositionArrived
        # self.connectedTracker.Measurement.MeasurementArrived += OnMeasurementArrived
        
    def disconnectTracker(self):
        if self.connectedTracker != None:
            # self.connectedTracker.Targets.TargetPositionChanged -= OnDroTargetPositionArrived
            # self.connectedTracker.Measurement.MeasurementArrived -= OnMeasurementArrived
            
            self.connectedTracker.Disconnect()
            print(f"Tracker disconnected")
            print("Nw check if connectedTracker is erroneously still available:")
            if self.connectedTracker:
                print("It is still available.\n Check if looking for targets gives an error:")
                if self.connectedTracker.Targets.Selected:
                    print(self.connectedTracker.Targets.Selected)
                    self.connectedTracker.PositionTo(True, False, 90, 0, 0)
            
    def DisconnectConnectedTracker():
        global connectedTracker
        if connectedTracker != None:
            connectedTracker.Targets.TargetPositionChanged -= OnDroTargetPositionArrived
            connectedTracker.Measurement.MeasurementArrived -= OnMeasurementArrived
            # Measurement status and preconditions
            connectedTracker.Measurement.Status.Changed -= MeasStatusChanged
            connectedTracker.Measurement.Status.Preconditions.Changed -= MeasPreconditionsChanged
            connectedTracker.Disconnect()

        # OVC images
        connectedTracker.OverviewCamera.WPFBitmapImageArrived -= OvcWpfBitmapImageArrived
            
    def initializeTracker(self):
        if self.connectedTracker != None:
            self.connectedTracker.Initialize()
            # self.TargetSelectionChanged(target=self.Target)            
            
    
    def startMeasurement(self):
        if self.connectedTracker != None:
            self.connectedTracker.Measurement.StartMeasurement()
            data = self.connectedTracker.Measurement.MeasurementArrived
            # Y = data.Position.Coordinate2.Value
            # Z = data.Position.Coordinate3.Value
            # print(f'X(mm), Y(mm), Z(mm): {X,Y,Z}')
            
    def stopMeasurement(self):
        if self.connectedTracker != None:
            self.connectedTracker.Measurement.StopMeasurement()
            
            
    def measureStationary(self):
        if self.connectedTracker != None:
            statMeas = self.connectedTracker.Measurement.MeasureStationary()
            X = statMeas.Position.Coordinate1.Value
            Y = statMeas.Position.Coordinate2.Value
            Z = statMeas.Position.Coordinate3.Value
            return X,Y,Z
    
    def changeMeasProfile(self, stat_cont='Stationary', precision='Standard'):
        #stat_cont: 'Stationary', 'Continuous Time', etc.
        #precision: 'Fast', 'Precise' or 'Standard'
        print(f"Current Measurement Profile: {self.connectedTracker.Measurement.Profiles.Selected.Name}")
        for p in self.connectedTracker.Measurement.Profiles:
            if (p.Name == stat_cont):
                p.Select()
                print(f"New Measurement Profile: {self.connectedTracker.Measurement.Profiles.Selected.Name}")
                #Gianluca added:
                break
        # Gianluca: i would change >>>if stat_cont == 'Stationary': with
        # >>>  if isinstance(selectedProfile, StationaryMeasurementProfile)
        if stat_cont == 'Stationary':
            selectedProfile = self.connectedTracker.Measurement.Profiles.Selected
            print('Precision: 0=Precise, 1=Standard, 2=Fast')
            print(f"Current Precision: {selectedProfile.Accuracy.Value}")
            value = int(Enum.Parse(EAccuracy, precision))
            selectedProfile.Accuracy.Value = value
            print(f"New Precision: {selectedProfile.Accuracy.Value}")
        
    def TargetSelectionChanged(self,target=None):
        if target != None:
            for t in self.connectedTracker.Targets:
                if (t.Name == target):
                    t.Select()
        else:
            print('Define feasible target name! Feasible Target Names are:')
            print("'BRR 1.5in'")
            print("The T-Mac target is chosen automatically upon recognition.")
        
        
    def OnMeasurementArrived(sender, paramMeasurements, paramException):
        for m in paramMeasurements:
            position = m.Position
            global stationaryValue1, stationaryValue2, stationaryValue3
            stationaryValue1.set(position.Coordinate1.Value)
            stationaryValue2.set(position.Coordinate2.Value)
            stationaryValue3.set(position.Coordinate3.Value)
            if (isinstance(m, StationaryMeasurement3D)):
                coord1 = m.Position.Coordinate1.Value
                coord2 = m.Position.Coordinate2.Value
                coord3 = m.Position.Coordinate3.Value
                precision = m.Position.Precision.Value
            elif (isinstance(m, SingleShotMeasurement3D)):
                coord1 = m.Position.Coordinate1.Value
                coord2 = m.Position.Coordinate2.Value
                coord3 = m.Position.Coordinate3.Value

    def OnDroTargetPositionArrived(sender, paramPosition):
        global droValue1, droValue2, droValue3
        droValue1.set("%.4f" % paramPosition.Position.Coordinate1.Value)
        droValue2.set("%.4f" % paramPosition.Position.Coordinate2.Value)
        droValue3.set("%.4f" % paramPosition.Position.Coordinate3.Value)

tracker = trackerReceiver()
tracker.findTracker()
tracker.connectTracker(simulator=False, ipAddress=tracker.trackers[0])
tracker.connectedTracker.Settings.CoordinateType = ECoordinateType.Spherical
tracker.connectedTracker.Settings.Units.AngleUnit = EAngleUnit.Degree
print("The inclination of the Tracker when pointing to the reflector is:\n")
print(tracker.connectedTracker.InclinationSensor.GetInclinationToGravity(), "\n\n")
print(tracker.connectedTracker.InclinationSensor.Measure(), "\n\n")
tracker.connectedTracker.PositionTo(False, False, 90, 0, 0)
# tracker.connectedTracker.PositionTo(False, False, -822.5960298057529, -1963.6193442058395, -50.0646893139661)
tracker.connectedTracker.PositionTo(False, False, 30, 20, 5000)

tracker.initializeTracker()
tracker.changeMeasProfile(stat_cont='Stationary', precision='Fast')
# print(tracker.connectedTracker.Measurement.Profiles.Selected.Name)
# tracker.startMeasurement()
# try:
#     X,Y,Z = tracker.measureStationary()
# except LmfException as ex: #LMF provides all exceptions as LmfExceptions (information for the users) with possibly other inner exceptions of other types (mostly information for the LMF development).
#     print("LMF Exception\n", ex)
"""
Throws: 
    Error# 840702
Target lost, Interferometer not locked.

Only when initializeTracker() is called.
"""
tracker.disconnectTracker()
# tracker.startMeasurement()
# print(f'X(mm), Y(mm), Z(mm): {stationaryValue1, stationaryValue2, stationaryValue3}')

    
        
    
                
        