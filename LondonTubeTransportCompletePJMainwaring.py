# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 18:48:50 2017

@author: w1l19

This program has been made to complete the following requirements:
Map all of the stations on the London tube transport network
Allow for route directions to be given from one statino to another in the fastest time
Close stations, lines (and zones - extension) and reroute the user through the network
Present a GUI requiring minimal computational skill to operate and understand the system.

This is final copy version of the system. Luicon.ico, BannerBack.jpg and MindTheGap2.png are needed in the same folder to allow the images to be used.
No further modules are required beyond the standard ones used in Keele University.

"""


import networkx as nx  #Needed primarily to create the graph.
import matplotlib.pyplot as plt #Needed to plot the graph. This graph is then saved as a png to be displayed to the user.

import time, copy,csv, re, os, pandas as pd 
#Basic modules allowing the core functionality of the program

import tkinter
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk, Image
#All of the above are used for the GUI of the program


"""
The following global variables are split into back end and front end requirements. 
"""
#Back End
lines = {}
connections = {}
stations = {}
plannedRoute = {}

stationsDown = []
linesDown = []
zonesDown = []

linesBackUP = {}
connectionsBackUP = {}
stationsBackUP = {}

StationStart = False
StationEnd = False

#Front End
window = tkinter.Tk()

GraphSizable = 35
GraphName = "GraphMap.png"

canvasRoute = False
canvasRouteNames = None
labelRouteDirections = None
canvasTubeMapRoute = None
labelMapDirections = None
scrollbarImageWidth = None
scrollbarImageHeight = None
canvas = None
scrollbarImageHeightMainMap = None
scrollbarImageWidthMainMap = None

###This class is used to generate the map. It is used for both the main tube map and the smaller route direction map. The result is saved ready to be displayed as an image on the GUI     
class FullMap:
    def __init__(self,lineStops):
        self.map = nx.Graph()
        self._get_stations(lineStops)
        
    def _get_stations(self, lineStops):
        #add the stations to the graph
        for tube_line in lineStops.values():
            self.map.add_path(tube_line[2:],data={'line':"{0}".format(tube_line[0]),'edge_color':tube_line[1]})
    
    def _generate_edge_colours(self,current_map):
        #create the edge_colours list 
        tube_edges = current_map.edges()
        edge_colours = []
        for edge in tube_edges:
            edge_colours.append(current_map.get_edge_data(edge[0],edge[1])["data"]["edge_color"])
        return edge_colours 
       
    def create_graph_plot(self,current_map, locations):
        #generate positions for each node
        edge_colours = self._generate_edge_colours(current_map)
        #create the matplotlib figure
        plt.figure(figsize=(GraphSizable,GraphSizable))
        #draw the graph
        nx.draw_networkx_nodes(current_map,locations,node_size=100,scale=3,node_color='white')
        nx.draw_networkx_labels(current_map,locations)
        nx.draw_networkx_edges(current_map,locations,edge_color=edge_colours,width=5.0)
        #save the plotted figure
        plt.savefig(GraphName)

    def display_full_map(self,locations):
        self.create_graph_plot(self.map,locations)
####################################################################################################################################
                                                                               #Back End
####################################################################################################################################        
        
###This begins the program calling the three spreadsheets into global dictionaries, checks the data ad then Loads the GUI
def main():
    global lines, connections,stations
    lines = ExtractCSV('london.lines.csv')
    connections = ExtractCSV('london.connections.csv', True)
    stations = ExtractCSV('london.stations.csv')
    ErrorCheck()
    LoadGUI()
    
### Read the three files, using the spreadsheet headers as dictionary keys. This must be maintained for the file to process.
def ExtractCSV(filename, DualKey = False):
    headers = int
    content = {}
    reader = csv.reader(open(filename))
    for row in reader:
        if reader.line_num == 1:
            headers = row[0:]
        else:
            if DualKey == True:
                content.update({str(row[0])+"-"+str(row[1]): dict(zip(headers, row[0:]))})
            else:
                content[row[0]] = dict(zip(headers, row[0:]))
    return content

###Runs a simple check to make sure the keys for lines and stations are numbers. 
###Completes a deep copy of each file so they do not need to be re-acccessed.
def ErrorCheck():
    global lines, connections,stations
    global linesBackUP, connectionsBackUP,stationsBackUP
 
    try:
        lines = {int(re.sub("\D","",key)):value for key, value in lines.items()}
        stations = {int(re.sub("\D","",key)):value for key, value in stations.items()}

    except ValueError:
        print ("Could not convert ID to Integer, please check your files") 
        os.sys.exit()
        
    linesBackUP = copy.deepcopy(lines)
    connectionsBackUP = copy.deepcopy(connections)
    stationsBackUP = copy.deepcopy(stations)


"""
Finds all possible routes from the station selected. This is designed initially to be run from the TO listbox
so that the FROM listbox can be accurately populated. This uses Dijkstra's algorithm to plot the shortest path.
The results are kept in plannedRoute.

