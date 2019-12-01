#!/usr/bin/env python
import time
import serial
import sys
import requests
import json
from time import localtime, strftime

def log_file(msg):  
  log = open('home/pi/log_mxmeter_odor_fan.txt', 'a+')
  log_msg = strftime('%Y-%m-%d %H:%M:%S', localtime())
  log_msg += ' mxmeter_odor_fan ' + msg + '\n'
  log.write(log_msg)
  log.close()
  
def ura_status(name):
  url = 'http://137.116.160.215:9080/maximo/oslc/os/mxapiasset?_lid=mxintadm&_lpwd=mxintadm&oslc.select=assetmeter{metername,lastreading}&oslc.where=assetnum=%22'
  
  url += name + '%22'
  #print(url)
  reply = requests.get(url)
  
  status = 0
  if reply.status_code == 200:
    res = reply.json()
    #print(res)
    res = res.get('rdfs:member')[0]
    #print(res)
    if name == 'EXTFAN-018':
      res = res.get('spi:assetmeter')[1]
    else:
      res = res.get('spi:assetmeter')[0]
    #print(res)
    status = int(res.get('spi:lastreading'))
    #print(status)
    return status
  else:
    return status

def poststatus(assetnum, metername, newreading):
  url = 'http://137.116.160.215:908f0/maxrest/rest/os/MXMETERDATA?_format=json'
  headers = {'Content-type': 'application/json'}
  
  params = '&_lid=mxintadm&_lpwd=mxintadm&SITEID=MK01'  
  params += '&ASSETNUM=' + assetnum
  params += '&METERNAME=' + metername  
  params += '&NEWREADING=' + newreading

    
  data = {
    '_lid': 'mxintadm', 
    '_lpwd': 'mxintadm', 
    'SITEID': 'MK01', 
    'ASSETNUM': assetnum,
    'METERNAME': metername, 
    'NEWREADING': newreading
  }
  
  r = requests.post(url+params, data=json.dumps(data), headers=headers)
  #print(assetnum, newreading, r.status_code)
  log_file('post ' + assetnum + ' ' + newreading + ' ' + str(r.status_code))

def main():
  log_file('start')
  
  odor_name = ['ODOR-001', 'ODOR-002']
  fan_name = ['EXTFAN-018']
  
  ser0 = serial.Serial(
          port = '/dev/ttyUSB0',
          baudrate = 9600,
          parity = serial.PARITY_NONE,
          stopbits = serial.STOPBITS_ONE,
          bytesize = serial.EIGHTBITS,
          timeout = 1
      )
      
  ser1 = serial.Serial(
          port = '/dev/ttyUSB1',
          baudrate = 9600,
          parity = serial.PARITY_NONE,
          stopbits = serial.STOPBITS_ONE,
          bytesize = serial.EIGHTBITS,
          timeout = 1
      )    
        
  #ser0.write('Z'.encode())
  #ser1.write('Z'.encode())
  #ser1.write('e'.encode())
  
  ser0.write('c'.encode())
  ser1.write('c'.encode())
  
  #5, 10, 30, 60s
  ser0.write('5'.encode())
  ser1.write('5'.encode())
  
  while True:
    usb0 = ser0.readline()
    #print(usb0)
    
    level_odor1 = 0
    if len(usb0) > 1:
      #print(usb0)
      res = usb0.split(', ')
      #print(res)
      
      h2s = int(res[1])
      
      if h2s > 0 and h2s < 101:
        level_odor1 = 1
      elif h2s > 100 and h2s < 301:
        level_odor1 = 2
      elif h2s > 300 and h2s < 401:
        level_odor1 = 3
      elif h2s > 400:
        level_odor1 = 4
        
      odor1_status = ura_status(odor_name[0])
      
      if odor1_status != level_odor1 and level_odor1 > 0:
        poststatus(odor_name[0], 'ODOR', str(level_odor1))
    
    usb1 = ser1.readline()
    #print(usb1)
    
    level_odor2 = 0
    if len(usb1) > 1:
      #print(usb1)
      res = usb1.split(', ')
      #print(res)
      
      h2s = int(res[1])
      
      if h2s > 0 and h2s < 101:
        level_odor2 = 1
      elif h2s > 100 and h2s < 301:
        level_odor2 = 2
      elif h2s > 300 and h2s < 401:
        level_odor2 = 3
      elif h2s > 400:
        level_odor2 = 4
        
      odor2_status = ura_status(odor_name[1])
      
      if odor2_status != level_odor2 and level_odor2 > 0:
        poststatus(odor_name[1], 'ODOR', str(level_odor1))
    
    fan_status = ura_status(fan_name[0])
    #print(level_odor1)
    #print(level_odor2)
    #print("fan_status: " + str(fan_status))
    
    if level_odor1 > 0 and level_odor2 > 0:
      if level_odor1 <= level_odor2 and level_odor2 != fan_status:
        poststatus(fan_name[0], 'FANSPEED', str(level_odor2))
        #print('fan: ' + str(level_odor2))
      elif level_odor1 > level_odor2 and level_odor1 != fan_status:
        poststatus(fan_name[0], 'FANSPEED', str(level_odor1))
        #print('fan: ' + str(level_odor1))
    elif level_odor1 > 0 and level_odor2 < 1 and level_odor1 != fan_status:
      poststatus(fan_name[0], 'FANSPEED', str(level_odor1))
      #print('fan: ' + str(level_odor1))
    elif level_odor1 < 1 and level_odor2 > 0 and level_odor2 != fan_status:
      poststatus(fan_name[0], 'FANSPEED', str(level_odor2))
      #print('fan: ' + str(level_odor2))
      

if __name__ == '__main__':
    main()