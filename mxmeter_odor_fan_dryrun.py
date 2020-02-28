#!/usr/bin/env python
import time
import sys
import requests
import json
from random import randrange
from time import localtime, strftime, sleep

def log_file(msg):  
  log = open('/home/pi/log_mxmeter_odor_fan.txt', 'a+')
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
      res = res.get('spi:assetmeter')[0]
    else:
      res = res.get('spi:assetmeter')[0]
    #print(res)
    status = int(res.get('spi:lastreading'))
    #print(status)
    return status
  else:
    return status

def poststatus(assetnum, metername, newreading):
  url = 'http://137.116.160.215:9080/maxrest/rest/os/MXMETERDATA?_format=json'
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
  print(assetnum, newreading, r.status_code)
  log_file('post ' + assetnum + ' ' + newreading + ' ' + str(r.status_code))

def main():
  #log_file('start')
  
  sleep(randrange(60,300))
  
  odor_name = ['ODOR-001', 'ODOR-002']
  fan_name = ['EXTFAN-018']
  
  level_odor1 = 1
  level_odor2 = 1
  level_fan = 1
  
  fan_status = ura_status(fan_name[0])
  if fan_status == 1:
    level_odor1 = 2
    level_odor2 = 2
    level_fan = 2
 
  odor1_status = ura_status(odor_name[0])

 
  poststatus(odor_name[0], 'ODOR', str(level_odor1))
  poststatus(odor_name[0], 'ODOR', str(level_odor2))
  poststatus(fan_name[0], 'FANSPEED', str(level_fan)) 

  #print(level_odor1)
  #print(level_odor2)
  #print("fan_status: " + str(fan_status))


if __name__ == '__main__':
    main()