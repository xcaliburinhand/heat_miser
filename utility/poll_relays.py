import datetime
import ecobee
import json
import logging
import math
import os
import random
import re
import time
from collections import deque, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('poll_relays')
logger.setLevel(level=logging.INFO)

os.environ['TZ'] = 'US/Eastern'
now = datetime.datetime.fromtimestamp(time.time())


def _pin_value(pin):
    if nopi is True:
        return random.randrange(0, 2)
    GPIO.setup(pin, GPIO.IN)
    pinval = GPIO.input(pin)
    logger.debug("value of pin %s is %s", pin, pinval)
    return pinval


def bitstring(n):
    s = bin(n)[2:]
    return '0'*(8-len(s)) + s


def average(values):
    total = 0
    for val in values:
        total += val
    return total/len(values)


def _stddev(values):
    min = _min(values)
    max = _max(values)
    total = 0
    for val in values:
        total += ((val-((min+max)/2.0))*(val-((min+max)/2.0)))
    return math.sqrt(total/len(values))


def _min(values):
    min = 9999
    for val in values:
        if val < min:
            min = val
    return min


def _max(values):
    max = 0
    for val in values:
        if val > max:
            max = val
    return max


def _most_occur(values):
    return Counter(values).most_common(1)[0][0]


def _adc_value(adc_channel):
    if nopi is True:
        return random.randrange(0, 2)

    conn = spidev.SpiDev(0, 0)
    conn.max_speed_hz = 1200000  # 1.2 MHz
    conn.mode = 0
    logger.debug("spi mode=%s", conn.mode)
    cmd = 192  # start bit + single ended
    cmd = 128
    if adc_channel:
        cmd += 32
    val = []
    for num in range(0, 500):
        reply_bytes = conn.xfer2([cmd, 0])
        reply_bitstring = ''.join(bitstring(n) for n in reply_bytes)
        reply = reply_bitstring[5:15]
        val.append(int(reply, 2))
        time.sleep(0.002)
    for num in range(0, 10):
        val.pop(num)
    min = _min(val)
    max = _max(val)
    stddev = _stddev(val)
    common = _most_occur(val)
    logger.info(
        "average value of adc channel %s is %s, median %s, std dev %s, min %s, max %s, diff %s, common %s",
        adc_channel, average(val), (min+max)/2.0, stddev, min, max, max-min, common
    )
    with open(
        os.path.dirname(os.path.realpath(__file__))+'/run_data/'+now.strftime('%Y%m%d')+'_debug.csv',
        'a'
    ) as debug_data:
        debug_data.write(now.strftime('%Y-%m-%d %H:%M')+','+str(average(val))+','+str((min+max)/2.0)+','+str(stddev)+','+str(min)+','+str(max)+','+str(max-min)+'\n')
    if (max-min) >= 60:
        if min >= 733 and min <= 735:
            return 1
        return 0  # over 60 not in range
    if (max-min) >= 27 and common >= 752 and common <= 768 and min >= 739 and min <= 744:
        return 1
    if (max-min) > 40 and min >= 749 and min <= 751:
        return 1
    if (min+max)/2.0 >= 768.0 and (min+max)/2.0 <= 771.5 and min >= 751 and min <= 753:
        return 1
    if average(val) >= 755 and average(val) <= 757 and max >= 770 and max <= 772:
        return 1
    if max >= 790 and max <= 792 and (min+max)/2.0 >= 772.0 and (min+max)/2.0 <= 773.0:
        return 1
    return 0


try:
    import RPi.GPIO as GPIO
    import spidev
    nopi = False
