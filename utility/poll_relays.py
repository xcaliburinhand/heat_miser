
import datetime
import ecobee
import json
import logging
import pytz
import random
import re
import time
from collections import deque

logging.basicConfig(level=logging.INFO)

try:
  import RPi.GPIO as GPIO
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
  GPIO.setup(config['burner']['pin'], GPIO.IN)
  status=GPIO.input(config['burner']['pin'])
else:
  status=random.randrange(0,2)

if hd==True:
  header = 'Burner  '
  result = str(status).ljust(8)
else:
  header = 'timestamp,Burner'
  result=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M')+','
  result+=str(status)

for zone in config['zones']:
  if nopi!=True:
    GPIO.setup(config['zones'][zone]['pin'], GPIO.IN)
    status=GPIO.input(config['zones'][zone]['pin'])
  else:
    status=random.randrange(0,2)
  if hd==True:
    header += zone+'  '
    result += str(status).ljust(2+len(zone))
  else:
    header += ','
    header += zone
    result += ','
    result += str(status)

if datetime.datetime.now().minute % 5 == 0:
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
  if datetime.datetime.now().minute % 5 == 0:
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

if hd==True:
  print(header)
print(result)

if nopi!=True:
  GPIO.cleanup()
  
#update cache
try:
  with open('.cache') as cache_file:
    cache_list=deque(cache_file,5)
except IOError:
  cache_list=deque()
cache_list.append(result+'\n')
logging.debug('current cache: %s',cache_list)

with open('.cache','w') as cache_file:
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
  
  
  

  