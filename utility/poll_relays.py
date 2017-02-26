
import datetime
import ecobee
import json
import logging
import math
import os
import random
import re
import time
from collections import deque

logging.basicConfig(level=logging.INFO)
os.environ['TZ'] = 'US/Eastern'
now = datetime.datetime.fromtimestamp(time.time())

def _pin_value(pin):
  if nopi!=True:
    GPIO.setup(pin, GPIO.IN)
    pinval = GPIO.input(pin)
    logging.debug("value of pin %s is %s",pin,pinval)
    return pinval
  else:
    return random.randrange(0,2)

def bitstring(n):
    s = bin(n)[2:]
    return '0'*(8-len(s)) + s

def average(values):
  total=0
  for val in values:
    total+=val
  return total/len(values)

def stddev(values):
  min=9999
  max=0
  total=0
  for val in values:
    if val>max: max=val
    if val<min: min=val
  for val in values:
    total+=((val-((min+max)/2))*(val-((min+max)/2)))
  return math.sqrt(total/len(values))

def _adc_value(adc_channel):
  if nopi!=True:
    conn = spidev.SpiDev(0, 0)
    conn.max_speed_hz = 1200000 # 1.2 MHz
    conn.mode = 0
    logging.debug("spi mode=%s",conn.mode)
    cmd = 192 #start bit + single ended
    cmd = 128
    if adc_channel:
        cmd += 32
    val=[]
    min=9999
    max=0
    for num in range(0,5000):
      reply_bytes = conn.xfer2([cmd, 0])
      reply_bitstring = ''.join(bitstring(n) for n in reply_bytes)
      reply = reply_bitstring[5:15]
      val.append(int(reply,2))
      if int(reply,2)>max: max=int(reply,2)
      if int(reply,2)<min: min=int(reply,2)
      time.sleep(0.001)
    logging.info("average value of adc channel %s is %s, median %s, std dev %s, min %s, max %s, diff %s",adc_channel,average(val),(min+max)/2,stddev(val),min,max,max-min)
    if  (max-min)<20:
      return 0
    elif stddev(val)>5:
      return 1
    else:
      return 0
  else:
    return random.randrange(0,2)

try:
  import RPi.GPIO as GPIO
  import spidev
  nopi=False
except RuntimeError:
  logging.error("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
except ImportError:
  nopi=True

if nopi!=True:
  GPIO.setmode(GPIO.BOARD)

hd=False

try:
  with open("/etc/heatmiser/config.json") as config_file:
    config = json.load(config_file)
except Exception as e:
  logging.error("Config file error {0}".format(e))
  exit(99)  

if nopi!=True:
  if "pin" in config['burner']:
    status=_pin_value(config['burner']['pin'])
  elif "adc" in config['burner']:
    status=_adc_value(config['burner']['adc'])
  else:
    logging.warn("No interface defined for burner")
else:
  status=random.randrange(0,2)

if hd==True:
  header = 'Burner  '
  result = str(status).ljust(8)
else:
  header = 'timestamp,Burner'
  result=now.strftime('%Y-%m-%d %H:%M')+','
  result+=str(status)

for zone in config['zones']:
  if "pin" in config['zones'][zone]:
    status=_pin_value(config['zones'][zone]['pin'])
  elif "adc" in config['zones'][zone]:
    status=_adc_value(config['zones'][zone]['adc'])
  else:
    logging.warn("No interface defined for %s",zone)
    
  if hd==True:
    header += zone+'  '
    result += str(status).ljust(2+len(zone))
  else:
    header += ','
    header += zone
    result += ','
    result += str(status)

if datetime.datetime.now().minute % 3 == 0:
  bee=ecobee.Client('LXaXX6lrtFoRml81RPvS0Q07BGrFoaeh',authfile='/etc/heatmiser/ecobee.conf')
  data = bee.get("thermostatSummary", {
        "selection": {
            "selectionType":  "registered",
            "selectionMatch": "",
            "includeEquipmentStatus":   True
        }
    })
  status_list=data['statusList']

for therm in config['thermostats']:
  if datetime.datetime.now().minute % 3 == 0:
      regex=re.compile(".*("+config['thermostats'][therm]+").*")
      equip_status = [m.group(0) for l in status_list for m in [regex.search(l)] if m]
      if "heat" in equip_status[0].lower():
        status = '1'
      else:
        status = '0'
  else:
    status = '-'
  if hd==True:
    header += therm+'  '
    result += str(status).ljust(2+len(therm))
  else:
    header += ','
    header += therm
    result += ','
    result += str(status)

if nopi!=True:
  GPIO.cleanup()

if hd==True:
  print(header)
print(result)
with open(os.path.dirname(os.path.realpath(__file__))+'/run_data/'+now.strftime('%Y%m%d')+'.csv','a') as run_data:
  run_data.write(result+'\n')
  
#update cache
try:
  with open(os.path.dirname(os.path.realpath(__file__))+'/.cache') as cache_file:
    cache_list=deque(cache_file,5)
except IOError:
  cache_list=deque()
cache_list.append(result+'\n')
logging.debug('current cache: %s',cache_list)

with open(os.path.dirname(os.path.realpath(__file__))+'/.cache','w') as cache_file:
  for line in cache_list:
    cache_file.write(line)

current_state={}
cache_list.reverse()
i=0
for heading in header.split(','):
  if heading=='timestamp':
    i+=1 
    continue
  for cache_item in cache_list:
    cache_val=cache_item.split(',')[i].strip()
    if cache_val=='0' or cache_val=='1':
      current_state[heading]=cache_val
      logging.debug('%s is %s at %s',heading,cache_val,cache_item.split(',')[0])
      break
  i+=1
  
with open(config['data_dir']+'/current_state.json','w') as out:
  json.dump(current_state,out)
