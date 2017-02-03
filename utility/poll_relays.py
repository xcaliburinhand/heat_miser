
import datetime
import json
import logging
import random
import time

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    logging.error("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
except ImportError:
  nopi=True

if nopi!=True:
  GPIO.setmode(GPIO.BOARD)

hd=False

try:
  with open("config.json") as config_file:
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
  header = 'burner  '
  result = str(status).ljust(8)
else:
  result=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M')+','
  result+=str(status)

for zone in config['zones']:
  if nopi!=True:
    GPIO.setup(zone['pin'], GPIO.IN)
    status=GPIO.input(zone['pin'])
  else:
    status=random.randrange(0,2)
  if hd==True:
    header += zone+'  '
    result += '0'.ljust(2+len(zone))
  else:
    result += ','
    result += '0'
  
try:
  print(header)
except:
  pass
print(result)

if nopi!=True:
  GPIO.cleanup()