#!/usr/bin/env python3
"""
UDP Test Client

This script can be used to test the UDP forwarder by sending test messages
or listening for forwarded messages.
"""

import argparse
import socket
import sys
import time
import threading


def udp_sender(target_ip: str, target_port: int, message: str, count: int, interval: float):
    """Send UDP messages to a target."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        print(f"Sending {count} messages to {target_ip}:{target_port}")
        print(f"Message: '{message}'")
        print(f"Interval: {interval} seconds")
        print()
        
        for i in range(count):
            msg = f"[{i+1}] {message}"
            sock.sendto(msg.encode('utf-8'), (target_ip, target_port))
            print(f"Sent: {msg}")
            
            if i < count - 1:  # Don't sleep after the last message
                time.sleep(interval)
        
        sock.close()
        print(f"\nCompleted sending {count} messages")
        
    except Exception as e:
        print(f"Error sending messages: {e}")


def udp_listener(listen_ip: str, listen_port: int, timeout: int):
    """Listen for UDP messages."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((listen_ip, listen_port))
        
        if timeout > 0:
            sock.settimeout(timeout)
        
        print(f"Listening for UDP messages on {listen_ip}:{listen_port}")
        if timeout > 0:
            print(f"Timeout: {timeout} seconds")
        print("Press Ctrl+C to stop")
        print()
        
        message_count = 0
        
        while True:
            try:
                data, addr = sock.recvfrom(65536)
                message_count += 1
                
                message = data.decode('utf-8', errors='replace')
                timestamp = time.strftime('%H:%M:%S')
                
                print(f"[{timestamp}] #{message_count} from {addr[0]}:{addr[1]}: {message}")
                
            except socket.timeout:
                print("Timeout reached, stopping listener")
                break
            except KeyboardInterrupt:
                print("\nStopping listener...")
                break
                
        sock.close()
        print(f"Received {message_count} messages total")
        
    except Exception as e:
        print(f"Error in listener: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="UDP Test Client - Send or receive UDP messages for testing the forwarder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send test messages
  python udp_test_client.py send --target-ip 127.0.0.1 --target-port 8080 --message "Hello" --count 5
  
  # Listen for messages
  python udp_test_client.py listen --listen-ip 0.0.0.0 --listen-port 9090 --timeout 30
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Sender mode
    send_parser = subparsers.add_parser('send', help='Send UDP messages')
    send_parser.add_argument('--target-ip', required=True, help='Target IP address')
    send_parser.add_argument('--target-port', type=int, required=True, help='Target port')
    send_parser.add_argument('--message', default='Test message', help='Message to send')
    send_parser.add_argument('--count', type=int, default=5, help='Number of messages to send')
    send_parser.add_argument('--interval', type=float, default=1.0, help='Interval between messages (seconds)')
    
    # Listener mode
    listen_parser = subparsers.add_parser('listen', help='Listen for UDP messages')
    listen_parser.add_argument('--listen-ip', default='0.0.0.0', help='IP to listen on')
    listen_parser.add_argument('--listen-port', type=int, required=True, help='Port to listen on')
    listen_parser.add_argument('--timeout', type=int, default=0, help='Timeout in seconds (0 = no timeout)')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    if args.mode == 'send':
        udp_sender(args.target_ip, args.target_port, args.message, args.count, args.interval)
    elif args.mode == 'listen':
        udp_listener(args.listen_ip, args.listen_port, args.timeout)


if __name__ == "__main__":
    main()
