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
from tkinter import *
from tkinter import ttk
from tkinter import messagebox

# Button press and combobox event handlers
# ###########################################################
def DiscoverTrackers():
    global trackerFinder
    global trackerList
    trackerFinder.Refresh
    availableTrackers = trackerFinder.Trackers
    # The trackers are listed using their IP that is used to establish a connection to it.
    # Filling the names into the list is also possible but requires a translation from the name to the IP to connect later on. So it is not shown here.
    trackerList.delete(0, 'end')
    for t in availableTrackers:
        trackerList.insert(0, t.IPAddress)
    # Adds the 'IP' to connect to a tracker simulator. Other simulators are also available according to the LMF documentation.
    trackerList.insert(0, "at960simulator")
    trackerList.insert(0, "ats600simulator")
    trackerList.insert(0, "at500simulator")
    trackerList.select_set(0)

def ConnectToSelectedTracker():
    # Connection
    global trackerList
    ipAddress = trackerList.get(trackerList.curselection()[0])
    global connectedTracker
    connectedTracker = Connection().Connect(ipAddress)
    # DRO and measurements
    connectedTracker.Targets.TargetPositionChanged += OnDroTargetPositionArrived
    connectedTracker.Measurement.MeasurementArrived += OnMeasurementArrived
    # Measurement profiles and accuracy
    global measProfileSelectionBox, currentMeasProfile
    profiles = []
    selectedMeasProfile = connectedTracker.Measurement.Profiles.Selected.Name
    index = 0
    for p in connectedTracker.Measurement.Profiles:
        profiles.append(p.Name)
        if (p.Name == selectedMeasProfile):
            selected = index
            currentMeasProfile = p.Name
        index +=1
    measProfileSelectionBox['values'] = profiles
    measProfileSelectionBox.current(selected)
    UpdateAccuracyToProfile()
    # Measurement status and preconditions
    connectedTracker.Measurement.Status.Changed += MeasStatusChanged
    connectedTracker.Measurement.Status.Preconditions.Changed += MeasPreconditionsChanged
    # Target selection
    global currentTarget
    availableTargets = []
    selectedTarget = connectedTracker.Targets.PreSelected.Name
    index = 0
    for t in connectedTracker.Targets:
        if (t.IsSelectable):
            availableTargets.append(t.Name)
            if (t.Name == selectedTarget):
                selectedIndex = index
                currentTarget = t.Name
    targetSelectionBox['values'] = availableTargets
    targetSelectionBox.current(selectedIndex)
    # OVC images
    connectedTracker.OverviewCamera.WPFBitmapImageArrived += OvcWpfBitmapImageArrived
    print("Connection successful")

def DisconnectConnectedTracker():
    global connectedTracker
    if connectedTracker != None:
        connectedTracker.Targets.TargetPositionChanged -= OnDroTargetPositionArrived
        connectedTracker.Measurement.MeasurementArrived -= OnMeasurementArrived
        # Measurement status and preconditions
        connectedTracker.Measurement.Status.Changed -= MeasStatusChanged
        connectedTracker.Measurement.Status.Preconditions.Changed -= MeasPreconditionsChanged
        connectedTracker.Disconnect()
    global measProfileSelectionBox, currentMeasProfile
    currentMeasProfile = ''
    measProfileSelectionBox['values'] = []
    # OVC images
    connectedTracker.OverviewCamera.WPFBitmapImageArrived -= OvcWpfBitmapImageArrived

def InitializeTracker():
    global connectedTracker
    if (connectedTracker != None):
        connectedTracker.Initialize()

def StartMeasurement():
    global connectedTracker
    if connectedTracker != None:
        connectedTracker.Measurement.StartMeasurement()

def StopMeasurement():
    global connectedTracker
    if connectedTracker != None:
        connectedTracker.Measurement.StopMeasurement()

def MeasureStationary():
    global connectedTracker
    if connectedTracker != None:
        try:
            statMeas = connectedTracker.Measurement.MeasureStationary()
            statMeas.Position.Coordinate1.Value
            stationaryValue1.set(str(statMeas.Position.Coordinate1.Value))
            stationaryValue2.set(str(statMeas.Position.Coordinate2.Value))
            stationaryValue3.set(str(statMeas.Position.Coordinate3.Value))
        except LmfException as ex: #LMF provides all exceptions as LmfExceptions (information for the users) with possibly other inner exceptions of other types (mostly information for the LMF development).
            messagebox.showinfo("LMF Exception", ex.ToString())
        

