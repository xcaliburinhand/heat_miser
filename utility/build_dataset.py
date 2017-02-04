
import copy
import csv
import datetime
import json
import logging
from operator import itemgetter

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
for therm in config['thermostats']:
  fields.append(str(therm))

equip=copy.copy(fields)
equip.remove('time')

status_store={}
call_store={}
rows =[]
calls = []
i=0

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
          if device.lower()=='burner':
            calls.append({"c":[{"v":device.title(),"f":None},{"v":
              datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
              str(datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").month-1)+
              datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
              ,"f":None},{"v":
              datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
              str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
              datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
              ,"f":None}]})
          else:
            rows.append({"c":[{"v":device.title(),"f":None},{"v":
              datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
              str(datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").month-1)+
              datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
              ,"f":None},{"v":
              datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
              str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
              datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
              ,"f":None}]})
          status_store[device]=None
      elif row[device]=='1':
        call_store[row['time']]=1
        if device not in status_store or status_store[device]==None:
          logging.debug('setting %s to on in status_store',device)
          status_store[device]=row['time']
    i+=1

# drain status_store
for device in equip:
  if device not in status_store:
    pass
  elif status_store[device]!=None:
    if device.lower()=='burner':
      calls.append({"c":[{"v":device.title(),"f":None},{"v":
        datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
        str(datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").month-1)+
        datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
        ,"f":None},{"v":
        datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
        str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
        datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
        ,"f":None}]})
    else:
      rows.append({"c":[{"v":device.title(),"f":None},{"v":
        datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
        str(datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").month-1)+
        datetime.datetime.strptime(status_store[device],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
        ,"f":None},{"v":
        datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
        str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
        datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
        ,"f":None}]})

# ensure all devices are added to table
for device in equip:
  if device.lower()=='burner':
    calls.append({"c":[{"v":device.title(),"f":None},{"v":
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d)')
      ,"f":None},{"v":
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d)')
      ,"f":None}]})
  else:
    rows.append({"c":[{"v":device.title(),"f":None},{"v":
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d)')
      ,"f":None},{"v":
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d)')
      ,"f":None}]})
calls.append({"c":[{"v":"Heat Call","f":None},{"v":
  datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
  str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
  datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d)')
  ,"f":None},{"v":
  datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
  str(datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").month-1)+
  datetime.datetime.strptime(row['time'],"%Y-%m-%d %H:%M").strftime(', %d)')
  ,"f":None}]})

calllist = call_store.keys()
calllist.sort()
logging.debug(calllist)
end=None
for calltime in calllist:
  if end==None:
    beg=calltime
    end=calltime
  elif (datetime.datetime.strptime(calltime,"%Y-%m-%d %H:%M")-datetime.datetime.strptime(calllist[len(calllist)-1],"%Y-%m-%d %H:%M")).total_seconds()==0:
    calls.append({"c":[{"v":"Heat Call","f":None},{"v":
      datetime.datetime.strptime(beg,"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(beg,"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(beg,"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
      ,"f":None},{"v":
      datetime.datetime.strptime(end,"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(end,"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(calltime,"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
      ,"f":None}]})
  elif (datetime.datetime.strptime(calltime,"%Y-%m-%d %H:%M")-datetime.datetime.strptime(end,"%Y-%m-%d %H:%M")).total_seconds()>60:
    logging.debug((datetime.datetime.strptime(calltime,"%Y-%m-%d %H:%M")-datetime.datetime.strptime(end,"%Y-%m-%d %H:%M")).total_seconds())
    calls.append({"c":[{"v":"Heat Call","f":None},{"v":
      datetime.datetime.strptime(beg,"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(beg,"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(beg,"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
      ,"f":None},{"v":
      datetime.datetime.strptime(end,"%Y-%m-%d %H:%M").strftime('Date(%Y, ')+
      str(datetime.datetime.strptime(end,"%Y-%m-%d %H:%M").month-1)+
      datetime.datetime.strptime(end,"%Y-%m-%d %H:%M").strftime(', %d, %H, %M)')
      ,"f":None}]})
    beg=calltime
    end=calltime
  elif (datetime.datetime.strptime(calltime,"%Y-%m-%d %H:%M")-datetime.datetime.strptime(end,"%Y-%m-%d %H:%M")).total_seconds()==60:
    end=calltime

dataTable={"cols":cols,"rows":rows}
logging.debug(dataTable)
with open(config['data_dir']+'/20170203.json','w') as out:
  json.dump(dataTable,out)
dataTable={"cols":cols,"rows":calls}
with open(config['data_dir']+'/20170203_overall.json','w') as out:
  json.dump(dataTable,out)
  
