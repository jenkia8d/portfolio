#!/usr/bin/env python3

import os
import glob
import tarfile
import tempfile
import argparse
import struct
import socket
from datetime import datetime, timezone

def read_pcap_packets(pcap_file):
    """Read packet info from pcap file"""
    packets = []
    try:
        with open(pcap_file, 'rb') as f:
            # Read pcap header
            header = f.read(24)
            if len(header) < 24:
                return []
            
            # Check magic number for endianness
            magic = struct.unpack('<I', header[:4])[0]
            if magic == 0xa1b2c3d4:
                endian = '<'  # little endian
            elif magic == 0xd4c3b2a1:
                endian = '>'  # big endian  
            else:
                return []
            
            # Read packets
            while True:
                packet_header = f.read(16)
                if len(packet_header) < 16:
                    break
                
                # Extract timestamp and length
                ts_sec, ts_usec, caplen, wirelen = struct.unpack(f'{endian}IIII', packet_header)
                timestamp = ts_sec + ts_usec / 1000000.0
                
                # Read packet data
                packet_data = f.read(caplen)
                if len(packet_data) < caplen:
                    break
                
                # Parse basic packet info
                src_ip, dst_ip, protocol = parse_packet(packet_data)
                
                packets.append({
                    'timestamp': timestamp,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'protocol': protocol,
                    'length': wirelen
                })
        
        print(f"Extracted {len(packets)} packets from {os.path.basename(pcap_file)}")
        return packets
    except Exception as e:
        print(f"Error reading pcap: {e}")
        return []

def parse_packet(packet_data):
    """Parse basic packet info (IP addresses and protocol)"""
    try:
        if len(packet_data) < 16:
            return "Unknown", "Unknown", "Unknown"
        
        # Check for Linux cooked capture (SLL) - protocol at bytes 14-15
        protocol = struct.unpack('!H', packet_data[14:16])[0]
        
        if protocol == 0x0800:  # IPv4
            # IP header starts at byte 16 for Linux cooked capture
            ip_start = 16
            if len(packet_data) < ip_start + 20:
                return "Unknown", "Unknown", "Unknown"
            
            # Extract IP header fields
            ip_protocol = packet_data[ip_start + 9]
            src_ip_bytes = packet_data[ip_start + 12:ip_start + 16]
            dst_ip_bytes = packet_data[ip_start + 16:ip_start + 20]
            
            # Convert to dotted decimal
            src_ip = '.'.join(str(b) for b in src_ip_bytes)
            dst_ip = '.'.join(str(b) for b in dst_ip_bytes)
            
            # Protocol names
            protocol_names = {1: 'ICMP', 6: 'TCP', 17: 'UDP', 2: 'IGMP'}
            protocol_name = protocol_names.get(ip_protocol, f'Protocol-{ip_protocol}')
            
            # Add port info to IP addresses for TCP/UDP
            if ip_protocol in [6, 17] and len(packet_data) >= ip_start + 24:
                src_port = struct.unpack('!H', packet_data[ip_start + 20:ip_start + 22])[0]
                dst_port = struct.unpack('!H', packet_data[ip_start + 22:ip_start + 24])[0]
                src_ip += f':{src_port}'
                dst_ip += f':{dst_port}'
            
            return src_ip, dst_ip, protocol_name
        else:
            return "Non-IPv4", "Non-IPv4", f"Proto-{protocol:04x}"
            
    except Exception as e:
        return "Parse-Error", "Parse-Error", "Parse-Error"

def check_response(packet, packets, start_idx, window_seconds=5):
    """Check if a packet gets a response within the time window"""
    src_ip = packet['src_ip'].split(':')[0]
    dst_ip = packet['dst_ip'].split(':')[0]
    
    # Look for response from dst back to src within time window
    for j in range(start_idx, len(packets)):
        if packets[j]['timestamp'] - packet['timestamp'] > window_seconds:
            break
        if (packets[j]['src_ip'].split(':')[0] == dst_ip and 
            packets[j]['dst_ip'].split(':')[0] == src_ip):
            return True
    return False

