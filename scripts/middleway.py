#!/usr/bin/env python

import rospy
from std_msgs.msg import Float64, Int16, String, Bool
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import NavSatFix, TimeReference
import traceback
import os
import sys
import time
import requests
import time
import bisect
import numpy as np
import pandas as pd
# import shapely
# from shapely import LineString,Point
# from shapely.ops import nearest_points
# from shapely import Polygon
import json

velocity_topic = "/car/state/vel_x"
sport_mode_topic = "car/state/sport_mode"
eco_mode_topic = "car/state/eco_mode"
# gantry_topic = "/vsl/latest_gantry"
vsl_set_speed_topic = "/vsl/set_speed"
distance_lines_topic="/acc/set_distance"

radar0_topic = "/car/radar/track_a0"
radar1_topic = "/car/radar/track_a1"
radar2_topic = "/car/radar/track_a2"
radar3_topic = "/car/radar/track_a3"
radar4_topic = "/car/radar/track_a4"
radar5_topic = "/car/radar/track_a5"
radar6_topic = "/car/radar/track_a6"
radar7_topic = "/car/radar/track_a7"

radar8_topic = "/car/radar/track_a8"
radar9_topic = "/car/radar/track_a9"
radar10_topic = "/car/radar/track_a10"
radar11_topic = "/car/radar/track_a11"
radar12_topic = "/car/radar/track_a12"
radar13_topic = "/car/radar/track_a13"
radar14_topic = "/car/radar/track_a14"
radar15_topic = "/car/radar/track_a15"

# gantry = None
vsl_set_speed = None
social_limit_v = 0
base_social_limit = 2
distance_lines = 0
max_speed = 32 ##32 m/s is 71.6 mph
velocity = None
radar0,radar1,radar2,radar3,radar4,radar5,radar6,radar7 = None,None,None,None,None,None,None,None
radar8,radar9,radar10,radar11,radar12,radar13,radar14,radar15 = None,None,None,None,None,None,None,None
radar_state = [[],[],[],[]]#nested list, x, y, relv,time
sport_mode=0
eco_mode=0
normal=0

def sport_mode_callback(data):
    global sport_mode
    sport_mode=data.data

def eco_mode_callback(data):
    global eco_mode
    eco_mode=data.data

def gantry_callback(data):
    global gantry
    gantry = data.data

def velocity_callback(data):
    global velocity
    velocity = data.data

def vsl_set_speed_callback(data):
    global vsl_set_speed
    vsl_set_speed = data.data

def distance_lines_callback(data):
    global distance_lines
    # global base_social_limit
    # global social_limit_v
    distance_lines = data.data
    # if distance_lines >0:
    #     social_limit_v = base_social_limit*distance_lines
    # else:
    #     social_limit_v = base_social_limit #the acc system is not on
    # # print('Social limit is: ',social_limit_v)

def radar0_callback(data):
    global radar0
    radar0 = data.point
    timeradar0 = data.header.stamp.secs
    addRadarPoint(radar0,timeradar0)
def radar1_callback(data):
    global radar1
    radar1 = data.point
    timeradar1 = data.header.stamp.secs
    addRadarPoint(radar1,timeradar1)
def radar2_callback(data):
    global radar2
    radar2 = data.point
    timeradar2 = data.header.stamp.secs
    addRadarPoint(radar2,timeradar2)
def radar3_callback(data):
    global radar3
    radar3 = data.point
    timeradar3 = data.header.stamp.secs
    addRadarPoint(radar3,timeradar3)
def radar4_callback(data):
    global radar4
    radar4 = data.point
    timeradar4 = data.header.stamp.secs
    addRadarPoint(radar4,timeradar4)
def radar5_callback(data):
    global radar5
    radar5 = data.point
    timeradar5 = data.header.stamp.secs
    addRadarPoint(radar5,timeradar5)
