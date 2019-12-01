#!/usr/bin/python

import socket
import threading
import codecs
import base64
import json
import numpy as np
import datetime
#import matplotlib.pyplot as plt
import requests
from time import localtime, strftime

port = 8093
bufferSize = 1024

rssi = 0
snr = 0
vcc = 0

def log_file(msg):  
  log = open('/home/pi/log_mxmeter_door.txt', 'a+')
  log_msg = strftime('%Y-%m-%d %H:%M:%S', localtime())
  log_msg += ' mxmeter_door ' + msg + '\n'
  log.write(log_msg)
  log.close()

def check_fault():
  door_name = {'2008':'DOOR-003', '2011':'DOOR-016', '2014':'DOOR-039', '2010':'DOOR-050', '2009':'DOOR-060', '2005':'DOOR-058', '2013':'DOOR-073', '2002':'DOOR-084', '2016':'DOOR-088', '2007':'DOOR-099', '2015':'DOOR-108', '2004':'DOOR-119', '2006':'DOOR-140', '2012':'DOOR-156', '2003':'DOOR-135', '2001':'DOOR-163'}
  
  url = 'http://137.116.160.215:9080/maximo/oslc/os/mxapiasset?_lid=mxintadm&_lpwd=mxintadm&oslc.select=assetmeter{lastreading,changedate}&oslc.where=assetnum=%22'
  
  now_time = strftime('%Y-%m-%d %H:%M:%S', localtime())
  
  for i in range(2001, 2017):
    ret_door = requests.get(url + door_name[str(i)] + '%22')
    res = ret_door.json()
    #print(res)
    res = res.get('rdfs:member')[0]
    #print(res)
    last_time = res.get('spi:changedate')
    print(last_time)
    door_status = res.get('spi:lastreading')
    
    diff = now_time - last_time
    diff_mins = diff.seconds / 60
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
  
      print(moduleID, door_name[str(moduleID)], 'FAULT')
      r = requests.post(url+params, data=json.dumps(data), headers=headers)
      #print(moduleID, door_name[str(moduleID)], 'FAULT', r.status_code)
      log_file('post ' + door_name[str(moduleID)] + ' ' + str(diff_mins) + ' ' + 'FAULT' + ' ' + str(r.status_code))

def ura_status(door_name):
  url = 'http://137.116.160.215:9080/maximo/oslc/os/mxapiasset?_lid=mxintadm&_lpwd=mxintadm&oslc.select=assetmeter{lastreading}&oslc.where=assetnum=%22'
  door_status = ''
  ret_door = requests.get(url+door_name+'%22')
  res = ret_door.json()
  #print(res)
  res = res.get('rdfs:member')[0]
  #print(res)
  res = res.get('spi:assetmeter')[0]
  #print(res)
  door_status = res.get('spi:lastreading')
 
  return door_status

def decryptDoorSense(rawData, sf):
  data = bytearray(6)
  key = b''
  if(sf == 'SF7B'):
    key = b'\xa1\x02\xd6\x80\xac\x6e'
  elif(sf == 'SF8B'):
    key = b'\xea\xc9\xf8\x68\x27\x29'
  elif(sf == 'SF9B'):
    key = b'\x03\x8c\x53\x75\x08\x53'
  elif(sf == 'SF10'):
    key = b'\x93\x49\xd9\x79\xe9\x6f'
  elif(sf == 'SF11'):
    key = b'\x88\x34\xe8\x98\x74\xeb'
  elif(sf == 'SF12'):
    key = b'\x44\x40\x0e\x66\x27\x90'
  
  for i in range(0, 6, 1):
    data[i] = rawData[i] ^ key[i]
  for i in range(0, 6, 1):
    data[i] = data[i] ^ data[5]
  return data

def parseDoorSense(rawData, sf):
  door_name = {'2008':'DOOR-003', '2011':'DOOR-016', '2014':'DOOR-039', '2010':'DOOR-050', '2009':'DOOR-060', '2005':'DOOR-058', '2013':'DOOR-073', '2002':'DOOR-084', '2016':'DOOR-088', '2007':'DOOR-099', '2015':'DOOR-108', '2004':'DOOR-119', '2006':'DOOR-140', '2012':'DOOR-156', '2003':'DOOR-135', '2001':'DOOR-163'}
  
  if(len(rawData) != 6):
    return
  data = decryptDoorSense(rawData, sf)
  if(data[4] != 0xa6):
    return
  if(data[5] != 0x00):
    print(data[5])
    return
    
  moduleID = int.from_bytes(data[0:2], byteorder='little', signed=False)
  
  if moduleID > 2000 and moduleID < 2017:
    doorStateRaw = int.from_bytes(data[2:4], byteorder='little', signed=False)& 0xFC00

    if(doorStateRaw == 0x5800):
      doorState = 'ON'
    elif(doorStateRaw == 0xA400):
      doorState = 'OFF'
    else:
      doorState = 'FAULT'
  
    vcc=1074*1024/(int.from_bytes(data[2:4], byteorder='little', signed=False) & 0x3FF)

    prev_status =  ura_status(door_name[str(moduleID)])
  
    if prev_status != doorState:
      url = 'http://137.116.160.215:9080/maxrest/rest/os/MXMETERDATA?_format=json'
      headers = {'Content-type': 'application/json'}
  
      params = '&_lid=mxintadm&_lpwd=mxintadm&SITEID=MK01'
      params += '&ASSETNUM=' + door_name[str(moduleID)]
      params += '&METERNAME=IOTALARM'
      params += '&NEWREADING=' + doorState   
    
      data = {
        '_lid': 'mxintadm', 
        '_lpwd': 'mxintadm', 
        'SITEID': 'MK01', 
        'ASSETNUM': door_name[str(moduleID)], 
        'METERNAME': 'IOTALARM', 
        'NEWREADING': doorState
      }
  
      #print(moduleID, door_name[str(moduleID)], doorState)
      r = requests.post(url+params, data=json.dumps(data), headers=headers)
      #print(moduleID, door_name[str(moduleID)], doorState, r.status_code)
      log_file('post ' + door_name[str(moduleID)] + ' ' + doorState + ' ' + str(r.status_code))
      
      print("Time:" , datetime.datetime.now(), "module: ", moduleID, "State: ", doorState, " RSSI: ", rssi, " SNR: ", snr, " SF: ", sf, " vcc: ", vcc)
      
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("", port))
s.setblocking(0)
s.settimeout(.1)

#print("Port opened at", port)
log_file('start ' + str(port))

while True:
  #check_fault()
  try:
    addr = 0
    payload, addr = s.recvfrom(bufferSize)    
    if (addr == 0):
      continue
    if (len(payload) < 13):
      continue
    if (payload[0] != 2):
      continue
    try:
      packet = json.loads(payload[12:])      
    except JSONDecodeError:
      continue
    if ("rxpk" not in packet):
      continue
    
    for i in range (len(packet["rxpk"])-1, -1, -1):
      currentPacket = packet["rxpk"][i]
      tmst=int(currentPacket["tmst"]) / 1000000
      rssi=int(currentPacket["rssi"])
      snr=int(currentPacket["lsnr"])
      sf=currentPacket["datr"][:4]
      data=base64.b64decode(currentPacket["data"])
      parseDoorSense(data, sf)

  except socket.timeout:
    continue
  except KeyboardInterrupt:
    exit()
  except BlockingIOError:
    continue