def UpdateAccuracyToProfile():
    global connectedTracker, accNamesTranslated
    selectedProfile = connectedTracker.Measurement.Profiles.Selected
    if (isinstance(selectedProfile, StationaryMeasurementProfile) or isinstance(selectedProfile, AreaScanProfile)):
        measProfileAccSelectionBox['values'] = accNamesTranslated
        index = selectedProfile.Accuracy.Value
        currentMeasProfileAccuracy.set(accNamesTranslated[index])
        measProfileAccSelectionBox.current(index)
    else:
        measProfileAccSelectionBox['values'] = []
        currentMeasProfileAccuracy.set('')

def MeasProfileSelectionChanged(event):
    selectedMeasProfile = measProfileSelectionBox.get()
    global connectedTracker
    for p in connectedTracker.Measurement.Profiles:
        if (p.Name == selectedMeasProfile):
            p.Select()
    UpdateAccuracyToProfile()

def MeasProfileAccSelectionChanged(event):
    selectedMeasProfileAcc = measProfileAccSelectionBox.get()
    global connectedTracker
    selectedProfile = connectedTracker.Measurement.Profiles.Selected
    if (isinstance(selectedProfile, StationaryMeasurementProfile)):
        value = int(Enum.Parse(EAccuracy, selectedMeasProfileAcc))
        selectedProfile.Accuracy.Value = value
        currentMeasProfileAccuracy.set(selectedMeasProfileAcc)

def TargetSelectionChanged(event):
    selectedTarget = targetSelectionBox.get()
    global connectedTracker
    for t in connectedTracker.Targets:
        if (t.Name == selectedTarget):
            t.Select()

def OpenOVCDialog():
    global connectedTracker
    if connectedTracker != None:
        connectedTracker.OverviewCamera.Dialog.Show()

def StartOvcImages():
    global connectedTracker
    if connectedTracker != None:
        connectedTracker.OverviewCamera.StartAsync()

def StopOvcImages():
    global connectedTracker
    if connectedTracker != None:
        connectedTracker.OverviewCamera.Stop()

# Event handlers ######################################################
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
    
def MeasStatusChanged(sender, newValue):
    global statusValue, statusNamesTranslated
    statusValue.set(statusNamesTranslated[newValue])

def MeasPreconditionsChanged(sender):
    global measPreconditions
    measPreconditions.delete(1.0, END)
    for p in sender:
        measPreconditions.insert(END, str(p.Number) + ' ' + str(p.Title) + ' ' + str(p.Description) + '\n')

def OvcWpfBitmapImageArrived(sender, image, atrCoordinates):
    global numAtrCoordinatesValue
    if atrCoordinates != None:
        numAtrCoordinatesValue.set(atrCoordinates.Count)
    else:
        numAtrCoordinatesValue.set("None")

# GUI setup ##############################################################
root = Tk()

# LMF discovery of the available trackers in the network
discoveryTitle = Label(root, text="Discovery")
discoveryTitle.grid(row=0, column=0)
discoverButton = Button(root, text = 'Discover Trackers', command = DiscoverTrackers)
discoverButton.grid(row=1, column=0)

trackerFinder = TrackerFinder()
trackerList = Listbox(root)
DiscoverTrackers()
trackerList.grid(row=1,column=0, rowspan=5)

# LMF connection and disconnection to a tracker and initialization
connectTitle = Label(root, text="Connection")
connectTitle.grid(row=0, column=1)

connectButton = Button(root, text = 'Connect to Selected Tracker', command = ConnectToSelectedTracker)
connectButton.grid(row=1,column=1)

disconnectButton = Button(root, text = 'Disconnect Tracker', command = DisconnectConnectedTracker)
disconnectButton.grid(row = 2,column = 1)

initButton = Button(root, text= 'Initialize Tracker', command = InitializeTracker)
initButton.grid(row = 3, column = 1)

# LMF DRO
droTitle = Label(root, text="DRO")
droTitle.grid(row=0, column=2)
droValue1 = StringVar()
droValue1.set('N/A')
droValue2 = StringVar()
droValue2.set('N/A')
droValue3 = StringVar()
droValue3.set('N/A')

droPos1 = Label(root, textvariable = droValue1)
droPos2 = Label(root, textvariable = droValue2)
droPos3 = Label(root, textvariable = droValue3)
droPos1.grid(row=1,column=2)
droPos2.grid(row=2,column=2)
droPos3.grid(row=3,column=2)

