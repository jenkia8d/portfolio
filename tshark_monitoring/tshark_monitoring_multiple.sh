#!/bin/bash

### Edit Crontab:
### sudo EDITOR=nano crontab -e
### Example crontab:
### */5 * * * * /home/powin/SEscripts/tshark_monitoring.sh > /home/powin/tsharkAudit/tshark_monitoring.log 2>&1

captureDuration=300
hostDEVICE1=10.0.X.XX
hostDEVICE2=10.0.X.XX
hostDEVICE3=10.0.X.XX
hostDEVICE4=10.0.X.XX
hostDEVICE5=10.0.X.XX
hostDEVICE6=10.0.X.XX
hostDEVICE7=10.0.X.XX
hostDEVICE8=10.0.X.XX
hostDEVICE9=10.0.X.XX
hostDEVICE10=10.0.X.XX
PORT=8080
fileNameBase=tsharkCapture
outDir='/home/powin/tsharkAudit/'
deleteAfterDays=5

if [ ! -d ${outDir} ]; then
 mkdir ${outDir}
fi

now=$(date +"%Y%m%d_%H%M")
fileName=${outDir}$fileNameBase${now}


touch ${fileName}_DEVICE1.pcap & touch ${fileName}_DEVICE2.pcap & touch ${fileName}_DEVICE3.pcap & touch ${fileName}_DEVICE4.pcap & touch ${fileName}_DEVICE5.pcap & touch ${fileName}_DEVICE6.pcap & touch ${fileName}_DEVICE7.pcap & touch ${fileName}_DEVICE8.pcap & touch ${fileName}_DEVICE9.pcap & touch ${fileName}_DEVICE10.pcap
tshark -f "host $hostDEVICE1 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE1.pcap -F pcap & tshark -f "host $hostDEVICE2 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE2.pcap -F pcap & tshark -f "host $hostDEVICE3 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE3.pcap -F pcap & tshark -f "host $hostDEVICE4 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE4.pcap -F pcap & tshark -f "host $hostDEVICE5 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE5.pcap -F pcap & tshark -f "host $hostDEVICE6 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE6.pcap -F pcap & tshark -f "host $hostDEVICE7 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE7.pcap -F pcap & tshark -f "host $hostDEVICE8 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE8.pcap -F pcap & tshark -f "host $hostDEVICE9 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE9.pcap -F pcap & tshark -f "host $hostDEVICE10 and port $PORT" -a duration:$captureDuration -w ${fileName}_DEVICE10.pcap -F pcap

tar cvzf ${fileName}_DEVICE1.tar.gz ${fileName}_DEVICE1.pcap
chown powin:powin ${fileName}_DEVICE1.tar.gz
rm ${fileName}_DEVICE1.pcap

tar cvzf ${fileName}_DEVICE2.tar.gz ${fileName}_DEVICE2.pcap
chown powin:powin ${fileName}_DEVICE2.tar.gz
rm ${fileName}_DEVICE2.pcap

tar cvzf ${fileName}_DEVICE3.tar.gz ${fileName}_DEVICE3.pcap
chown powin:powin ${fileName}_DEVICE3.tar.gz
rm ${fileName}_DEVICE3.pcap

tar cvzf ${fileName}_DEVICE4.tar.gz ${fileName}_DEVICE4.pcap
chown powin:powin ${fileName}_DEVICE4.tar.gz
rm ${fileName}_DEVICE4.pcap

tar cvzf ${fileName}_DEVICE5.tar.gz ${fileName}_DEVICE5.pcap
chown powin:powin ${fileName}_DEVICE5.tar.gz
rm ${fileName}_DEVICE5.pcap

tar cvzf ${fileName}_DEVICE6.tar.gz ${fileName}_DEVICE6.pcap
chown powin:powin ${fileName}_DEVICE6.tar.gz
rm ${fileName}_DEVICE6.pcap

tar cvzf ${fileName}_DEVICE7.tar.gz ${fileName}_DEVICE7.pcap
chown powin:powin ${fileName}_DEVICE7.tar.gz
rm ${fileName}_DEVICE7.pcap

tar cvzf ${fileName}_DEVICE8.tar.gz ${fileName}_DEVICE8.pcap
chown powin:powin ${fileName}_DEVICE8.tar.gz
rm ${fileName}_DEVICE8.pcap

tar cvzf ${fileName}_DEVICE9.tar.gz ${fileName}_DEVICE9.pcap
chown powin:powin ${fileName}_DEVICE9.tar.gz
rm ${fileName}_DEVICE9.pcap

tar cvzf ${fileName}_DEVICE10.tar.gz ${fileName}_DEVICE10.pcap
chown powin:powin ${fileName}_DEVICE10.tar.gz
rm ${fileName}_DEVICE10.pcap

# find ${outDir} -name "*.tar.gz" -type f -mtime +$deleteAfterDays | xargs -I FILE rm FILE
# find ${outDir} -name "*.tar.gz" -type f -mtime $deleteAfterDays | xargs -I FILE rm FILE


