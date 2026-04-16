#!/bin/bash

### Edit Crontab:
### sudo EDITOR=nano crontab -e
### Example crontab:
### */5 * * * * /home/powin/SEscripts/tshark_gap_check.sh > /home/powin/tsharkAudit/tshark_gap_check.log 2>&1

DEFAULT_DURATION=300
hostDEVICE=10.1.2
PORT=502
fileNameBase=tsharkCapture
outDir='/home/powin/tsharkAudit/'
deleteAfterDays=5
GAP_THRESHOLD=0.75  # Gap threshold in seconds
PERFORM_GAP_CHECK=true  # Set to false to skip gap analysis

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

# Wait for tshark to fully complete file writing
sleep 2

tar cvzf ${fileName}_DEVICE.tar.gz ${fileName}_DEVICE.pcap
chown powin:powin ${fileName}_DEVICE.tar.gz
rm ${fileName}_DEVICE.pcap

# Quick gap check using tshark
if [ "$PERFORM_GAP_CHECK" = "true" ]; then
echo "DEBUG: Starting gap check analysis"
# Ensure gap_alerts.log exists and is writable
if [ ! -f "${outDir}gap_alerts.log" ]; then
    touch ${outDir}gap_alerts.log
    chown powin:powin ${outDir}gap_alerts.log
fi
tempDir=$(mktemp -d)
echo "DEBUG: Created temp directory: $tempDir"
tar -xzf "${fileName}_DEVICE.tar.gz" -C "$tempDir"
pcapFile=$(find "$tempDir" -name "*.pcap" | head -1)
echo "DEBUG: Found pcap file: $pcapFile"

if [ -f "$pcapFile" ]; then
    echo "DEBUG: Checking file integrity"
    if ! tshark -r "$pcapFile" -c 1 >/dev/null 2>&1; then
        echo "FILE_CORRUPT"
        echo "Error: Pcap file is corrupt or unreadable"
    else
        echo "DEBUG: Extracting timestamps with threshold: $GAP_THRESHOLD seconds"
        # Extract timestamps and check for gaps
        gap_result=$(tshark -r "$pcapFile" -T fields -e frame.time_epoch | sort -n | awk -v threshold=$GAP_THRESHOLD '
    BEGIN { gap_found = 0 }
    NR > 1 {
        gap = $1 - prev
        if (gap > threshold) {
            print "GAP_DETECTED: " gap "s gap between " prev " and " $1
            gap_found = 1
            exit 1
        }
    }
    { prev = $1 }
    END { 
        if (gap_found == 0) {
            if (NR > 1) {
                print "NO_GAPS"
            } else if (NR == 1) {
                print "SINGLE_PACKET"
            } else {
                print "NO_PACKETS"
            }
        }
    }' 2>&1)
    
    awk_exit_code=$?
    echo "DEBUG: Gap analysis result: $gap_result"
    echo "$gap_result"
    
    # Check for AWK errors
    if [[ $awk_exit_code -ne 0 && "$gap_result" != *"GAP_DETECTED"* ]]; then
        echo "ERROR: AWK processing failed: $gap_result"
    fi
    
    if [[ "$gap_result" == GAP_DETECTED* ]]; then
        # Extract timestamps and convert to readable format
        start_epoch=$(echo "$gap_result" | grep -o 'between [0-9.]*' | cut -d' ' -f2 | cut -d'.' -f1)
        end_epoch=$(echo "$gap_result" | grep -o 'and [0-9.]*' | cut -d' ' -f2 | cut -d'.' -f1)
        start_time=$(date -d @$start_epoch '+%Y-%m-%d %H:%M:%S')
        end_time=$(date -d @$end_epoch '+%Y-%m-%d %H:%M:%S')
        duration=$(echo "$gap_result" | grep -o '[0-9.]*s gap' | cut -d's' -f1)
        echo "${start_time}: ${duration}s gap until ${end_time} in ${fileName}_DEVICE.tar.gz" >> ${outDir}gap_alerts.log
        chown powin:powin ${outDir}gap_alerts.log
    else
        echo "No gaps detected"
    fi
    fi
else
    echo "DEBUG: No pcap file found in archive"
    echo "Warning: No pcap file found in archive"
fi

echo "DEBUG: Cleaning up temp directory: $tempDir"
rm -rf "$tempDir"
else
echo "DEBUG: Gap check skipped (PERFORM_GAP_CHECK=false)"
fi

find ${outDir} -name "*.tar.gz" -type f -mtime +$deleteAfterDays | xargs -I FILE rm FILE
find ${outDir} -name "*.tar.gz" -type f -mtime $deleteAfterDays | xargs -I FILE rm FILE


