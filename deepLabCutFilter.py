# -*- coding: utf-8 -*-
"""
This script is for analyzing csv outputs from deeplabcut. The data are filtered
for possible errors and then an analysis of movement is performed.

Code by Luigim Vargas
May 17th, 2023
"""
import pandas as pd
import numpy as np
import tkinter
from tkinter import filedialog
import os

def openFile():
    filepath = filedialog.askopenfilename()
    return filepath

root = tkinter.Tk()
root.withdraw()
filename = filedialog.askopenfilename(parent=root)
#%%
#Import the data and change to numpy array
ofData=pd.read_csv("SampleData\\pb16_bilateralDeepCut_resnet50_laserInCabinetMar10shuffle1_1030000.csv",header=[1,2])
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

## NOTE TO SELF: Remember to solve for acute and obtuse if needed
a=np.zeros(np.shape(noseCords[:,0]))
b=np.zeros(np.shape(bodyCords[:,0]))
c=np.zeros(np.shape(tailCords[:,0]))
angle=np.zeros(np.shape(noseCords[:,0]))
for i in range(tailCords.shape[0]-1):
    a[i]=distance(noseDataFiltered[i,0],tailDataFiltered[i,0],noseDataFiltered[i,1],tailDataFiltered[i,1])
    b[i]=distance(tailDataFiltered[i,0],bodyDataFiltered[i,0],tailDataFiltered[i,1],bodyDataFiltered[i,1])
    c[i]=distance(bodyDataFiltered[i,0],noseDataFiltered[i,0],bodyDataFiltered[i,1],noseDataFiltered[i,1])
    angle[i]=np.arccos( (-a[i]**2 + b[i]**2 + c[i]**2) / (2*b[i]*c[i]) )
    #angle[i] is a coordinate in radians. To convert radians back to degrees,
    #we divide 180 by Pi and multiply the result value by radians
    angle[i]=180/np.pi*angle[i]
    
#%%  Cell for correlating with laser

import scipy.io as sio
laserStruct=sio.loadmat("SampleData\\pb16_bilateral_LaserTimes.mat")

#Create new arrays with laser times converted to frame number (at 10 frames per second)
#In this experiment, we are limiting analysis to 80 laser bouts.

laserOnTimes=np.zeros(80)
laserOffTimes=np.zeros(80)
for i in range(80):
    laserOnTimes[i]=round(laserStruct['LaserOnTimes'][i][0]*10)
    laserOffTimes[i]=round(laserStruct['LaserOffTimes'][i][0]*10)

#Extract 0.5 second windows around laser On & Off to see if there's an effect
#In these arrays, column 0 is pre-laser and column 1 is post-laser
alignedVelocityLaserOn=np.zeros((80,2),)
alignedVelocityLaserOff=np.zeros((80,2),)
#Repeat for body angle
alignedTurningLaserOn=np.zeros((80,2),)
alignedTurningLaserOff=np.zeros((80,2),)
for i in range(80):
    alignedVelocityLaserOn[i,0]=mouseVelocity[int(laserOnTimes[i]-5)]
    alignedVelocityLaserOn[i,1]=mouseVelocity[int(laserOnTimes[i]+5)]
    alignedVelocityLaserOff[i,0]=mouseVelocity[int(laserOffTimes[i]-5)]
    alignedVelocityLaserOff[i,1]=mouseVelocity[int(laserOffTimes[i]+5)]
    
    alignedTurningLaserOn[i,0]=angle[int(laserOnTimes[i]-5)]
    alignedTurningLaserOn[i,1]=angle[int(laserOnTimes[i]+5)]
    alignedTurningLaserOff[i,0]=angle[int(laserOffTimes[i]-5)]
    alignedTurningLaserOff[i,1]=angle[int(laserOffTimes[i]+5)]

#%% Graph Results

from matplotlib import pyplot as plt 

#Function for repeated plotting. turningOn will keep track of whether the data corresponds
#to the data turning On or Off to color points appropriately.
def laserPlot(alignedLaserPoints,turningOn):
    if turningOn==True:
        colorPre=[0.9,0.9,0.9]
        colorPost='g'
    else:
        colorPre='g'
        colorPost=[0.9,0.9,0.9]
    for i in range(80):
        plt.scatter(1,alignedLaserPoints[i,0],color=colorPre)
        plt.scatter(2,alignedLaserPoints[i,1],color=colorPost)
        plt.plot([1,2],[alignedLaserPoints[i,0],alignedLaserPoints[i,1]],color=[0.9,0.9,0.9])
    plt.plot([1,2],[np.mean(alignedLaserPoints[:,0]),np.mean(alignedLaserPoints[:,1])],color='k')    
    return
plt.subplot(2,2,1)
laserPlot(alignedVelocityLaserOn,True)
plt.xticks([1,2],labels=["Laser Off","Laser On"])
plt.xlim([0,3])
plt.ylabel("Velocity (AU)")
plt.title("pb16 Laser Turning On Effect on Velocity")

plt.subplot(2,2,2)
laserPlot(alignedVelocityLaserOff,False)
plt.xticks([1,2],labels=["Laser On","Laser Off"])
plt.xlim([0,3])
plt.ylabel("Velocity (AU)")
plt.title("pb16 Laser Turning Off Effect on Velocity")

plt.subplot(2,2,3)
laserPlot(alignedTurningLaserOn,True)
plt.xticks([1,2],labels=["Laser Off","Laser On"])
plt.xlim([0,3])
plt.ylabel("Body Angle (Degrees)")
plt.title("pb16 Laser Turning On Effect on Body Angle")

plt.subplot(2,2,4)
laserPlot(alignedTurningLaserOff,False)
plt.xticks([1,2],labels=["Laser On","Laser Off"])
plt.xlim([0,3])
plt.ylabel("Body Angle (Degrees)")
plt.title("pb16 Laser Turning Off Effect on Body Angle")