def find_gaps(packets, threshold, ems_ip):
    """Find gaps larger than threshold seconds"""
    gaps = []
    for i in range(1, len(packets)):
        gap = packets[i]['timestamp'] - packets[i-1]['timestamp']
        if gap > threshold:
            # Find first non-EMS message after gap
            first_non_target = None
            first_idx = None
            for j in range(i, len(packets)):
                if not packets[j]['src_ip'].startswith(ems_ip):
                    first_non_target = packets[j]
                    first_idx = j
                    break
            
            # Find last message from that IP before gap
            last_from_ip = None
            last_idx = None
            if first_non_target:
                target_ip = first_non_target['src_ip'].split(':')[0]  # Remove port if present
                for j in range(i-1, -1, -1):
                    if packets[j]['src_ip'].split(':')[0] == target_ip:
                        last_from_ip = packets[j]
                        last_idx = j
                        break
            
            # Check if messages are answered
            last_answered = check_response(last_from_ip, packets, last_idx + 1) if last_from_ip else None
            first_answered = check_response(first_non_target, packets, first_idx + 1) if first_non_target else None
            
            gaps.append({
                'start_time': datetime.fromtimestamp(packets[i-1]['timestamp'], tz=timezone.utc),
                'end_time': datetime.fromtimestamp(packets[i]['timestamp'], tz=timezone.utc),
                'duration': gap,
                'before_packet': packets[i-1],
                'after_packet': packets[i],
                'first_non_target': first_non_target,
                'last_from_ip': last_from_ip,
                'last_answered': last_answered,
                'first_answered': first_answered
            })
    return gaps