""" 
def RouteFind(CurrentStation):
    global plannedRoute
    unvisited = {stationID: None for stationID in stationsBackUP} #None for infinity
    plannedRoute = {stationID: {'Distance':None, 'StationList':[], 'Connections':[]} for stationID in stationsBackUP} #None for infinity
    visited = {}
    current = CurrentStation
    StationZone = 0
    StationRail = 0
    StationName = ''

    currentDistance = 0
    unvisited[current] = currentDistance
    plannedRoute[current]['Distance'] = currentDistance
    counter = 0
    while True:
        neighbour =0
        distance = 0
        counter+=1
        for stationNo, stationDetail in stations.items():
            if(stationNo == current):
                StationZone = stationDetail['zone']
                StationName = stationDetail['name']
                StationRail = stationDetail['rail']
        for key, diction in connections.items():
            if(diction['station1'] == str(current)):
                neighbour = int(diction['station2'])
                distance = int(diction['time'])
                trainLine = int(diction['line'])
            elif(diction['station2'] == str(current)):
                neighbour = int(diction['station1'])
                distance = int(diction['time'])
                trainLine = int(diction['line'])
            else: continue
            if neighbour not in unvisited: continue # next vertex
            newDistance = currentDistance + distance

            if unvisited[neighbour] is None or unvisited[neighbour] > newDistance:
                unvisited[neighbour] = newDistance
                plannedRoute[neighbour]['Distance'] = newDistance   
                plannedRoute[neighbour]['StationList'].append({'Station':current,'Line':trainLine, 'Time':distance, 'Zone' : StationZone, 'Rail' : StationRail, 'Name' : StationName, 'NewDistance':newDistance})
                plannedRoute[neighbour]['Connections'].append(key)
                                

        visited[current] = currentDistance
        del unvisited[current]
        if not unvisited: break 
        candidates = [node for node in unvisited.items() if node[1]]
        if not candidates: 
            for key, value in unvisited.items():
                visited.update({key:"Station Unreachable"})
            break
        else: current, currentDistance = sorted(candidates, key = lambda x: x[1])[0]

    for station in unvisited.keys():
        del plannedRoute[station]

    return(visited)
    
###Once the stations have been visited, the history for the destination station is recursively retrieved 
def RouteHistory(CurrentStation, Destination, DrillDownStation= None):

    global stations, connections

    if(DrillDownStation is None):
        DrillDownStation = Destination
        #Used on the first run through before DrillDownStation is populated.
    if(CurrentStation !=DrillDownStation):
        for k,i in plannedRoute.items():
            if(k == DrillDownStation):
                plannedRoute[Destination]['Connections'].append( i['Connections'][0])
                plannedRoute[Destination]['StationList'].append( i['StationList'][0])
                RouteHistory(CurrentStation,Destination, i['StationList'][0]['Station'])
    else:
        plannedRoute[Destination]['Connections'].pop(0)
        plannedRoute[Destination]['StationList'].pop(0)
        #remove inital duplicate value from lists
    return

"""
Calls the two functions above to find a station and see the path it takes to get to the destination station
"""
def RoutePlan(From, To):
    global RoutePrintDataFrame,RoutePrint,StationEnd
    RouteFind(From)
    RouteHistory(From,To)
    RoutePrint2 = {}

    if To not in plannedRoute:
        StationEnd = 'Station Unreachable'
        return
    else:
        for k,v in plannedRoute.items():
            if(int(k)==int(To)):
                for item in v['StationList']:
                    for lineNo,LineName in lines.items():
                        if(int(lineNo)==int(item['Line'])):
                            RoutePrint2.update({int(item['NewDistance']):{'1.Station':item['Name'],'2.Line':LineName['name'],'3.Zone':item['Zone'],'4.Rail':item['Rail'],'5.Time':item['Time'],'6.Total Time':item['NewDistance']}})    
    RoutePrint = {}  
    for k,v in sorted(RoutePrint2.items(),key = lambda x: x[0]):
        RoutePrint.update({k:v})
    RoutePrintDataFrame = pd.DataFrame(RoutePrint)
    RoutePrintDataFrame=RoutePrintDataFrame.T
    MakeGraph(To) #Smaller graph used to show in GUI
    print(RoutePrintDataFrame) #Used for testing purposes only
    return

"""
This function will close stations, lines and zones. 
Ver 2:  This has been amended to bypass stations instead of closing them. This means trains can pass through a closed station.
        Lines have been closed fully - this has not been changed