# LMF measurement starting / stopping
measureTitle = Label(root, text="Measurements")
measureTitle.grid(row=0, column=3)
startMeasButton = Button(root, text = 'Start Measurement', command = StartMeasurement)
startMeasButton.grid(row=1,column=3)
stopMeasButton = Button(root, text = 'Stop Measurement', command = StopMeasurement)
stopMeasButton.grid(row=2,column=3)

measStationaryButton = Button(root, text = "Measure Stationary", command = MeasureStationary)
measStationaryButton.grid(row=3, column=3)

stationaryValue1 = StringVar()
stationaryValue1.set('N/A')
stationaryValue2 = StringVar()
stationaryValue2.set('N/A')
stationaryValue3 = StringVar()
stationaryValue3.set('N/A')
stationaryPos1 = Label(root, textvariable = stationaryValue1)
stationaryPos2 = Label(root, textvariable = stationaryValue2)
stationaryPos3 = Label(root, textvariable = stationaryValue3)
stationaryPos1.grid(row=4,column=3)
stationaryPos2.grid(row=5,column=3)
stationaryPos3.grid(row=6,column=3)

# LMF profile and accuracy selection
profileTitle = Label(root, text="Measurement Profiles")
profileTitle.grid(row=0, column=4)

currentMeasProfile = StringVar()
measProfileSelectionBox = ttk.Combobox(root, textvariable=currentMeasProfile)
measProfileSelectionBox['values'] = []
measProfileSelectionBox.bind("<<ComboboxSelected>>", MeasProfileSelectionChanged)
measProfileSelectionBox.grid(row=1, column=4)

currentMeasProfileAccuracy = StringVar()
measProfileAccSelectionBox = ttk.Combobox(root, textvariable=currentMeasProfileAccuracy)
accuracyNames = Enum.GetNames(EAccuracy)
accNamesTranslated = []
for a in accuracyNames:
    accNamesTranslated.append(a)
measProfileAccSelectionBox['values'] = accNamesTranslated
measProfileAccSelectionBox.bind("<<ComboboxSelected>>", MeasProfileAccSelectionChanged)
measProfileAccSelectionBox.grid(row=2, column=4)

# LMF measurement status and preconditions
statusTitle = Label(root, text="Measurement Status and Preconditions")
statusTitle.grid(row=0, column=5)
statusNames = Enum.GetNames(EMeasurementStatus)
statusNamesTranslated = []
for s in statusNames:
    statusNamesTranslated.append(s)

statusValue = StringVar()
statusValue.set('N/A')
statusLabel = Label(root, textvariable = statusValue)
statusLabel.grid(row=1, column=5)

measPreconditions = Text(root)
measPreconditions.grid(row=2, column=5, rowspan=5)

# LMF target selection
targetTitle = Label(root, text="Target Selection")
targetTitle.grid(row=0, column=6)
currentTarget = StringVar()
targetSelectionBox = ttk.Combobox(root, textvariable=currentTarget)
targetSelectionBox['values'] = []
targetSelectionBox.bind("<<ComboboxSelected>>", TargetSelectionChanged)
targetSelectionBox.grid(row=1, column = 6)

# LMF OVC handling
ovcTitle = Label(root, text="OVC")
ovcTitle.grid(row=0, column=7)
ovcDialogButton = Button(root, text= 'Open OVC Dialog', command = OpenOVCDialog)
ovcDialogButton.grid(row = 1, column = 7)

ovcImagesStartButton = Button(root, text= 'Start OVC Images', command = StartOvcImages)
ovcImagesStartButton.grid(row = 2, column = 7)
ovcImagesStopButton = Button(root, text= 'Stop OVC Images', command = StopOvcImages)
ovcImagesStopButton.grid(row = 3, column = 7)

numAtrCoordinatesValue = StringVar()
numAtrCoordinatesValue.set('N/A')
numAtrCoordTitleLabel = Label(root, text="Num ATR Points")
numAtrCoordTitleLabel.grid(row=4, column=7)
numAtrCoordLabel = Label(root, textvariable = numAtrCoordinatesValue)
numAtrCoordLabel.grid(row=5, column=7)


# General grid configuration and start of the GUI
colCount, rowCount = root.grid_size()
for col in range(colCount):
    root.grid_columnconfigure(col, pad=10)

for row in range(rowCount):
    root.grid_rowconfigure(row, pad=5)

root.mainloop()
