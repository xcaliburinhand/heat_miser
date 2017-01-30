
import copy
import csv
import datetime
import json
import logging

logging.basicConfig(level=logging.DEBUG)

fields=['time','burner']
cols= [
        {"id":"","label":"Zone","pattern":"","type":"string"},
        {"id":"","label":"Equipment Start","pattern":"","type":"date"},
        {"id":"","label":"Equipment Stop","pattern":"","type":"date"}
      ]

with open('config.json') as configfile:
  config = json.load(configfile)
  
for zone in config['zones']:
  fields.append(str(zone))

equip=copy.copy(fields)
equip.remove('time')

status_store={}
rows =[]

with open('fake_data') as csvfile:
  reader = csv.DictReader(csvfile,fieldnames=fields)
  for row in reader:
    logging.debug(row)
    for device in equip:
      logging.debug("row value for %s is %s",device,row[device])
      if row[device]=='0':
        logging.debug("status_store: %s",status_store)
        if device not in status_store or status_store[device]==None:
          logging.debug('%s is not on in status_store',device)
          pass
        else:
          logging.debug('writing data point and changing %s to off in status_store',device)
          rows.append({"c":[{"v":device,"f":None},{"v":"Date("+
            datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M:%S").strftime('%Y, %m, %d, %H, %M')+
            ")","f":None},{"v":"Date("+
            datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M:%S").strftime('%Y, %m-1, %d, %H, %M')+
            ")","f":None}]})
          status_store[device]=None
      elif row[device]=='1':
        if device not in status_store or status_store[device]==None:
          logging.debug('setting %s to on in status_store',device)
          status_store[device]=row['time']

# drain status_store
for device in equip:
  if device not in status_store:
    pass
  elif status_store[device]!=None:
    rows.append({"c":[{"v":device,"f":None},{"v":"Date("+
      datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M:%S").strftime('%Y, %m, %d, %H, %M')+
      ")","f":None},{"v":"Date("+
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M:%S").strftime('%Y, %m, %d, %H, %M')+
      ")","f":None}]})

dataTable={"cols":cols,"rows":rows}
logging.debug(json.dumps(dataTable))