Ext: Zones have been added here to demonstrate flexibility in the program. 
"""    
def ServiceOutage(stationNo = None, lineNo = None, zoneNo = None):
    global linesDown, zonesDown,stationsDown #Lists of bypassed stations and lines to be closed
       
    if(stationNo in stations):
        if(stationNo not in stationsDown):
            stationsDown.append(stationNo)
        del stations[stationNo]
        connectionsTemp = copy.deepcopy(connections)
        for k, value in connectionsTemp.items():
            if value['station1'] == str(stationNo) or value['station2'] == str(stationNo):
                StationSkip(k,value,stationNo)
    
    if zoneNo:
        if(zoneNo not in zonesDown):
            zonesDown.append(zoneNo)
        for stationNumber, StationDetails in stationsBackUP.items():
            if(StationDetails['zone'] == str(zoneNo)):
                ServiceOutage(stationNumber,None,None)
           
    if(lineNo in lines):
        if(lineNo not in linesDown):
            linesDown.append(lineNo)
        if lineNo:
            lineKeys = []
            del lines[lineNo]   
            for k, value in connections.items():
                if value['line'] == str(lineNo):
                    lineKeys.append(k)
            for item in lineKeys:
                try: del connections[item]
                except KeyError: pass
"""
If stations are being bypassed, the stations connected to them need to be able to pass through the station.
For example if line A-B-C has B removed, A must continue to C
These skips are only completed during the closure of stations (and zones)
Once the skip is made the original connections are removed from the connections dictionary.
"""            
def StationSkip(ConnectKey,connection, stationClosed, Close = True):
    stationRemoval = []
    stationSkip = {}
    for connect, detail in connections.items():
        if(connect not in stationRemoval):
            if((str(stationClosed) == detail['station1'] or str(stationClosed) == detail['station2']) and detail['line'] == connection['line']):
                for connect2, detail2 in connections.items():
                    if(detail['line'] == detail2['line'] 
                    and (detail['station1'] != detail2['station1'] or detail['station2'] != detail2['station2'])  
                    and (str(stationClosed) == detail2['station1'] or str(stationClosed) == detail2['station2'])):
                        if(detail['station1']==str(stationClosed)): From = detail['station2'] 
                        else: From = detail['station1']
                        if(detail2['station1']==str(stationClosed)): To = detail2['station2'] 
                        else: To = detail2['station1']
                        newConKey = str(To+'-'+From)
                        if(Close):
                            if(To!=From and newConKey not in stationSkip):
                                stationSkip.update({newConKey:{'station1':To,'station2':From,'line':detail['line'],'time':int(detail['time'])+int(detail2['time']) }})
                            stationRemoval.append(connect)

    for newCon, NewDet in stationSkip.items():
        connections.update({newCon:NewDet})
    if not(Close):
        for connect, detail in connectionsBackUP.items():
            if(str(stationClosed) == detail['station1'] or str(stationClosed) == detail['station2']):
               connections.update({connect:detail}) 
    else:
        for item in stationRemoval:
            try: del connections[item]
            except KeyError: pass
        try: del connections[ConnectKey]
        except KeyError: pass
"""
To restore stations, lines and zones, the items are removed from the Closed lists and the deep copies are used to regenerate
the dictionaries. Any exisitng closures are then re-added. This impacts on performance but is simpler than rebuilding connections.
It ensures the graph is accurate and more robust.
"""        
def ServiceRestore(stationNo = None, lineNo = None, zoneNo = None):
    global lines, connections,stations
    global linesBackUP, connectionsBackUP,stationsBackUP
    global linesDown, zonesDown,stationsDown
    
    if (lineNo in linesDown):
        linesDown.remove(lineNo)
    if (stationNo in stationsDown):
        stationsDown.remove(stationNo)
    if (zoneNo in zonesDown):
        zonesDown.remove(zoneNo)
        result = messagebox.askyesno("You said the magic word!", "You have restored Zone "+zoneNo+".\nWould you like to restore all stations on Zone "+zoneNo+'?')
        if (result == True):
            for stationNumber, stationDetail in stationsBackUP.items():
                if(stationDetail['zone'] == str(zoneNo) and stationNumber in stationsDown):
                    stationsDown.remove(stationNumber)
                    
    lines = copy.deepcopy(linesBackUP)
    connections = copy.deepcopy(connectionsBackUP)
    stations = copy.deepcopy(stationsBackUP)
    
    for station in stationsDown:
        ServiceOutage(station, None, None)
    for line in linesDown:
        ServiceOutage(None, line, None)
    for zone in zonesDown:
        ServiceOutage(None, None, zone)    
    

#Creates the graph for the full map or the route map depending on the station number entered
def MakeGraph(StationNumberList = None):
    lineStops = {}
    locations = {}
    count = 0    
    if(StationNumberList is None):
        for l, m in lines.items():
            for t, q in connections.items():
                stationLine = []
                stationLine.append(m['name'])
                stationLine.append('#'+m['colour'])
                if(str(l) == q['line']):
                    count +=1 #unique key to add each connection
                    StationOne = ''
                    StationTwo = ''
                    for stationID, stationDetail in stations.items():
                        if (str(stationID) == q['station1']):
                            StationOne = stationDetail['name']
                        if (str(stationID) == q['station2']):
                            StationTwo = stationDetail['name']
                    stationLine.append(StationOne)
                    stationLine.append(StationTwo)
                    lineStops.update({count:stationLine})
        for no,stationD in stations.items():
            locations.update({stationD['name']:[float(stationD['latitude']), float(stationD['longitude'])]})
    else:
        for k,v in plannedRoute.items():
            if(k==int(StationNumberList)):
                for node in v['Connections']:
                    for l, m in connections.items():
                        if(l==node):
                            for lineNo,lineDetail in lines.items():
                                if(str(lineNo) == m['line']):
                                    count+=1
                                    stationLine = []
                                    stationLine.append(lineDetail['name'])
                                    stationLine.append('#'+lineDetail['colour'])
                                    for stationID, stationDetail in stations.items():
                                        if (str(stationID) == m['station1']):
                                            StationOne = stationDetail['name']
                                        if (str(stationID) == m['station2']):
                                            StationTwo = stationDetail['name']
                                    stationLine.append(StationOne)
                                    stationLine.append(StationTwo)
                                    lineStops.update({count:stationLine})

    for no,stationD in stations.items():
        locations.update({stationD['name']:[float(stationD['latitude']), float(stationD['longitude'])]})
        
    tube_map = FullMap(lineStops)
    tube_map.display_full_map(locations)      


####################################################################################################################################
                                                                               #Front End
####################################################################################################################################        
   

"""
This is the GUI for the interface, this loads the initial screen waiting for user input.
This is mostly labels added to the screen in the colour of the tube lines.
The full graph is added at the end showing the current view of the tube network.
Three images are needed for this to load - please ensure they are available in the same file as the program:
    luicon.ico - not essential
    BannerBack.JPG
    MindTheGap2.png"
