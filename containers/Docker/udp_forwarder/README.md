# UDP Forwarder

A Python script that receives UDP messages on one socket and forwards them to another UDP socket. Both source and destination IP addresses and ports are configurable via command line arguments.

## Features

- Configurable listening and forwarding IP addresses and ports
- Input validation for IP addresses and ports
- Message counting and logging
- Graceful shutdown with Ctrl+C
- Comprehensive error handling
- Test client included for easy testing

## Files

- `udp_forwarder.py` - Main UDP forwarder script
- `udp_test_client.py` - Test client for sending and receiving UDP messages
- `README.md` - This documentation

## Usage

### UDP Forwarder

```bash
python3 udp_forwarder.py --listen-ip <IP> --listen-port <PORT> --forward-ip <IP> --forward-port <PORT>
```

#### Required Arguments

- `--listen-port, -lp`: Port to listen on
- `--forward-ip, -fi`: IP address to forward messages to
- `--forward-port, -fp`: Port to forward messages to

#### Optional Arguments

- `--listen-ip, -li`: IP address to listen on (default: 0.0.0.0 - all interfaces)
- `--help, -h`: Show help message
- `--version, -v`: Show version information

#### Examples

```bash
# Listen on all interfaces port 8080, forward to localhost port 9090
python3 udp_forwarder.py --listen-port 8080 --forward-ip 127.0.0.1 --forward-port 9090

# Listen on specific interface, forward to remote server
python3 udp_forwarder.py --listen-ip 192.168.1.10 --listen-port 5000 --forward-ip 10.0.0.1 --forward-port 5001

# Using short argument names
python3 udp_forwarder.py -lp 8080 -fi 192.168.1.100 -fp 9090
```

### Test Client

The included test client can send messages or listen for forwarded messages:

#### Send Messages

```bash
python3 udp_test_client.py send --target-ip <IP> --target-port <PORT> [options]
```

Options:
- `--message`: Message to send (default: "Test message")
- `--count`: Number of messages to send (default: 5)
- `--interval`: Interval between messages in seconds (default: 1.0)

#### Listen for Messages

```bash
python3 udp_test_client.py listen --listen-port <PORT> [options]
```

Options:
- `--listen-ip`: IP to listen on (default: 0.0.0.0)
- `--timeout`: Timeout in seconds (default: 0 = no timeout)

## Testing Example

Here's a complete testing scenario:

1. **Terminal 1** - Start the listener (destination):
```bash
python3 udp_test_client.py listen --listen-port 9090
```

2. **Terminal 2** - Start the forwarder:
```bash
python3 udp_forwarder.py --listen-port 8080 --forward-ip 127.0.0.1 --forward-port 9090
```

3. **Terminal 3** - Send test messages:
```bash
python3 udp_test_client.py send --target-ip 127.0.0.1 --target-port 8080 --message "Hello World" --count 3
```

You should see:
- Terminal 3: Confirms messages are sent
- Terminal 2: Shows messages received and forwarded
- Terminal 1: Shows the forwarded messages

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Error Handling

The script includes comprehensive error handling for:
- Invalid IP addresses and ports
- Socket binding failures
- Network connectivity issues
- Graceful shutdown on interruption
- Prevention of forwarding loops

## Notes

- The script validates that the listening and forwarding sockets are not the same to prevent infinite loops
- Maximum UDP packet size is 65536 bytes
- The script listens on all interfaces (0.0.0.0) by default
- Use Ctrl+C to gracefully shutdown the forwarder
