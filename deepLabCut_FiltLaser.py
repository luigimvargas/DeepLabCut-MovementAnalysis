# -*- coding: utf-8 -*-
"""
This function is for analyzing csv outputs from deeplabcut. The data are filtered
for possible errors and then an analysis of movement is performed.

Moreover, we are using a 0.5 second window around the laser turning on and off
for our analyses here. I did this because my laser lengths are 1.5 seconds.
If your laser time is much shorter, this window might be too long. Change 
halfSecFrames as necessary to shorten or elongate the window.

INPUTS: 
    coordinate_path = path to deeplabcut csv coordinate data. 3 body positions
    are being tracked and, after the first column, each position has 3 columns
    that correspond to it (x, y, likelihood). We will not be using the
    likelihood column for filtering. Instead, we catch errors with unlikely
    distance changes.
    
    laser_path = path to matlab matrix containing the laser on/off times.
    In this case, the laser times are encoded in seconds whereas the deeplabcut 
    coordinates are encoded in frames per second. Seconds are multiplied by 
    frames per second (fps) to account for this difference. Be sure to account 
    for this step for any other situations.
    
    fps = frames per second for video (10 in sample data)
    
    num_events = number of laser on/off events for a given experiment. I 
    limited my analysis to 80 events for the sample data.
    
OUTPUTS:
    animalName = string containing the name of the subject. Name is
    extrapolated from the first characters in the laser path data.
    
    alignedVelocityLaserOn = mean velocity for the 0.5 seconds prior to the
    laser turning on for all events in column 0. In column 1, mean velocity
    after the laser turned on for all events. 
    
    alignedVelocityLaserOff = mean velocity for the 0.5 seconds prior to the
    laser turning off for all events in column 0. In column 1, mean velocity
    after the laser turned off for all events. 
    
    alignedTurningLaserOn = mean body angle for the 0.5 seconds prior to the
    laser turning on for all events in column 0. In column 1, mean body angle
    after the laser turned on for all events. 
    
    alignedTurningLaserOff = mean body angle for the 0.5 seconds prior to the
    laser turning off for all events in column 0. In column 1, mean body angle
    after the laser turned off for all events. 
    
Code by Luigim Vargas
May 17th, 2023
"""
import pandas as pd
import numpy as np
import scipy.io as sio

