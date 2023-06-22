# -*- coding: utf-8 -*-
"""
Script for using deepLabCut_FiltLaser to analyze groups of animals
and average across group.

We are analyzing for effects as a laser turns on (on_pre -> on_post) and for
effects as a laser turns off (off_pre -> off_post)

Currently no statistics are being taken to determine whether effect sizes are
signficantly significant. Sample data taken from open field sessions that are
not comparable (bilateral vs unilateral). For unilateral laser manipulations,
side of manipulation potentially biasing turns in one direction should not
matter because the method of measuring body angle is agnostic to which
direction the animal turns.

Make sure to define variables (fps, num events) below for your specific project

When running this code, two pop up windows will appear to prompt a file input
for each animal.The first input should be the coordinate data as a csv output
from deeplabcut. The second input is a matlab matrix. Each row of the matlab
matrix represents a distinct laser event. The first column of each row is the
time that the laser turns on & the second column is the time that the laser
turns off. 

@author: Luigim Vargas
June 8th, 2023
"""
from tkinter import filedialog
import tkinter as tk
import pandas as pd
import numpy as np
from deepLabCut_FiltLaser import deepLabCut_FiltLaser

#DEFINE VARIABLES
#Change these lines as needed
nAnimals=2
fps=10
num_events=80



dataStorage=pd.DataFrame()

vel_on_pre=list()
vel_on_post=list()
vel_off_pre=list()
vel_off_post=list()

angle_on_pre=list()
angle_on_post=list()
angle_off_pre=list()
angle_off_post=list()
for i in range(nAnimals):
    #create a window so GUI opens above IDE
    window = tk.Tk()
    window.wm_attributes('-topmost', 1)
    window.withdraw()   #close unnecessary tk window
    coordinate_path = filedialog.askopenfilename(parent = window)
    laser_path = filedialog.askopenfilename(parent = window)
    #Change line below to fit your video's fps & number of laser events
    dataStorage[i]=deepLabCut_FiltLaser(coordinate_path,laser_path,fps,num_events)
    vel_on_pre.append(dataStorage[i][1][0])
    vel_on_post.append(dataStorage[i][1][1])
    vel_off_pre.append(dataStorage[i][2][0])
    vel_off_post.append(dataStorage[i][2][1])

    angle_on_pre.append(dataStorage[i][3][0])
    angle_on_post.append(dataStorage[i][3][1])
    angle_off_pre.append(dataStorage[i][4][0])
    angle_off_post.append(dataStorage[i][4][1])


#%% Graph Results

from matplotlib import pyplot as plt 

#Function for repeated plotting. turningOn will keep track of whether the data
# corresponds to the laser turning ON or OFF to color points appropriately.
def laserPlot(pre,post,turningOn):
    if turningOn==True:
        colorPre=[0.9,0.9,0.9]
        colorPost='g'
    else:
        colorPre='g'
        colorPost=[0.9,0.9,0.9]
    for i in range(nAnimals):
        plt.scatter(1,pre[i],color=colorPre)
        plt.scatter(2,post[i],color=colorPost)
        plt.plot([1,2],[pre[i],post[i]],color=[0.9,0.9,0.9])
    plt.plot([1,2],[np.mean(pre[:]),np.mean(post[:])],color='k')    
    return

# For those on using spyder, to make pop-out window use python > preferences >
# IPython console > Graphics > Graphics backend > Backend: Automatic

plt.subplot(2,2,1)
laserPlot(vel_on_pre,vel_on_post,True)
plt.xticks([1,2],labels=["Laser Off","Laser On"])
plt.xlim([0,3])
plt.ylabel("Velocity (AU)")
plt.title([" Laser Turning On Effect on Velocity"])

plt.subplot(2,2,2)
laserPlot(vel_off_pre,vel_off_post,False)
plt.xticks([1,2],labels=["Laser On","Laser Off"])
plt.xlim([0,3])
plt.ylabel("Velocity (AU)")
plt.title([" Laser Turning Off Effect on Velocity"])

plt.subplot(2,2,3)
laserPlot(angle_on_pre,angle_on_post,True)
plt.xticks([1,2],labels=["Laser Off","Laser On"])
plt.xlim([0,3])
plt.ylabel("Body Angle (Degrees)")
plt.title([" Laser Turning On Effect on Body Angle"])

plt.subplot(2,2,4)
laserPlot(angle_off_pre,angle_off_post,False)
plt.xticks([1,2],labels=["Laser On","Laser Off"])
plt.xlim([0,3])
plt.ylabel("Body Angle (Degrees)")
plt.title([" Laser Turning Off Effect on Body Angle"])

#%% Final Table for exporting
# 1 Column for each animal. All rows correspond to the mean velocity and body 
# angles for that animal when the laser turns on or off. 
exportTable=pd.DataFrame()
for i in range(nAnimals):
    exportTable[dataStorage.loc[0][i]]=[vel_on_pre[i],vel_on_post[i],
                                        vel_off_pre[i],vel_off_post[i],
                                        angle_on_pre[i],angle_on_post[i],
                                        angle_off_pre[i],angle_off_post[i]]
    