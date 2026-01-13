#!/usr/bin/env python3
"""
UDP Message Forwarder

This script receives UDP messages on one socket and forwards them to another UDP socket.
The IP addresses and ports for both sockets are configurable via command line arguments.
"""

import argparse
import socket
import sys
import threading
import time
from typing import Tuple


class UDPForwarder:
    def __init__(self, listen_ip: str, listen_port: int, forward_ip: str, forward_port: int):
        """
        Initialize the UDP forwarder.
        
        Args:
            listen_ip: IP address to listen on
            listen_port: Port to listen on
            forward_ip: IP address to forward messages to
            forward_port: Port to forward messages to
        """
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.forward_ip = forward_ip
        self.forward_port = forward_port
        
        self.listen_socket = None
        self.forward_socket = None
        self.running = False
        
    def setup_sockets(self):
        """Set up the listening and forwarding sockets."""
        try:
            # Create listening socket
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listen_socket.bind((self.listen_ip, self.listen_port))
            
            # Create forwarding socket
            self.forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            print(f"Listening on {self.listen_ip}:{self.listen_port}", flush=True)
            print(f"Forwarding to {self.forward_ip}:{self.forward_port}", flush=True)
            
        except Exception as e:
            print(f"Error setting up sockets: {e}", flush=True)
            self.cleanup()
            sys.exit(1)
    
    def forward_messages(self):
        """Main message forwarding loop."""
        self.running = True
        message_count = 0
        
        try:
            while self.running:
                try:
                    # Receive message from listening socket
                    data, addr = self.listen_socket.recvfrom(65536)  # Max UDP packet size
                    
                    if not data:
                        continue
                    
                    message_count += 1
                    print(f"[{message_count}] Received {len(data)} bytes from {addr[0]}:{addr[1]}", flush=True)
                    
                    # Forward message to destination
                    self.forward_socket.sendto(data, (self.forward_ip, self.forward_port))
                    print(f"[{message_count}] Forwarded to {self.forward_ip}:{self.forward_port}", flush=True)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error forwarding message: {e}", flush=True)
                        
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, shutting down...", flush=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up sockets and resources."""
        self.running = False
        
        if self.listen_socket:
            try:
                self.listen_socket.close()
            except:
                pass
                
        if self.forward_socket:
            try:
                self.forward_socket.close()
            except:
                pass
        
        print("Cleanup completed")
    
    def start(self):
        """Start the UDP forwarder."""
        self.setup_sockets()
        
        try:
            self.forward_messages()
        except Exception as e:
            print(f"Unexpected error: {e}", flush=True)
            self.cleanup()


def validate_ip_or_hostname(host: str) -> str:
    """Validate IP address or hostname format."""
    try:
        # Try to resolve the hostname/IP to validate it
        socket.getaddrinfo(host, None)
        return host
    except socket.gaierror:
        raise argparse.ArgumentTypeError(f"Invalid IP address or hostname: {host}")


def validate_port(port: str) -> int:
    """Validate port number."""
    try:
        port_num = int(port)
        if not (1 <= port_num <= 65535):
            raise argparse.ArgumentTypeError(f"Port must be between 1 and 65535, got: {port_num}")
        return port_num
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid port number: {port}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="UDP Message Forwarder - Receives UDP messages and forwards them to another UDP socket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Forward from localhost:8080 to remote server
  python udp_forwarder.py --listen-ip 0.0.0.0 --listen-port 8080 --forward-ip 192.168.1.100 --forward-port 9090
  
  # Forward between specific interfaces
  python udp_forwarder.py -li 192.168.1.10 -lp 5000 -fi 10.0.0.1 -fp 5001
        """
    )
    
    # Listening socket configuration
    listen_group = parser.add_argument_group('Listening Socket Configuration')
    listen_group.add_argument(
        '--listen-ip', '-li',
        type=validate_ip_or_hostname,
        default='0.0.0.0',
        help='IP address or hostname to listen on (default: 0.0.0.0 - all interfaces)'
    )
    listen_group.add_argument(
        '--listen-port', '-lp',
        type=validate_port,
        required=True,
        help='Port to listen on (required)'
    )
    
    # Forwarding socket configuration
    forward_group = parser.add_argument_group('Forwarding Socket Configuration')
    forward_group.add_argument(
        '--forward-ip', '-fi',
        type=validate_ip_or_hostname,
        required=True,
        help='IP address or hostname to forward messages to (required)'
    )
    forward_group.add_argument(
        '--forward-port', '-fp',
        type=validate_port,
        required=True,
        help='Port to forward messages to (required)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='UDP Forwarder 1.0.0'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Validate that we're not creating a loop
    if (args.listen_ip == args.forward_ip or args.listen_ip == '0.0.0.0') and args.listen_port == args.forward_port:
        print("Error: Listen and forward sockets cannot be the same!", flush=True)
        sys.exit(1)
    
    print("UDP Message Forwarder starting...", flush=True)
    print(f"Configuration:", flush=True)
    print(f"  Listen:  {args.listen_ip}:{args.listen_port}", flush=True)
    print(f"  Forward: {args.forward_ip}:{args.forward_port}", flush=True)
    print(flush=True)
    
    # Create and start the forwarder
    forwarder = UDPForwarder(
        listen_ip=args.listen_ip,
        listen_port=args.listen_port,
        forward_ip=args.forward_ip,
        forward_port=args.forward_port
    )
    
    forwarder.start()


if __name__ == "__main__":
    main()
