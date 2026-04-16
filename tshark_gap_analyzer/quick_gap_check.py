#!/usr/bin/env python3

import os
import sys
import glob
import tarfile
import tempfile
import struct

def read_pcap_timestamps(pcap_file):
    """Extract only timestamps from pcap file"""
    timestamps = []
    try:
        with open(pcap_file, 'rb') as f:
            header = f.read(24)
            if len(header) < 24:
                return []
            
            magic = struct.unpack('<I', header[:4])[0]
            endian = '<' if magic == 0xa1b2c3d4 else '>'
            
            while True:
                packet_header = f.read(16)
                if len(packet_header) < 16:
                    break
                
                ts_sec, ts_usec, caplen, wirelen = struct.unpack(f'{endian}IIII', packet_header)
                timestamps.append(ts_sec + ts_usec / 1000000.0)
                
                if caplen > 0:
                    f.seek(caplen, 1)
        
        return sorted(timestamps)
    except:
        return []

def check_gaps(tar_path, threshold):
    """Check if any gaps exceed threshold"""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(temp_dir, filter='data')
            
            pcap_files = glob.glob(os.path.join(temp_dir, '**', '*.pcap'), recursive=True)
            if not pcap_files:
                return False
            
            timestamps = read_pcap_timestamps(pcap_files[0])
            
            for i in range(1, len(timestamps)):
                if timestamps[i] - timestamps[i-1] > threshold:
                    return True
            
            return False
        except:
            return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 quick_gap_check.py <file.tar.gz> <threshold>")
        sys.exit(1)
    
    tar_file = sys.argv[1]
    threshold = float(sys.argv[2])
    
    if check_gaps(tar_file, threshold):
        print("GAPS_DETECTED")
        sys.exit(1)
    else:
        print("NO_GAPS")
        sys.exit(0)