def analyze_file(tar_path, threshold, ems_ip):
    """Analyze a single tar.gz file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            print(f"Extracting {os.path.basename(tar_path)}...")
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(temp_dir, filter='data')
            
            pcap_files = glob.glob(os.path.join(temp_dir, '**', '*.pcap'), recursive=True)
            if not pcap_files:
                pcap_files = glob.glob(os.path.join(temp_dir, '**', '*.cap'), recursive=True)
            
            if not pcap_files:
                print("No pcap files found in archive")
                return []
            
            packets = read_pcap_packets(pcap_files[0])
            return find_gaps(packets, threshold, ems_ip)
        except Exception as e:
            print(f"Error analyzing file: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description='Analyze tshark captures for message gaps')
    parser.add_argument('pattern', help='File pattern (e.g., /path/tsharkCapture202509*_DEVICE.tar.gz)')
    parser.add_argument('--threshold', '-t', type=float, default=1.0, 
                       help='Gap threshold in seconds (default: 1.0)')
    parser.add_argument('--ems-ip', type=str, default='10.0.0.3',
                       help='EMS IP address to exclude (default: 10.0.0.3)')
    
    args = parser.parse_args()
    
    files = sorted(glob.glob(args.pattern))
    
    if not files:
        print(f"No files found matching pattern: {args.pattern}")
        return
    
    print(f"Analyzing {len(files)} files with gap threshold: {args.threshold}s")
    print("-" * 60)
    
    total_gaps = 0
    for file_path in files:
        filename = os.path.basename(file_path)
        gaps = analyze_file(file_path, args.threshold, args.ems_ip)
        
        if gaps:
            print(f"\n{filename}:")
            for gap in gaps:
                print(f"  Gap: {gap['duration']:.3f}s from {gap['start_time'].strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]} to {gap['end_time'].strftime('%Y-%m-%d %H:%M:%S.%f UTC')[:-3]}")
                
                before = gap['before_packet']
                after = gap['after_packet']
                before_time = datetime.fromtimestamp(gap['before_packet']['timestamp'], tz=timezone.utc).strftime('%H:%M:%S.%f')[:-3]
                after_time = datetime.fromtimestamp(gap['after_packet']['timestamp'], tz=timezone.utc).strftime('%H:%M:%S.%f')[:-3]
                
                if gap['first_non_target'] and gap['last_from_ip']:
                    last = gap['last_from_ip']
                    first = gap['first_non_target']
                    last_time = datetime.fromtimestamp(last['timestamp'], tz=timezone.utc).strftime('%H:%M:%S.%f')[:-3]
                    first_time = datetime.fromtimestamp(first['timestamp'], tz=timezone.utc).strftime('%H:%M:%S.%f')[:-3]
                    duration = first['timestamp'] - last['timestamp']
                    
                    last_status = "Answered" if gap['last_answered'] else "No Response"
                    first_status = "Answered" if gap['first_answered'] else "No Response"
                    
                    print(f"    {'Non-EMS Before:':<25} {last_time} UTC        SRC={last['src_ip']:<20} DST={last['dst_ip']:<20} Protocol={last['protocol']:<8} Len={last['length']:<8} [{last_status}]")
                    print(f"    {'EMS Before:':<25} {before_time} UTC        SRC={before['src_ip']:<20} DST={before['dst_ip']:<20} Protocol={before['protocol']:<8} Len={before['length']}")
                    print(f"    {'EMS After:':<25} {after_time} UTC        SRC={after['src_ip']:<20} DST={after['dst_ip']:<20} Protocol={after['protocol']:<8} Len={after['length']}")
                    print(f"    {'Non-EMS After:':<25} {first_time} UTC        SRC={first['src_ip']:<20} DST={first['dst_ip']:<20} Protocol={first['protocol']:<8} Len={first['length']:<8} [{first_status}]")
                    print("    " + "-" * 80)
                    print(f"    {'EMS Silence:':<25} {gap['duration']:.3f}s")
                    print(f"    {'Device Interval:':<25} {duration:.3f}s")
                elif gap['first_non_target']:
                    first = gap['first_non_target']
                    first_time = datetime.fromtimestamp(first['timestamp'], tz=timezone.utc).strftime('%H:%M:%S.%f')[:-3]
                    
                    first_status = "Answered" if gap['first_answered'] else "No Response"
                    
                    print(f"    {'EMS Before:':<25} {before_time} UTC        SRC={before['src_ip']:<20} DST={before['dst_ip']:<20} Protocol={before['protocol']:<8} Len={before['length']}")
                    print(f"    {'EMS After:':<25} {after_time} UTC        SRC={after['src_ip']:<20} DST={after['dst_ip']:<20} Protocol={after['protocol']:<8} Len={after['length']}")
                    print(f"    {'Non-EMS After:':<25} {first_time} UTC        SRC={first['src_ip']:<20} DST={first['dst_ip']:<20} Protocol={first['protocol']:<8} Len={first['length']:<8} [{first_status}]")
                    print(f"    No previous message from {first['src_ip'].split(':')[0]} found before gap")
                    print("    " + "-" * 80)
                    print(f"    {'EMS Silence:':<25} {gap['duration']:.3f}s")
                    print(f"    {'Device Interval:':<25} N/A")
                else:
                    print(f"    {'EMS Before:':<25} {before_time} UTC        SRC={before['src_ip']:<20} DST={before['dst_ip']:<20} Protocol={before['protocol']:<8} Len={before['length']}")
                    print(f"    {'EMS After:':<25} {after_time} UTC        SRC={after['src_ip']:<20} DST={after['dst_ip']:<20} Protocol={after['protocol']:<8} Len={after['length']}")
                    print(f"    No non-{args.ems_ip} messages found after gap")
                    print("    " + "-" * 80)
                    print(f"    {'EMS Silence:':<25} {gap['duration']:.3f}s")
                    print(f"    {'Device Interval:':<25} N/A")
            total_gaps += len(gaps)
        else:
            print(f"{filename}: No gaps found")
        print()  # Blank line between files
    
    print(f"\nTotal gaps found: {total_gaps}")

if __name__ == '__main__':
    main()