def deepLabCut_FiltLaser(coordinate_path,laser_path,fps,num_events):
    #Import the data and change to numpy array
    #Infer animal name from coordinate_path
    ofData=pd.read_csv(coordinate_path,header=[1,2])
    ofData=np.asarray(ofData)
    
    #%% Cell for cleaning coordinate data
    #Cut data length to 20 minutes or, at 10fps, 12000 frames
    # (Make it start at 10 seconds prior to first laser)
    noseCords=ofData[:,[1,2]]
    bodyCords=ofData[:,[4,5]]
    tailCords=ofData[:,[7,8]]
    
    #Basic distance formula we will be using repeatedly
    def distance(x1,x0,y1,y0):
        result=np.sqrt((x1-x0)**2 +(y1-y0)**2 )
        return result
    
    #First calculate the change in distance for each point's X & Y coordinate
    noseDeltas=np.zeros(np.shape(noseCords[:,0]))
    bodyDeltas=np.zeros(np.shape(bodyCords[:,0]))
    tailDeltas=np.zeros(np.shape(tailCords[:,0]))
    for i in range(noseCords.shape[0]-1):
        noseDeltas[i]=distance(noseCords[i+1,0],noseCords[i,0],noseCords[i+1,1],noseCords[i,1])
            
        bodyDeltas[i]=distance(bodyCords[i+1,0],bodyCords[i,0],bodyCords[i+1,1],bodyCords[i,1])
            
        tailDeltas[i]=distance(tailCords[i+1,0],tailCords[i,0],tailCords[i+1,1],tailCords[i,1])
    
    #Calculate the standard deviation & means of change for each coordinate
    noseDeltaMeans=np.mean(noseDeltas)
    noseDeltaSDevs=np.std(noseDeltas)
    
    bodyDeltaMeans=np.mean(bodyDeltas)
    bodyDeltaSDevs=np.std(bodyDeltas)
    
    tailDeltaMeans=np.mean(tailDeltas)
    tailDeltaSDevs=np.std(tailDeltas)
    
    #For points that change > std, set X & Y of ofData to previous point
    noseEditFlag=np.zeros(noseCords.shape)
    bodyEditFlag=np.zeros(bodyCords.shape)
    tailEditFlag=np.zeros(tailCords.shape)
    
    noseDataFiltered=noseCords
    bodyDataFiltered=bodyCords
    tailDataFiltered=tailCords
    
    for i in range(noseCords.shape[0]-1):
        if noseDeltas[i]> (noseDeltaMeans + noseDeltaSDevs*2.58):
            noseDataFiltered[i,0]=noseCords[i-1,0]
            noseDataFiltered[i,1]=noseCords[i-1,1]
            noseEditFlag[i]=1
                
        if bodyDeltas[i]> (bodyDeltaMeans + bodyDeltaSDevs*2.58):
            bodyDataFiltered[i,0]=bodyCords[i-1,0]
            bodyDataFiltered[i,1]=bodyCords[i-1,1]
            bodyEditFlag[i]=1
        
        if tailDeltas[i]> (tailDeltaMeans + tailDeltaSDevs*2.58):
            tailDataFiltered[i,0]=tailCords[i-1,0]
            tailDataFiltered[i,1]=tailCords[i-1,1]
            tailEditFlag[i]=1
            
    #%% Cell for calculating Distance, Speed, & Turning        
            
    #With data filtered, calculate distance using tailBase
    tailTotalDist=0
    for i in range(tailCords.shape[0]-1):
        tailTotalDist=tailTotalDist+distance(tailDataFiltered[i+1,0],tailDataFiltered[i,0],tailDataFiltered[i+1,1],tailDataFiltered[i,1])
    
    mouseVelocity=np.zeros(tailCords.shape[0])
    #Calculate Speed using displacement over 0.5 seconds
    #Change velocit frames as necessary if you need a smaller window to average
    
    for i in range(5,tailCords.shape[0]-1):
        mouseVelocity[i]=distance(tailDataFiltered[i,0],tailDataFiltered[i-5,0],tailDataFiltered[i,1],tailDataFiltered[i-5,1])
    
    # Calculate turning as deltas of angles between body and tail, body and nose
    
    #               / \
    #              / C \
    #             /     \     
    #            /       \
    #         b /         \ a
    #          /           \
    #         /             \
    #        /A ___________ B\
    #                c
    
    # Note on how this is calculated: The lengths between nose-body and tail-body 
    # form an isosceles triangle. The side lengths of this triangle are able to be 
    # calculated using the distance formula. To calculate an angle in an isosceles triangle
    # with known side lengths, the cosine rule is used.
    # Cosine Rule: a^2 = b^2 + c^2 - 2bc * cos(A). 
    
    # The angle I'm interested in for the mouse is angle tail->body->nose, which
    # would be the angle opposite of a line connecting the nose and tail in this
    # hypothetical triangle. Therefore, in the formula above, length a is the distance
    # between the nose and the tail. We are solving for the sides, then the angle
    # for every point in the loop below
    
    # MAJOR ADVANTAGE OF THIS METHOD:
    # Unilateral manipulation of the brain tends to cause biases toward movement in
    # one direction or the other. Because we are using distances to determine body
    # angle, the change in body angle is agnostic to the direction of turning. Therefore,
    # it makes no difference if the animal turns right or left, or if the manipulation is
    # on the right or left side. We are measuring a direction-agnostic change in body angle
    # so we don't have to group by the side the manipulation is performed on.
    a=np.zeros(np.shape(noseCords[:,0]))
    b=np.zeros(np.shape(bodyCords[:,0]))
    c=np.zeros(np.shape(tailCords[:,0]))
    angle=np.zeros(np.shape(noseCords[:,0]))
    for i in range(tailCords.shape[0]-1):
        a[i]=distance(noseDataFiltered[i,0],tailDataFiltered[i,0],noseDataFiltered[i,1],tailDataFiltered[i,1])
        b[i]=distance(tailDataFiltered[i,0],bodyDataFiltered[i,0],tailDataFiltered[i,1],bodyDataFiltered[i,1])
        c[i]=distance(bodyDataFiltered[i,0],noseDataFiltered[i,0],bodyDataFiltered[i,1],noseDataFiltered[i,1])
        # We are solving for angle A
        angle[i]=np.arccos( (-a[i]**2 + b[i]**2 + c[i]**2) / (2*b[i]*c[i]) )
        
        #angle[i] is a coordinate in radians. To convert radians back to degrees,
        #we divide 180 by Pi and multiply the result value by radians
        angle[i]=180/np.pi*angle[i]
        
    #%%  Cell for correlating with laser
    
    
    laserStruct=sio.loadmat(laser_path)
    animalName=laser_path.split('/')[-1].split('_')[0]
    #Create new arrays with laser times converted to frame number
    laserOnTimes=np.zeros(num_events)
    laserOffTimes=np.zeros(num_events)
    for i in range(num_events):
        laserOnTimes[i]=round(laserStruct['LaserOnTimes'][i][0]*fps)
        laserOffTimes[i]=round(laserStruct['LaserOffTimes'][i][0]*fps)
    
    #Extract 0.5 second windows around laser On & Off to see if there's an effect
    #In these arrays, column 0 is pre-laser and column 1 is post-laser
    alignedVelocityLaserOn=np.zeros((num_events,2),)
    alignedVelocityLaserOff=np.zeros((num_events,2),)
    #Repeat for body angle
    alignedTurningLaserOn=np.zeros((num_events,2),)
    alignedTurningLaserOff=np.zeros((num_events,2),)
    for i in range(num_events):
        alignedVelocityLaserOn[i,0]=mouseVelocity[int(laserOnTimes[i]-fps/2)]
        alignedVelocityLaserOn[i,1]=mouseVelocity[int(laserOnTimes[i]+fps/2)]
        alignedVelocityLaserOff[i,0]=mouseVelocity[int(laserOffTimes[i]-fps/2)]
        alignedVelocityLaserOff[i,1]=mouseVelocity[int(laserOffTimes[i]+fps/2)]
        
        alignedTurningLaserOn[i,0]=angle[int(laserOnTimes[i]-fps/2)]
        alignedTurningLaserOn[i,1]=angle[int(laserOnTimes[i]+fps/2)]
        alignedTurningLaserOff[i,0]=angle[int(laserOffTimes[i]-fps/2)]
        alignedTurningLaserOff[i,1]=angle[int(laserOffTimes[i]+fps/2)]
    #%% Convert all lists to means for final averaging
    alignedVelocityLaserOn=[np.mean(alignedVelocityLaserOn[:,0]),np.mean(alignedVelocityLaserOn[:,1])]
    alignedVelocityLaserOff=[np.mean(alignedVelocityLaserOff[:,0]),np.mean(alignedVelocityLaserOff[:,1])]
    alignedTurningLaserOn=[np.mean(alignedTurningLaserOn[:,0]),np.mean(alignedTurningLaserOn[:,1])]
    alignedTurningLaserOff=[np.mean(alignedTurningLaserOff[:,0]),np.mean(alignedTurningLaserOff[:,1])]
    #%%
    return([animalName,alignedVelocityLaserOn,alignedVelocityLaserOff,alignedTurningLaserOn,alignedTurningLaserOff]) 


    