except RuntimeError:
    logger.error("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
except ImportError:
    nopi = True

if nopi is not True:
    GPIO.setmode(GPIO.BOARD)

hd = False

try:
    with open("/etc/heatmiser/config.json") as config_file:
        config = json.load(config_file)
except Exception as e:
    logger.error("Config file error {0}".format(e))
    exit(99)

if nopi is not True:
    if "pin" in config['burner']:
        status = _pin_value(config['burner']['pin'])
    elif "adc" in config['burner']:
        status = _adc_value(config['burner']['adc'])
    else:
        logger.warn("No interface defined for burner")
else:
    status = random.randrange(0, 2)

if hd is True:
    header = 'Burner  '
    result = str(status).ljust(8)
else:
    header = 'timestamp,Burner'
    result = now.strftime('%Y-%m-%d %H:%M')+','
    result += str(status)

for zone in config['zones']:
    if "pin" in config['zones'][zone]:
        status = _pin_value(config['zones'][zone]['pin'])
    elif "adc" in config['zones'][zone]:
        status = _adc_value(config['zones'][zone]['adc'])
    else:
        logger.warn("No interface defined for %s", zone)

    if hd is True:
        header += zone+'  '
        result += str(status).ljust(2+len(zone))
    else:
        header += ','
        header += zone
        result += ','
        result += str(status)

if config['query_ecobee'] is True and datetime.datetime.now().minute % 3 == 0:
    bee = ecobee.Client('LXaXX6lrtFoRml81RPvS0Q07BGrFoaeh', authfile='/etc/heatmiser/ecobee.conf')
    data = bee.get("thermostatSummary", {
            "selection": {
                "selectionType":  "registered",
                "selectionMatch": "",
                "includeEquipmentStatus": True
            }
        })
    status_list = data['statusList']

if config['query_ecobee'] is True and datetime.datetime.now().minute % 9 == 0:
    try:
        with open(config['data_dir']+'/'+now.strftime('%Y%m%d')+'_temps.json') as json_file:
            json_data = json.load(json_file)
    except IOError:
        json_data = {}
    if 'cols' not in json_data:
        json_data = {"cols": [], "rows": []}
    cols = [{"type": "datetime"}]
    row = [{"v": now.strftime('Date(%Y,%m,%d,%H,%M)')}]
    temps = now.strftime('%Y-%m-%d %H:%M')
    data = bee.get("thermostat", {
            "selection": {
                "selectionType":  "registered",
                "selectionMatch": "",
                "includeSensors": True
            }
        })
    them_list = data['thermostatList']
    for therm in them_list:
        for sensor in therm['remoteSensors']:
            cols.append({"label": sensor['name'], "type": "number"})
            sensor_temps = filter(lambda capability: capability['type'] == 'temperature', sensor['capability'])
            temp = str(float(next(sensor_temps)['value'])/10)
            temps += ','+temp
            row.append({"v": temp})
    print(temps)
    json_data['cols'] = cols
    json_data['rows'].append({"c": row})
    with open(config['data_dir']+'/'+now.strftime('%Y%m%d')+'_temps.json', 'w') as json_file:
        json.dump(json_data, json_file)

for therm in config['thermostats']:
    if config['query_ecobee'] is True and datetime.datetime.now().minute % 3 == 0:
        regex = re.compile(".*("+config['thermostats'][therm]+").*")
        equip_status = [m.group(0) for l in status_list for m in [regex.search(l)] if m]
        if "heat" in equip_status[0].lower():
            status = '1'
        else:
            status = '0'
    else:
        status = '-'
    if hd is True:
        header += therm+'  '
        result += str(status).ljust(2+len(therm))
    else:
        header += ','
        header += therm
        result += ','
        result += str(status)

if nopi is not True:
    GPIO.cleanup()

if hd is True:
    print(header)
print(result)
with open(os.path.dirname(os.path.realpath(__file__))+'/run_data/'+now.strftime('%Y%m%d')+'.csv', 'a') as run_data:
    run_data.write(result+'\n')

# update cache
try:
    with open(os.path.dirname(os.path.realpath(__file__))+'/.cache') as cache_file:
        cache_list = deque(cache_file, 5)
except IOError:
    cache_list = deque()
cache_list.append(result+'\n')
logger.debug('current cache: %s', cache_list)

with open(os.path.dirname(os.path.realpath(__file__))+'/.cache', 'w') as cache_file:
    for line in cache_list:
        cache_file.write(line)

current_state = {}
cache_list.reverse()
i = 0
for heading in header.split(','):
    if heading == 'timestamp':
        i += 1
        continue
    for cache_item in cache_list:
        cache_val = cache_item.split(',')[i].strip()
        if cache_val == '0' or cache_val == '1':
            current_state[heading] = cache_val
            logger.debug('%s is %s at %s', heading, cache_val, cache_item.split(',')[0])
            break
    i += 1

with open(config['data_dir']+'/current_state.json', 'w') as out:
    json.dump(current_state, out)