def radar6_callback(data):
    global radar6
    radar6 = data.point
    timeradar6 = data.header.stamp.secs
    addRadarPoint(radar6,timeradar6)
def radar7_callback(data):
    global radar7
    radar7 = data.point
    timeradar7 = data.header.stamp.secs
    addRadarPoint(radar7,timeradar7)

def radar8_callback(data):
    global radar8
    radar8 = data.point
    timeradar8 = data.header.stamp.secs
    addRadarPoint(radar8,timeradar8)
def radar9_callback(data):
    global radar9
    radar9 = data.point
    timeradar9 = data.header.stamp.secs
    addRadarPoint(radar9,timeradar9)
def radar10_callback(data):
    global radar10
    radar10 = data.point
    timeradar10 = data.header.stamp.secs
    addRadarPoint(radar10,timeradar10)
def radar11_callback(data):
    global radar11
    radar11 = data.point
    timeradar11 = data.header.stamp.secs
    addRadarPoint(radar11,timeradar11)
def radar12_callback(data):
    global radar12
    radar12 = data.point
    timeradar12 = data.header.stamp.secs
    addRadarPoint(radar12,timeradar12)
def radar13_callback(data):
    global radar13
    radar13 = data.point
    timeradar13 = data.header.stamp.secs
    addRadarPoint(radar13,timeradar13)
def radar14_callback(data):
    global radar14
    radar14 = data.point
    timeradar14 = data.header.stamp.secs
    addRadarPoint(radar14,timeradar14)
def radar15_callback(data):
    global radar15
    radar15 = data.point
    timeradar15 = data.header.stamp.secs
    addRadarPoint(radar15,timeradar15)

def addRadarPoint(point,t):
    """adding a point to the state of the radar system"""
    global radar_state
    global velocity
    if point.z > 0:
        radar_state[0].append(point.x)#longitude distance
        radar_state[1].append(point.y)#lateral distance
        radar_state[2].append(point.z + velocity)#relative velocity_topic
        radar_state[3].append(time.time())#time stamp second
        # print('added point: ',point.z+velocity, 'length',len(radar_state[2]))
    # while len(radar_state[0]) >= 1600: #5 second history of 16 tracks at 20 hz
    #     radar_state[0].pop(0) #pop the oldest stuff
    #     radar_state[1].pop(0)
    #     radar_state[2].pop(0)
    recursivePop()

def recursivePop():
    global radar_state
    if len(radar_state[3]) !=0:
        oldest_time = radar_state[3].pop(0)
        #print(oldest_time, time.time())
        if abs(oldest_time - time.time()) > 5:
            radar_state[0].pop(0) #pop the oldest stuff
            radar_state[1].pop(0)
            radar_state[2].pop(0)
            recursivePop()
        else:
            radar_state[3].insert(0,oldest_time)
    else:
        return
#TODO
# using the radar_state, calculate and publish the prevailing vel of
# the traffic overall, (or a lane by lane approximation?)
def getPrevailingSpeed():
    """returns the mean and standard deviation of object measurements in the last 5 seconds"""
    if len(radar_state[2]) >= 100:
        return np.mean(radar_state[2]),np.std(radar_state[2])
    else:
        return 0,0
# radar_state can do avg speeds, max speeds, or approx. distribution
# this means that a lane-independent control will be pulled faster by passing cars even if the car ahead is going slower


