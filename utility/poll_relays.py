
import datetime
import json
import logging
import time

hd=False

try:
  with open("config.json") as config_file:
    config = json.load(config_file)
except Exception as e:
  logging.error("Config file error {0}".format(e))
  exit(99)  

if hd==True:
  header = 'burner  '
  result = '1'.ljust(8)
else:
  result=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')+','
  result+='1'

for zone in config['zones']:
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