#!/usr/bin/python3
import socket
import threading
import codecs
import base64
import json
import numpy as np
import datetime
import sys
#import matplotlib.pyplot as plt
import requests
from time import localtime, strftime
import re

port = 8093
bufferSize = 1024
rssi = 0
snr = 0
vcc = 0

def log_file(msg):
  log = open('/home/pi/log_mxmeter_door.txt', 'a+')
  log_msg = strftime('%Y-%m-%d %H:%M:%S', localtime())
  log_msg += ' mxmeter_door_fault ' + msg + '\n'
  log.write(log_msg)
  log.close()
  
def check_fault():
  door_name = {'2008':'DOOR-003', '2011':'DOOR-016', '2014':'DOOR-039', '2010':'DOOR-050', '2009':'DOOR-060', '2005':'DOOR-058', '2013':'DOOR-073', '2002':'DOOR-084', '2016':'DOOR-088', '2007':'DOOR-099', '2015':'DOOR-108', '2004':'DOOR-119', '2006':'DOOR-140', '2012':'DOOR-156', '2003':'DOOR-135', '2001':'DOOR-163'}
  
  url = 'http://137.116.160.215:9080/maximo/oslc/os/mxapiasset?_lid=mxintadm&_lpwd=mxintadm&oslc.select=assetmeter{lastreading,changedate}&oslc.where=assetnum=%22'
  
  now_time = datetime.datetime.now()
  print('now_time: ' + now_time.isoformat())
  #print(datetime.datetime.now())
  
  for i in range(2001, 2017):
    ret_door = requests.get(url + door_name[str(i)] + '%22')
    print(i, ret_door.status_code)
    
    if ret_door.status_code == 200:
      res = ret_door.json()
      res = res.get('rdfs:member')
      j = res[0]['spi:assetmeter'][0]
      # print(j['spi:changedate'], j['spi:lastreading'])
      last_time = j['spi:changedate']
      print(last_time)
      last_time = datetime.datetime.strptime(last_time, "%Y-%m-%dT%H:%M:%S%z")
      door_status = j['spi:lastreading']
      print(door_status)
      diff_mins = (now_time.timestamp() - last_time.timestamp())/60
      print(diff_mins)
      
      if diff_mins > 5 and door_status == 'ON':
        door_status = 'FAULT'
        url = 'http://137.116.160.215:9080/maxrest/rest/os/MXMETERDATA?_format=json'
        headers = {'Content-type': 'application/json'}
        params = '&_lid=mxintadm&_lpwd=mxintadm&SITEID=MK01'
        params += '&ASSETNUM=' + door_name[str(i)]
        params += '&METERNAME=IOTALARM'
        params += '&NEWREADING=FAULT'
        data = {
          '_lid': 'mxintadm',
          '_lpwd': 'mxintadm',
          'SITEID': 'MK01',
          'ASSETNUM': door_name[str(i)],
          'METERNAME': 'IOTALARM',
          'NEWREADING': 'FAULT'
        }
        print(i, door_name[str(i)], 'FAULT')
        r = requests.post(url+params, data=json.dumps(data), headers=headers)
        #print(i, door_name[str(i)], 'FAULT', r.status_code)
        log_file('post ' + door_name[str(i)] + ' ' + str(diff_mins) + ' ' + 'FAULT' + ' ' + str(r.status_code))
    else:
      continue

check_fault()
sys.exit()