class middleway:
    def __init__(self):
        rospy.init_node('middleway', anonymous=True)

        # rospy.Subscriber(gantry_topic,Int16,gantry_callback)
        rospy.Subscriber(velocity_topic,Float64,velocity_callback)
        rospy.Subscriber(vsl_set_speed_topic,Float64,vsl_set_speed_callback)
        rospy.Subscriber(distance_lines_topic,Int16,distance_lines_callback)
        rospy.Subscriber(sport_mode_topic,Bool,sport_mode_callback)
        rospy.Subscriber(eco_mode_topic,Bool,eco_mode_callback)

        rospy.Subscriber(radar0_topic,PointStamped,radar0_callback)
        rospy.Subscriber(radar1_topic,PointStamped,radar1_callback)
        rospy.Subscriber(radar2_topic,PointStamped,radar2_callback)
        rospy.Subscriber(radar3_topic,PointStamped,radar3_callback)
        rospy.Subscriber(radar4_topic,PointStamped,radar4_callback)
        rospy.Subscriber(radar5_topic,PointStamped,radar5_callback)
        rospy.Subscriber(radar6_topic,PointStamped,radar6_callback)
        rospy.Subscriber(radar7_topic,PointStamped,radar7_callback)

        rospy.Subscriber(radar8_topic,PointStamped,radar8_callback)
        rospy.Subscriber(radar9_topic,PointStamped,radar9_callback)
        rospy.Subscriber(radar10_topic,PointStamped,radar10_callback)
        rospy.Subscriber(radar11_topic,PointStamped,radar11_callback)
        rospy.Subscriber(radar12_topic,PointStamped,radar12_callback)
        rospy.Subscriber(radar13_topic,PointStamped,radar13_callback)
        rospy.Subscriber(radar14_topic,PointStamped,radar14_callback)
        rospy.Subscriber(radar15_topic,PointStamped,radar15_callback)

        global middle_set_speed_pub
        middle_set_speed_pub = rospy.Publisher('/vsl/middleway_speed', Float64, queue_size=1000)
        global prevailing_speed_pub
        prevailing_speed_pub = rospy.Publisher('/vsl/ego_radar/prevailing_speed', Float64, queue_size=1000)
        global prevailing_speed_offset_pub
        prevailing_speed_offset_pub = rospy.Publisher('/vsl/v_pr_offset', Float64, queue_size=1000)
        # global in_i24_pub
        # in_i24_pub = rospy.Publisher('/vsl/in_i24', Bool, queue_size=10)
        # global vsl_set_speed_pub
        # vsl_set_speed_pub = rospy.Publisher('/vsl/set_speed', Float64, queue_size=1000) #sample and hold, doest not publish until getting close to one
        self.rate = rospy.Rate(20)

    def loop(self):
        print('Running middleway.')
        while not rospy.is_shutdown():
            try:
                global max_speed
                global social_limit_v
                global middle_set_speed_pub
                global vsl_set_speed
                global velocity
                global sport_mode
                global eco_mode
                global normal
                global base_social_limit

                if sport_mode:
                    social_limit_v = base_social_limit*1
                elif eco_mode:
                    social_limit_v = base_social_limit*3
                else:
                    social_limit_v = base_social_limit*2
                prevailing_speed_offset_pub.publish(social_limit_v)

                avg_v, std_v = getPrevailingSpeed()
                prevailing_speed_pub.publish(avg_v)
                # print('Radar avg: ',avg_v,'Radar STDev: ',std_v)
                # print()
                # print('min: ', np.min(radar_state[2]), 'max: ', np.max(radar_state[2]))
                # print('25th%: ', np.quantile(radar_state[2],0.25),'Mean: ',avg_v,'50th%: ', np.quantile(radar_state[2],0.5),'75th%: ', np.quantile(radar_state[2],0.75))
                # print(avg_v,social_limit_v,vsl_set_speed,max_speed)
                practical_vsl_set_speed = vsl_set_speed
                if vsl_set_speed == None:
                    practical_vsl_set_speed = velocity #when there is no vsl present
                middle_set_speed_pub.publish(min(max(avg_v-social_limit_v,practical_vsl_set_speed), max_speed))
            except Exception as e:
                print(e)
                traceback.print_exc()
                print("Something has gone wrong.")
            self.rate.sleep()

if __name__ == '__main__':
    try:
        head = middleway()
        head.loop()
    except Exception as e:
        print(e)
        traceback.print_exc()
        print("An exception occurred")
