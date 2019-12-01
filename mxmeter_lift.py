import sys
import requests
import json
from time import localtime, strftime

def log_file(msg):  
  log = open('/home/pi/log_mxmeter_lift.txt', 'a+')
  log_msg = strftime('%Y-%m-%d %H:%M:%S', localtime())
  log_msg += ' mxmeter_lift ' + msg + '\n'
  log.write(log_msg)
  log.close()

def ura_status(lift_name):
  url = 'http://137.116.160.215:9080/maximo/oslc/os/mxapiasset?_lid=mxintadm&_lpwd=mxintadm&oslc.select=assetmeter{lastreading}&oslc.where=assetnum=%22'
  lift_status = ['', '', '']
  i = 0
  for lift in lift_name:
    ret_lift = requests.get(url+lift+'%22')
    res = ret_lift.json()
    #print(res)
    res = res.get('rdfs:member')[0]
    #print(res)
    res = res.get('spi:assetmeter')[0]
    #print(res)
    lift_status[i] = res.get('spi:lastreading')
    i += 1

  #print(lift_status)
  return lift_status

def main():
  log_file('start')
  
  url = 'http://137.116.160.215:9080/maxrest/rest/os/MXMETERDATA?_format=json'
  headers = {'Content-type': 'application/json'}

  params = '&_lid=mxintadm&_lpwd=mxintadm&SITEID=MK01'

  # LIFT-001: 36 - FAULT; 38 - ON; 40 - OFF
  # LIFT-002: 35 - FAULT; 37 - ON; 32 - OFF
  # LIFT-003: 29 - FAULT; 31 - ON; 33 - OFF
  #lift_pin = [20, 21, 16, 26, 12, 19, 6, 13, 5]
  
  lift_name = ['LIFT-001', 'LIFT-002', 'LIFT-003']
  
  pre_status = ura_status(lift_name)

  gpiourl = 'http://172.22.207.82:5000/api/v1/pin'
  res = requests.get(gpiourl)
  #print(res.json())
  gpio = res.json()
  #print(gpio)

  status = ['', '', '']
  l = -1

  for pin in gpio:
    if pin.get('num') == 20:
      l = 0 
      if pin.get('value') == 0:
        status[l] = 'ON'
    elif pin.get('num') == 20:
      l = 0
      if pin.get('value') == 1:
        status[l] = 'OFF'
    elif pin.get('num') == 16:
      l = 0
      if pin.get('value') == 0:
        status[l] = 'FAULT'
    elif pin.get('num') == 26:
      l = 1
      if pin.get('value') == 0:
        status[l] = 'ON'
    elif pin.get('num') == 26:
      l = 1
      if pin.get('value') == 1:
        status[l] = 'OFF'
    elif pin.get('num') == 19:
      l = 1
      if pin.get('value') == 0:
        status[l] = 'FAULT'
    elif pin.get('num') == 6:
      l = 2
      if pin.get('value') == 0:
        status[l] = 'ON'
    elif pin.get('num') == 6:
      l = 2
      if pin.get('value') == 1:
        status[l] = 'OFF'
    elif pin.get('num') == 5:
      l = 2
      if pin.get('value') == 0:
        status[l] = 'FAULT'
    else:
      continue

  for i in range(3):
    #print(lift_name[i], pre_status[i], status[i])
    if pre_status[i] != status[i]:
      params += '&ASSETNUM=' + lift_name[i]
      params += '&METERNAME=IOTALARM'
      params += '&NEWREADING=' + status[i]
      
      data = {
        '_lid': 'mxintadm', 
        '_lpwd': 'mxintadm', 
        'SITEID': 'MK01', 
        'ASSETNUM': lift_name[i], 
        'METERNAME': 'IOTALARM', 
      }
      
      r = requests.post(url+params, data=json.dumps(data), headers=headers)
      #print(lift_name[i], pre_status[i], status[i], r.status_code)
      log_file('post ' + lift_name[i] + ' ' + status[i] + ' ' + str(r.status_code))
  
  sys.exit()

if __name__ == '__main__':
    main()
