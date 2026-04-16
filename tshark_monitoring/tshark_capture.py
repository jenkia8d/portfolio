#!/usr/bin/env python3


###################################################################################################################################
# Generate IPs 10.0.1.118 through 10.0.26.118
# sudo python tshark_capture.py --ip-seq "10.0.x.118,1,26" --port 443 --duration 60 --output-dir /home/powin/tsharkAudit/test/
#
# Still works with manual IP list
# sudo python tshark_capture.py --ips "192.168.1.1,192.168.1.2" --port 80 --duration 30 --output-dir /home/powin/tsharkAudit/test/
###################################################################################################################################


import subprocess
import datetime
import tarfile
import os
import sys
import threading
import argparse


def capture_packets(ip, port, duration, output_dir):
    """Capture packets for a single IP address"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ip_formatted = ip.replace('.', '_')
    pcap_filename = "{}_{}.pcap".format(timestamp, ip_formatted)
    pcap_path = os.path.join(output_dir, pcap_filename)
    
    # Build tshark command
    cmd = [
        'tshark',
        '-i', 'any',  # Capture on all interfaces
        '-f', 'host {}'.format(ip) if port is None else 'host {} and port {}'.format(ip, port),
        '-a', 'duration:{}'.format(duration),
        '-w', pcap_path
    ]
    
    port_str = 'all ports' if port is None else port
    print("Starting capture for {}:{} -> {}".format(ip, port_str, pcap_filename))
    print("Command: {}".format(' '.join(cmd)))
    
    try:
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.communicate()
        result.stdout = stdout.decode('utf-8') if stdout else ''
        result.stderr = stderr.decode('utf-8') if stderr else ''
        print("Return code for {}: {}".format(ip, result.returncode))
        if result.stdout:
            print("Stdout for {}: {}".format(ip, result.stdout))
        if result.stderr:
            print("Stderr for {}: {}".format(ip, result.stderr))
        
        if result.returncode == 0:
            print("Capture completed: {}".format(pcap_filename))
            return pcap_path
        else:
            print("Error capturing {}: return code {}".format(ip, result.returncode))
            return None
    except subprocess.TimeoutExpired:
        print("Timeout capturing {}".format(ip))
        return None
    except Exception as e:
        print("Exception capturing {}: {}".format(ip, e))
        return None

def compress_pcap(pcap_path):
    """Compress a single pcap file to tar.gz"""
    if not pcap_path or not os.path.exists(pcap_path):
        return None
        
    tar_path = pcap_path.replace('.pcap', '.tar.gz')
    
    try:
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(pcap_path, arcname=os.path.basename(pcap_path))
        
        # Remove original pcap file
        os.remove(pcap_path)
        print("Compressed: {}".format(os.path.basename(tar_path)))
        return tar_path
    except Exception as e:
        print("Error compressing {}: {}".format(pcap_path, e))
        return None

def generate_sequential_ips(pattern, start, end):
    """Generate sequential IPs from pattern like 10.0.x.118"""
    return [pattern.replace('x', str(i)) for i in range(start, end + 1)]

def main():
    print("Script starting...")
    parser = argparse.ArgumentParser(description='Automated tshark packet capture')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ips', help='Comma-separated IP addresses')
    group.add_argument('--ip-seq', help='Sequential IPs: pattern,start,end (e.g., 10.0.x.118,1,26)')
    parser.add_argument('--port', type=int, help='Port to capture (optional - captures all traffic if not specified)')
    parser.add_argument('--duration', type=int, default=60, help='Capture duration in seconds (default: 60)')
    parser.add_argument('--output-dir', default='.', help='Output directory (default: current)')
    
    print("Parsing arguments...")
    args = parser.parse_args()
    print("Arguments parsed: {}".format(args))
    
    # Parse IP addresses
    if args.ips:
        ip_list = [ip.strip() for ip in args.ips.split(',')]
    else:
        parts = args.ip_seq.split(',')
        pattern, start, end = parts[0], int(parts[1]), int(parts[2])
        ip_list = generate_sequential_ips(pattern, start, end)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    print("Target IPs:")
    for ip in ip_list:
        print("  {}".format(ip))
    port_str = 'all ports' if args.port is None else args.port
    print("Starting parallel captures for {} IPs on {} for {}s".format(len(ip_list), port_str, args.duration))
    
    # Parallel execution using threading
    threads = []
    pcap_files = [None] * len(ip_list)
    
    def capture_wrapper(index, ip):
        pcap_files[index] = capture_packets(ip, args.port, args.duration, args.output_dir)
    
    for i, ip in enumerate(ip_list):
        thread = threading.Thread(target=capture_wrapper, args=(i, ip))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Compress all pcap files
    print("\nCompressing pcap files...")
    for pcap_file in pcap_files:
        if pcap_file:
            compress_pcap(pcap_file)
    
    print("All captures completed!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Script failed with error: {}".format(e))
        import traceback
        traceback.print_exc()