#!/bin/bash

### Edit Crontab:
### sudo EDITOR=nano crontab -e
### Example crontab:
### */5 * * * * /home/powin/SEscripts/tshark_monitoring.sh > /home/powin/tsharkAudit/tshark_monitoring.log 2>&1

DEFAULT_DURATION=300
hostDEVICE=10.0.0.XX
PORT=XXXX
fileNameBase=tsharkCapture
outDir='/home/powin/tsharkAudit/'
deleteAfterDays=5

if [ ! -d ${outDir} ]; then
 mkdir ${outDir}
fi

now=$(date +"%Y%m%d_%H%M")
fileName=${outDir}$fileNameBase${now}

if [ -n "$1" ]; then
    captureDuration=$1
else
    captureDuration=$DEFAULT_DURATION
fi

touch ${fileName}_DEVICE.pcap 
tshark -i any -f "host $hostDEVICE and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE.pcap -F pcap

tar cvzf ${fileName}_DEVICE.tar.gz ${fileName}_DEVICE.pcap
chown powin:powin ${fileName}_DEVICE.tar.gz
rm ${fileName}_DEVICE.pcap

find ${outDir} -name "*.tar.gz" -type f -mtime +$deleteAfterDays | xargs -I FILE rm FILE
find ${outDir} -name "*.tar.gz" -type f -mtime $deleteAfterDays | xargs -I FILE rm FILE