"""
def LoadGUI(): 
    MakeGraph()
    global window
    window.title("London Underground Transport Network")
    window.geometry("1200x1000")
    window.configure(background="Dark Blue")
    try: window.wm_iconbitmap('luicon.ico') 
    except : print("Icon Not Found")

    photo =ImageTk.PhotoImage(Image.open("BannerBack.jpg"))
    w = tkinter.Label(window, image = photo, width = 1200, height = 300)
    w.grid(row=1, column = 0, rowspan = 3, columnspan = 10, sticky =N+S+E+W)

    global canvasLogo #Canvas to hold the Mind The Gap logo
    photo2 =Image.open("MindTheGap2.png")
    photo3 = ImageTk.PhotoImage(photo2)
    canvasLogo = tkinter.Canvas(window,background = "white")
    canvasLogo.grid(row=2, column = 3, columnspan = 4, rowspan = 2,sticky='NSEW')
    canvasLogo.create_image(215,160,image=photo3, anchor = CENTER)

    labelTitle = tkinter.Label(window, text = "LONDON UNDERGROUND TRANSPORT NETWORK")
    labelTitle.config(font = ("Gill Sans MT",30), fg='White', bg = 'Dark Blue', borderwidth = 1, highlightbackground = 'red')
    labelTitle.grid(row=0, column = 0, columnspan = 10)
    
    labelTo = tkinter.Label(window, text = "TO", width = 19)
    labelTo.configure(bg = "#00A166",font = ("Gill Sans MT",16),fg = "White")
    labelTo.grid(row=1, column = 3, sticky = NSEW,columnspan = 2)
    
    labelTo2 = tkinter.Label(window, text = "TO", width = 15)
    labelTo2.configure(bg = "#00A166",font = ("Gill Sans MT",16),fg = "White")
    labelTo2.grid(row=1, column = 3, sticky = NSEW)
    
    labelFrom = tkinter.Label(window, text = "FROM", width = 19)
    labelFrom.configure(bg = "#0A9CDA",font = ("Gill Sans MT",16),fg = "White")
    labelFrom.grid(row=1, column = 1,sticky = NSEW,columnspan = 2)
    
    labelRouteSummaryP = tkinter.Label(window, width = 19, text = "JOURNEY RESULTS")
    labelRouteSummaryP.configure(bg = "#91005A",font = ("Gill Sans MT",16),fg = "White")
    labelRouteSummaryP.grid(row=1, column = 5,sticky = NSEW)
    
    labelRouteSummary = tkinter.Label(window, width = 19, text = "JOURNEY RESULTS")
    labelRouteSummary.configure(bg = "#91005A",font = ("Gill Sans MT",16),fg = "White")
    labelRouteSummary.grid(row=1, column = 5,sticky = NSEW,  columnspan = 2)
    
    labelClosuresP = tkinter.Label(window, text = "TRANSPORT CLOSURES", width = 40)
    labelClosuresP.configure(bg = "#FBAE34",font = ("Gill Sans MT",16),fg = "Dark Blue")
    labelClosuresP.grid(row=1, column = 7,sticky = NSEW) 
    
    labelClosures = tkinter.Label(window, text = "TRANSPORT CLOSURES", width = 40)
    labelClosures.configure(bg = "#FBAE34",font = ("Gill Sans MT",16),fg = "Dark Blue")
    labelClosures.grid(row=1, column = 7,sticky = NSEW,columnspan = 2) 
    
    labelMap = tkinter.Label(window, text = "TUBE MAP")
    labelMap.configure(bg = "#F15B2E",font = ("Gill Sans MT",16),fg = "White")
    labelMap.grid(row=4, column = 1, columnspan = 8,sticky = NSEW) 

    
    RemakeBigMap(window) #Makes the map at the bottom of the screen
    StationClosureGrid(window) #Makes the closure list at the top right of the screen
    
    global listboxFrom, scrollbarFrom
    
    listboxFrom = tkinter.Listbox(window, width = 20, height = 12)
    listboxFrom.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxFrom.grid(row=2, column = 1 ,rowspan = 2, sticky = NSEW)

    sortedStations = []
    for stationNo,StationName in stations.items():
        sortedStations.append(StationName['name'])
    count= 0
    for stationListed in sorted(sortedStations):
        count+=1
        listboxFrom.insert(count,stationListed)
        
    scrollbarFrom = tkinter.Scrollbar(window, width = 15)
    scrollbarFrom.grid(row=2, column = 2,rowspan = 2,sticky=NSEW)
    listboxFrom.config(yscrollcommand=scrollbarFrom.set)
    scrollbarFrom.config(command=listboxFrom.yview)
    listboxFrom.bind('<<ListboxSelect>>', FindStations)
    
    window.mainloop()  #Runs the GUI

###If the FROM listbox is clicked, this is accessed and runs the function directly below.    
def FindStations(stationNo):
    w = stationNo.widget
    index = int(w.curselection()[0])
    value = w.get(index)
    FindStationsFrom(value)

"""
Gets the origin station and finds all available routes from this station (depending on closures)
Populates the TO list box so a destination station can be selected
"""    
def FindStationsFrom(value):
    global StationStart, StationEnd,GraphSizable,canvasLogo, listboxTo,scrollbarTo
    GraphSizable = 9
    if (canvasLogo): canvasLogo.grid_forget()
    for stationNo,StationName in stations.items():
        if(value == StationName['name']):
            StationStart = stationNo
            RouteFind(stationNo)  

    listboxTo = tkinter.Listbox(window, width = 20)
    listboxTo.grid(row=2, column = 3,rowspan = 2 ,sticky= NSEW)
    listboxTo.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
                        
                        
    sortedStations = []
    for key,route in plannedRoute.items():        
        for stationNo,StationName in stations.items():
            if(key==stationNo):
                sortedStations.append(StationName['name'])
    count= 0
    for stationListed in sorted(sortedStations):
        count+=1
        listboxTo.insert(count,stationListed)
                                       
        
    scrollbarTo = tkinter.Scrollbar(window, width = 15)
    scrollbarTo.grid(row=2, column = 4,rowspan =2,sticky= NSEW)
    listboxTo.config(yscrollcommand=scrollbarTo.set)
    scrollbarTo.config(command=listboxTo.yview)
    if(StationEnd):
        FindStationRouteProcess(StationNameRetrieve(StationEnd))
    RouteOptions(window)
    listboxTo.bind('<<ListboxSelect>>', FindStationRoute)

###If the TO listbox is clicked, this is accessed and runs the function directly below. 
def FindStationRoute(stationNo):
    w = stationNo.widget
    print(w)
    index = int(w.curselection()[0])
    value = w.get(index)
    FindStationRouteProcess(value)
    
"""
This finds a route from the origin to the destination station. 
The list of stations on the left hand side of the screen is populated here.
(Module pandastable would have been useful here but is not on the Keele network, due to this the list cannot be scrolled through
This does mean if the list gets longer then the window needs to be expanded)
The route graph is then show on the right hand side of the page using the same data.
"""    
def FindStationRouteProcess(stationName):
    global StationStart, StationEnd,GraphName,RoutePrintDataFrame, canvasRoute,RoutePrint
    global labelRouteDirections,canvasTubeMapRoute,labelMapDirections, scrollbarImageWidth, scrollbarImageHeight
    
    #Route List inserted as a graph on a canvas (NB: this is not scrollable)
    
    for stationNo,StationName in stations.items():
        if(stationName == StationName['name']):
            StationEnd = stationNo
            RoutePlan(StationStart, StationEnd)
            if (canvasRoute): canvasRoute.grid_forget()
            canvasRoute = tkinter.Canvas(window,background = "white", height = 400,scrollregion=(-100,-100,1000,1000))
            canvasRoute.grid(row=5, column = 1,columnspan = 5,rowspan = 3, sticky='NSEW')
            
            countRow = 0
            for item in RoutePrint.values():
                if(countRow ==0):
                    countColumn = 0
                    for title in item:
                        l = tkinter.Label(canvasRoute,text = title[2:])
                        l.configure(bg = "White",font = ("Gill Sans MT",16),fg = "Dark Blue")
                        l.grid(row=countRow,column=countColumn, sticky = W)
                        countColumn += 1
                    countRow += 1
                countColumn = 0
                for title in item:
                    l = tkinter.Label(canvasRoute,text =  item[title])
                    l.configure(bg = "White",fg = "Dark Blue")
                    if(countColumn>1): l.grid(row=countRow,column=countColumn)
                    else:l.grid(row=countRow,column=countColumn, sticky = W)
                    countColumn += 1
                countRow+=1

            #Tube Graph Inserted

            TubeMapRaw =Image.open(GraphName)
            Cropped = TubeMapRaw.crop((40,40,635,625))
            TubeMapRoute = ImageTk.PhotoImage(Cropped)
            window.TubeMapRoute = TubeMapRoute
            if (canvasTubeMapRoute): canvasTubeMapRoute.grid_forget()
            if (labelRouteDirections): labelRouteDirections.grid_forget()
            if (labelMapDirections): labelMapDirections.grid_forget()
            if (scrollbarImageHeight): scrollbarImageHeight.grid_forget()
            if (scrollbarImageWidth): scrollbarImageWidth.grid_forget()
            canvasTubeMapRoute = tkinter.Canvas(window,background = "white",width = 500, height = 500,scrollregion=(00,00,600,600))
            canvasTubeMapRoute.grid(row=5, column = 6, rowspan = 2,columnspan = 2, sticky='NSEW')
            canvasTubeMapRoute.create_image(0,0, anchor=NW,image=TubeMapRoute)
            
            scrollbarImageHeight = tkinter.Scrollbar(window, width = 20)
            scrollbarImageWidth = tkinter.Scrollbar(window,orient = HORIZONTAL, width = 20)
            scrollbarImageHeight.grid(row=5, column = 8, rowspan = 4,sticky=N+S+W+E)
            scrollbarImageWidth.grid(row=7, column = 6,columnspan = 2,sticky=N+W+E+S)
            canvasTubeMapRoute.config(yscrollcommand=scrollbarImageHeight.set)
            canvasTubeMapRoute.config(xscrollcommand=scrollbarImageWidth.set)
            scrollbarImageHeight.config(command=canvasTubeMapRoute.yview)
            scrollbarImageWidth.config(command=canvasTubeMapRoute.xview)
            
            labelMapDirections = tkinter.Label(window, text = "DIRECTIONS", height = 1)
            labelMapDirections.configure(bg = "#F491A8",font = ("Gill Sans MT",16),fg = "Dark Blue")
            labelMapDirections.grid(row=4, column = 6, columnspan = 3,sticky = NSEW)
            
            labelRouteDirections = tkinter.Label(window, text = "ROUTE STAGES", height = 1)
            labelRouteDirections.configure(bg = "#FFE02B",font = ("Gill Sans MT",16),fg = "Dark Blue")
            labelRouteDirections.grid(row=4, column = 1, columnspan = 5,sticky = NSEW)
            
            RouteOptions(window)#Central box updated in the GUI for TO FROM and TIME
        
"""
When the origin or destination station changes or items are removed to prevent the completion of the journey,
the central box is updated to show the user the current state of the program.
"""
def RouteOptions(window):           
    global canvasRouteNames, StationStart, StationEnd
        
    if (canvasRouteNames): canvasRouteNames.grid_forget()
    
    if (StationStart or StationEnd):
        canvasRouteNames = tkinter.Canvas(window, width = 20)
        canvasRouteNames.grid(row=2, column = 5,rowspan = 2,columnspan = 2)    
        
        if(StationStart):
            if(StationStart not in stations):
                StationStart = 'Station Unreachable'
        if(StationEnd):
            if(StationEnd not in stations):
                StationEnd = 'Station Unreachable'
        
        labelRouteFrom = tkinter.Label(canvasRouteNames, text = "FROM STATION")
        labelRouteFrom.configure(bg = "#88D0C4",font = ("Gill Sans MT",16),fg = "White")
        labelRouteFrom.grid(row=0, column = 0,sticky = NSEW) 
        if(StationStart):  
            if(str(StationStart) == 'Station Unreachable'):  
                labelRouteFromS = tkinter.Label(canvasRouteNames, text = StationStart)
            else:
                labelRouteFromS = tkinter.Label(canvasRouteNames, text = StationNameRetrieve(StationStart))
            labelRouteFromS.configure(bg = "#88D0C4",font = ("Gill Sans MT",16),fg = "White")
            labelRouteFromS.grid(row=1, column = 0,sticky = NSEW) 
    
        labelRouteTo = tkinter.Label(canvasRouteNames, text = 'TO STATION')
        labelRouteTo.configure(bg = "#AE6017",font = ("Gill Sans MT",16),fg = "White")
        labelRouteTo.grid(row=3, column = 0,sticky = NSEW) 
        if(StationEnd):
            if(str(StationEnd) == 'Station Unreachable'):
                labelRouteToS = tkinter.Label(canvasRouteNames, text = StationEnd)
            else:
                labelRouteToS = tkinter.Label(canvasRouteNames, text = StationNameRetrieve(StationEnd))
            labelRouteToS.configure(bg = "#AE6017",font = ("Gill Sans MT",16),fg = "White")
            labelRouteToS.grid(row=4, column = 0,sticky = NSEW) 
        labelRouteDist = tkinter.Label(canvasRouteNames, text = 'TIME TAKEN')
        labelRouteDist.configure(bg = "#000000",font = ("Gill Sans MT",16),fg = "White")
        labelRouteDist.grid(row=5, column = 0,sticky = NSEW) 
        if(StationStart and StationEnd):
            if(StationStart == StationEnd or (StationStart == 'Station Unreachable') or (StationEnd == 'Station Unreachable')):
                labelRouteDistance = tkinter.Label(canvasRouteNames, text = '0 MINUTES')
                labelRouteDistance.configure(bg = "#000000",font = ("Gill Sans MT",16),fg = "White")
                labelRouteDistance.grid(row=6, column = 0,sticky = NSEW) 
            else:
                for Stop, StopDetails in RoutePrint.items():
                    Distance = StopDetails['6.Total Time']
                labelRouteDistance = tkinter.Label(canvasRouteNames, text = str(Distance)+ ' MINUTES')
                labelRouteDistance.configure(bg = "#000000",font = ("Gill Sans MT",16),fg = "White")
                labelRouteDistance.grid(row=6, column = 0,sticky = NSEW) 

    if((StationStart == 'Station Unreachable') or (StationEnd == 'Station Unreachable')):
        #removes the route directions list and the graph if the station cannot be found and shows the original full map
        canvasRoute.grid_forget()
        labelRouteDirections.grid_forget()
        canvasTubeMapRoute.grid_forget()
        labelMapDirections.grid_forget()
        scrollbarImageHeight.grid_forget()
        scrollbarImageWidth.grid_forget()

"""
Makes the original 'big' map to be displayed on the bottom half of the GUI
"""
def RemakeBigMap(window):  
    global canvas,scrollbarImageHeightMainMap,scrollbarImageWidthMainMap,GraphSizable
   
    GraphSizable = 35
    MakeGraph()      
    GraphSizable = 9

    if(canvas): canvas.grid_forget()
    if(scrollbarImageHeightMainMap): scrollbarImageHeightMainMap.grid_forget()
    if(scrollbarImageWidthMainMap): scrollbarImageWidthMainMap.grid_forget()    
    
    TubeMapRaw =Image.open(GraphName)
    Cropped = TubeMapRaw.crop((400,400,2200,2200))
    TubeMap = ImageTk.PhotoImage(Cropped)   
    window.TubeMap = TubeMap
    canvas = tkinter.Canvas(window,background = "white",width = 500, height = 500,scrollregion=(-1500,-1500,1500,1500))
    canvas.grid(row=5, column = 1, columnspan = 7,sticky='NSEW')
    canvas.create_image(600,400,image=TubeMap)

    scrollbarImageHeightMainMap = tkinter.Scrollbar(window, width = 20)
    scrollbarImageWidthMainMap = tkinter.Scrollbar(window,orient = HORIZONTAL, width = 20)
    scrollbarImageHeightMainMap.grid(row=5, column = 8, rowspan = 2,sticky=N+S+W+E)
    scrollbarImageWidthMainMap.grid(row=7, column = 1, columnspan = 8,sticky=N+W+S+E)
    
    canvas.config(yscrollcommand=scrollbarImageHeightMainMap.set)
    canvas.config(xscrollcommand=scrollbarImageWidthMainMap.set)
    scrollbarImageHeightMainMap.config(command=canvas.yview)
    scrollbarImageWidthMainMap.config(command=canvas.xview) 

"""
Allows stations, lines and zones to be removed or restored to the system. 
The result is directly viewable on both graphs giving a visual representation of the current network.
"""
def StationClosureGrid(window):
    canvasService = tkinter.Canvas(window,background = "white")
    canvasService.grid(row=2, column = 7,rowspan = 2,columnspan = 2, sticky = N+E+W+S)  
        
    labelRemove = tkinter.Label(canvasService, text = 'REMOVE')
    labelRemove.configure(bg = "#00A4A7",font = ("Gill Sans MT",16),fg = "White")
    labelRemove.grid(row=0, column = 0,sticky = NSEW, columnspan = 7)

    #############REMOVE STATIONS#############
    listboxStationRemove = tkinter.Listbox(canvasService, width = 20, height = 5)
    listboxStationRemove.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxStationRemove.grid(row=1, column = 1 , sticky = NSEW)
    for stationNo,StationName in stations.items():
        listboxStationRemove.insert(stationNo,StationName['name'])
    scrollbarStatRem = tkinter.Scrollbar(canvasService, width = 15)
    scrollbarStatRem.grid(row=1, column = 2,sticky=NSEW)
    listboxStationRemove.config(yscrollcommand=scrollbarStatRem.set)
    scrollbarStatRem.config(command=listboxStationRemove.yview)
    listboxStationRemove.bind('<<ListboxSelect>>', RemoveStationsClicked)
    
    #############REMOVE lINES#############
    listboxListRemove = tkinter.Listbox(canvasService, width = 20, height = 5)
    listboxListRemove.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxListRemove.grid(row=1, column = 3 , sticky = NSEW)
    for LineNo,LineName in lines.items():
        listboxListRemove.insert(LineNo,LineName['name'])
    scrollbarListRem = tkinter.Scrollbar(canvasService, width = 15)
    scrollbarListRem.grid(row=1, column = 4,sticky=NSEW)
    listboxListRemove.config(yscrollcommand=scrollbarStatRem.set)
    scrollbarListRem.config(command=listboxListRemove.yview)
    listboxListRemove.bind('<<ListboxSelect>>', RemoveLinesClicked)

    #############REMOVE ZONES#############
    listboxZoneRemove = tkinter.Listbox(canvasService, width = 15, height = 5)
    listboxZoneRemove.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxZoneRemove.grid(row=1, column = 5 , sticky = NSEW)
    Zones = set()
    for stationNo,StationName in stations.items():
        Zones.add(StationName['zone'])
    for item in sorted(Zones, key=lambda x:float(x)):
        listboxZoneRemove.insert(stationNo,str('Zone '+item))
    scrollbarZoneRem = tkinter.Scrollbar(canvasService, width = 15)
    scrollbarZoneRem.grid(row=1, column = 6,sticky=NSEW)
    listboxZoneRemove.config(yscrollcommand=scrollbarZoneRem.set)
    scrollbarZoneRem.config(command=listboxZoneRemove.yview)
    listboxZoneRemove.bind('<<ListboxSelect>>', RemoveZonesClicked)

    labelRestore = tkinter.Label(canvasService, text = 'RESTORE')
    labelRestore.configure(bg = "#84B817",font = ("Gill Sans MT",16),fg = "White")
    labelRestore.grid(row=2, column = 0,sticky = NSEW, columnspan = 7) 
    
    global stationsDown ,linesDown ,zonesDown 

    #############RESTORE STATIONS#############
    listboxStationRestore = tkinter.Listbox(canvasService, width = 20, height = 5)
    listboxStationRestore.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxStationRestore.grid(row=3, column = 1 , sticky = NSEW)
    for stationNo in sorted(stationsDown):
        listboxStationRestore.insert(stationNo,StationNameRetrieve(stationNo))
    scrollbarStatRes = tkinter.Scrollbar(canvasService, width = 15)
    scrollbarStatRes.grid(row=3, column = 2,sticky=NSEW)
    listboxStationRestore.config(yscrollcommand=scrollbarStatRes.set)
    scrollbarStatRes.config(command=listboxStationRestore.yview)
    listboxStationRestore.bind('<<ListboxSelect>>', RestoreStationsClicked)

    #############RESTORE LINES#############
    listboxLineRestore = tkinter.Listbox(canvasService, width = 20, height = 5)
    listboxLineRestore.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxLineRestore.grid(row=3, column = 3 , sticky = NSEW)
    for lineNo in sorted(linesDown):
        listboxLineRestore.insert(lineNo,LineNameRetrieve(lineNo))
    scrollbarListRes = tkinter.Scrollbar(canvasService, width = 15)
    scrollbarListRes.grid(row=3, column = 4,sticky=NSEW)
    listboxLineRestore.config(yscrollcommand=scrollbarListRes.set)
    scrollbarListRes.config(command=listboxLineRestore.yview)
    listboxLineRestore.bind('<<ListboxSelect>>', RestoreLinesClicked)

    #############RESTORE ZONES#############
    listboxZoneRestore = tkinter.Listbox(canvasService, width = 15, height = 5)
    listboxZoneRestore.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxZoneRestore.grid(row=3, column = 5 , sticky = NSEW)
    count = 0
    for ZoneNo in sorted(zonesDown, key=lambda x:float(x)):
        count+=1
        listboxZoneRestore.insert(count,'Zone '+str(ZoneNo))
    scrollbarZoneRes = tkinter.Scrollbar(canvasService, width = 15)
    scrollbarZoneRes.grid(row=3, column = 6,sticky=NSEW)
    listboxZoneRestore.config(yscrollcommand=scrollbarZoneRes.set)
    scrollbarZoneRes.config(command=listboxZoneRestore.yview)
    listboxZoneRestore.bind('<<ListboxSelect>>', RestoreZonesClicked)   
    
    RouteOptions(window) #Update the central box to show changes

"""
The following two functions direct the removal and restoration of stations to the function directly below
"""
def RemoveStationsClicked(stationNo):
    w = stationNo.widget
    index = int(w.curselection()[0])
    value = w.get(index) 
    print('You have selected '+str(value)+' From '+str(index))
    RemoveRestoreStations(value, 'Remove')

def RestoreStationsClicked(StationNo):
    w = StationNo.widget
    index = int(w.curselection()[0])
    value = w.get(index)  
    print('You have selected '+value+' From '+str(index))
    RemoveRestoreStations(value, 'Restore')

### Removes or restores stations using the fuctions in the back-end described earlier       
def RemoveRestoreStations(value, RemRes):
    global stationsDown, StationStart, StationEnd,zonesDown
  
    for stationNo,StationName in stationsBackUP.items():
        if(value == StationName['name']):
            if(RemRes == 'Restore'):
                if(StationName['zone'] in zonesDown):
                    messagebox.showwarning("You didn't say the magic word", "I cannot restore Station "+StationName['name']+" because Zone "+StationName['zone']+" is not in service")
                ServiceRestore(stationNo, None, None)
            else:
                ServiceOutage(stationNo, None, None)
            StationClosureGrid(window)    
            if(StationStart):
                if(StationStart == stationNo or StationStart == 'Station Unreachable'):
                    StationStart = 'Station Unreachable'
                else:
                    FindStationsFrom(StationNameRetrieve(StationStart))
                    if(StationEnd):
                        if(StationEnd == stationNo or StationEnd == 'Station Unreachable'):
                            StationEnd = 'Station Unreachable'
                        else:
                            FindStationRouteProcess(StationNameRetrieve(StationEnd))
            RouteOptions(window)
    FromStationListBox(window)
   
###Updates the list of stations that can be used as origin stations    
def FromStationListBox(window):
    global listboxFrom, scrollbarFrom
    
    listboxFrom = tkinter.Listbox(window, width = 20, height = 12)
    listboxFrom.configure(bg = "#ffffff",font = ("Gill Sans MT",11),fg = "Dark Blue")
    listboxFrom.grid(row=2, column = 1 ,rowspan = 2, sticky = NSEW)
    for stationNo,StationName in stations.items():
        listboxFrom.insert(stationNo,StationName['name'])
        
    scrollbarFrom = tkinter.Scrollbar(window, width = 15)
    scrollbarFrom.grid(row=2, column = 2,rowspan = 2,sticky=NSEW)
    listboxFrom.config(yscrollcommand=scrollbarFrom.set)
    scrollbarFrom.config(command=listboxFrom.yview)
    listboxFrom.bind('<<ListboxSelect>>', FindStations)
    
    if((StationStart == 'Station Unreachable') or (StationEnd == 'Station Unreachable') or not (StationStart and StationEnd)):
        RemakeBigMap(window)
"""
The following two functions direct the removal and restoration of zones to the function directly below
"""        
def RemoveZonesClicked(ZoneNo):
    w = ZoneNo.widget
    index = int(w.curselection()[0])
    value = w.get(index)  
    print('You have selected '+str(value[5:])+' From '+str(index))
    RemoveRestoreZones(value[5:], 'Remove') #only the last few digits are needed as the text should be "'Zone '1.5"
    
def RestoreZonesClicked(ZoneNo):
    w = ZoneNo.widget
    index = int(w.curselection()[0])
    value = w.get(index)  
    print('You have selected '+str(value[5:])+' From '+str(index))
    RemoveRestoreZones(value[5:], 'Restore')

### Removes or restores zones and stations using the fuctions in the back-end described earlier   
def RemoveRestoreZones(value, RemRes):
    global stations,StationStart
    if(RemRes == 'Restore'):
        ServiceRestore(None, None, str(value))  
    else:
        for StationNumber, StationDetails in stations.items():
            if (StationStart == StationNumber and StationDetails['zone'] == value[5:]):
                if (listboxTo): listboxTo.grid_forget()
                if (scrollbarTo): scrollbarTo.grid_forget()
        ServiceOutage(None, None, str(value))    
    
    StationClosureGrid(window)         
    if(StationStart and StationStart!='Station Unreachable'):
        FindStationsFrom(StationNameRetrieve(StationStart))
    if(StationEnd and StationEnd == 'Station Unreachable'):
        FindStationsFrom(StationNameRetrieve(StationStart))              
    RouteOptions(window)    
    if((StationStart == 'Station Unreachable') or (StationEnd == 'Station Unreachable') or not (StationStart and StationEnd)):
        RemakeBigMap(window)
    FromStationListBox(window)

### Removes lines completely using the fuctions in the back-end described earlier      
def RemoveLinesClicked(lineNo):
    global lines
    w = lineNo.widget
    index = int(w.curselection()[0])
    value = w.get(index) 
    print('You have selected '+str(value)+' From '+str(index))
    for lineNo, lineName in linesBackUP.items():
        if(value == lineName['name']):
            ServiceOutage(None, lineNo, None)
            StationClosureGrid(window)    
            if(StationStart and StationStart != 'Station Unreachable'):
                FindStationsFrom(StationNameRetrieve(StationStart))
                if(StationEnd and StationEnd != 'Station Unreachable'):
                    FindStationRouteProcess(StationNameRetrieve(StationEnd))
            RouteOptions(window)
    if((StationStart == 'Station Unreachable') or (StationEnd == 'Station Unreachable') or not (StationStart and StationEnd)):
        RemakeBigMap(window)
        
### Restores lines using the fuctions in the back-end described earlier   
def RestoreLinesClicked(lineNo):
    global lines
    w = lineNo.widget
    index = int(w.curselection()[0])
    value = w.get(index) 
    print('You have selected'+str(value)+' From '+str(index))
    for lineNo, lineName in linesBackUP.items():
        if(value == lineName['name']):
            ServiceRestore(None, lineNo, None)
            StationClosureGrid(window)    
            RouteOptions(window)
    if((StationStart == 'Station Unreachable') or (StationEnd == 'Station Unreachable') or not (StationStart and StationEnd)):
        RemakeBigMap(window)

"""
The following two functions have been added to save coding time when selecting the stations and lines from the listboxes.
The back-end was made to run on unique IDs as this was seen to be quicker to index than the station and line names.
"""
def StationNameRetrieve(stationNumber):
    global stationsBackUP
    for stationNo,StationName in stationsBackUP.items():
        if(str(stationNumber) == 'Station Unreachable'): 
            return stationNumber
        elif(int(stationNumber) == stationNo): 
            return StationName['name']
def LineNameRetrieve(lineNumber):
    global linesBackUP
    for lineNo,lineName in linesBackUP.items():
        if(int(lineNumber) == lineNo):
            return lineName['name']

#How long did it take to run - used for testin purposes mainly before the implementation of the GUI
            
        
start_time = time.time()
main()
print("\n\n--- %s seconds ---" % (time.time() - start_time))