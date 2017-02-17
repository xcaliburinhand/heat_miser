
import datetime
import ecobee
import json
import logging
import os
import random
import re
import time
from collections import deque

logging.basicConfig(level=logging.WARN)
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
  
def _adc_value(channel):
  if nopi!=True:
    SPICLK = 23
    SPIMISO = 21
    SPIMOSI = 19
    SPICS = 24
     
    # set up the SPI interface pins
    GPIO.setup([SPIMOSI, SPICLK, SPICS], GPIO.OUT)
    GPIO.setup(SPIMISO, GPIO.IN)
    
    adcval=readadc(channel, SPICLK, SPIMOSI, SPIMISO, SPICS)
    logging.debug("value of adc channel %s is %s",channel,adcval)
  else:
    return random.randrange(0,2)
  
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
  if nopi==True:
    return

  if ((adcnum > 7) or (adcnum < 0)):
          return -1
  GPIO.output(cspin, True)

  GPIO.output(clockpin, False)  # start clock low
  GPIO.output(cspin, False)     # bring CS low

  commandout = adcnum
  commandout |= 0x18  # start bit + single-ended bit
  commandout <<= 3    # we only need to send 5 bits here
  for i in range(5):
    if (commandout & 0x80):
      GPIO.output(mosipin, True)
    else:
      GPIO.output(mosipin, False)
    commandout <<= 1
    GPIO.output(clockpin, True)
    GPIO.output(clockpin, False)

  adcout = 0
  # read in one empty bit, one null bit and 10 ADC bits
  for i in range(12):
    GPIO.output(clockpin, True)
    GPIO.output(clockpin, False)
    adcout <<= 1
    if (GPIO.input(misopin)):
      adcout |= 0x1

  GPIO.output(cspin, True)
  
  adcout >>= 1       # first bit is 'null' so drop it
  return adcout

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
  result=now.strftime('%Y-%m-%d %H:%M')+','
  result+=str(status)

for zone in config['zones']:
  if "pin" in config['zones'][zone]:
    status=_pin_value(config['zones'][zone]['pin'])
  elif "adc" in config['zones'][zone]:
    status=_adc_value(config['zones'][zone]['spi'])
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
