# Tshark Gap Analyzer

Analyzes tshark capture files for message gaps to identify communication interruptions and device response patterns.

## Features

- **Gap Detection**: Identifies communication interruptions above configurable threshold
- **Device Analysis**: Tracks non-EMS device communication patterns around gaps
- **Response Detection**: Checks if device messages receive responses within 5 seconds
- **Chronological Display**: Shows packet sequence (Non-EMS Before → EMS Before → EMS After → Non-EMS After)
- **Precise Timing**: Displays durations with millisecond precision (3 decimal places)
- **Configurable EMS IP**: Supports custom EMS IP addresses

## Dependencies

- **Python 3** (no external packages required)
- Works with or without tshark (falls back to built-in pcap parsing)

## Usage

```bash
# Basic usage with default settings (1.0s threshold, EMS IP 10.0.0.3)
python tshark_gap_analyzer_python.py "/path/tsharkCapture*_DEVICE.tar.gz"

# Custom threshold (0.5 seconds)
python tshark_gap_analyzer_python.py "/path/tsharkCapture*_DEVICE.tar.gz" --threshold 0.5

# Custom EMS IP address (for non-standard EMS configurations)
python tshark_gap_analyzer_python.py "/path/tsharkCapture*_DEVICE.tar.gz" --ems-ip 10.1.0.3

# Combined options
python tshark_gap_analyzer_python.py "/path/tsharkCapture*_DEVICE.tar.gz" -t 0.8 --ems-ip 10.1.0.3
```

## Parameters

- `--threshold` or `-t`: Gap threshold in seconds (default: 1.0)
- `--ems-ip`: EMS IP address to exclude from device analysis (default: 10.0.0.3)
  - The script identifies "Non-EMS" messages as any packets NOT originating from this IP
  - Use this parameter when your EMS uses a non-standard IP address
  - Example: If your EMS is at 10.1.0.3, use `--ems-ip 10.1.0.3`

## Output Example

```
Analyzing 3 files with gap threshold: 1.000s
------------------------------------------------------------

tsharkCapture20250913_1452_DEVICE.tar.gz:
  Gap: 1.899s from 2025-09-13 14:52:15.848 UTC to 2025-09-13 14:52:17.747 UTC
    Non-EMS Before:           14:52:15.793 UTC        SRC=10.1.2.5:502        DST=10.1.0.3:51584      Protocol=TCP     Len=109      [Answered]
    EMS Before:               14:52:15.848 UTC        SRC=10.1.0.3:55852      DST=10.1.2.12:502       Protocol=TCP     Len=68
    EMS After:                14:52:17.747 UTC        SRC=10.1.0.3:41088      DST=10.1.2.15:502       Protocol=TCP     Len=80
    Non-EMS After:            14:52:17.766 UTC        SRC=10.1.2.5:502        DST=10.1.0.3:51584      Protocol=TCP     Len=80       [No Response]
    --------------------------------------------------------------------------------
    EMS Silence:              1.899s
    Device Interval:          1.973s

Total gaps found: 1
```

## Output Fields

- **Gap**: Duration and time range of the communication interruption
- **Non-EMS Before**: Last message from device before the gap
- **EMS Before**: Last EMS message before the gap
- **EMS After**: First EMS message after the gap
- **Non-EMS After**: First device message after the gap
- **[Answered/No Response]**: Whether device messages received responses
- **EMS Silence**: Duration of EMS communication gap
- **Device Interval**: Time between device's last and first messages

The script automatically extracts .tar.gz files and analyzes the .pcap files inside using built-in Python pcap parsing.