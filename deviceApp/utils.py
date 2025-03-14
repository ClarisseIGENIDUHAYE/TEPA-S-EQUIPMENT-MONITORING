import socket
import subprocess
import platform
from datetime import datetime

# utils.py
import socket
import subprocess
import platform
import time
import re
import statistics
from datetime import datetime

def is_valid_ipv4(ip):
    """Validate if the given string is a valid IPv4 address."""
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    match = re.match(pattern, ip)
    
    if not match:
        return False
    
    # Check that each octet is between 0 and 255
    for octet in match.groups():
        if int(octet) > 255:
            return False
    
    return True

def measure_ping_latency(ip_address, count=1, timeout=5, retry_count=2):
    """
    Measure ping latency to the specified IP address with retry mechanism.
    
    Parameters:
    - ip_address: IP to ping
    - count: Number of pings to send
    - timeout: Timeout in seconds
    - retry_count: Number of retries if ping fails
    
    Returns a dictionary with latency in milliseconds.
    """
    result = {
        'latency_ms': None,
        'error': None,
        'packet_loss': None
    }
    
    if not is_valid_ipv4(ip_address):
        result['error'] = "Invalid IP address format"
        return result
    
    # Try multiple times if needed
    for attempt in range(retry_count + 1):
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
            timeout_value = str(timeout * 1000) if platform.system().lower() == 'windows' else str(timeout)
            
            command = ['ping', param, str(count), timeout_param, timeout_value, ip_address]
            
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=timeout + 5)  # Add buffer time
            stdout_str = stdout.decode(errors='ignore')
            
            # Check for packet loss
            if platform.system().lower() == 'windows':
                loss_pattern = r'(\d+)% loss'
                loss_match = re.search(loss_pattern, stdout_str)
                if loss_match:
                    result['packet_loss'] = int(loss_match.group(1))
            else:
                loss_pattern = r'(\d+)% packet loss'
                loss_match = re.search(loss_pattern, stdout_str)
                if loss_match:
                    result['packet_loss'] = int(loss_match.group(1))
            
            # Check if device is reachable first (look for reply indicators)
            if platform.system().lower() == 'windows':
                if "Reply from" in stdout_str:
                    # Device is reachable, now extract time
                    time_pattern = r'time[=<](\d+\.?\d*)ms'
                    time_matches = re.findall(time_pattern, stdout_str)
                    
                    if time_matches:
                        # Calculate average of all responses
                        latencies = []
                        for match in time_matches:
                            latencies.append(float(match))
                        result['latency_ms'] = sum(latencies) / len(latencies)
                        # Success, break retry loop
                        break
                    elif "time<1ms" in stdout_str:
                        # Special case for very fast responses
                        result['latency_ms'] = 0.5  # Approximate as 0.5ms
                        break
                    else:
                        result['error'] = "Could not parse ping time from output"
                else:
                    result['error'] = "No reply received from host"
            else:
                # Unix format: "64 bytes from 8.8.8.8: icmp_seq=1 ttl=115 time=14.6 ms"
                if "bytes from" in stdout_str:
                    pattern = r'time=(\d+\.?\d*)\s*ms'
                    times = re.findall(pattern, stdout_str)
                    
                    if times:
                        # Calculate average of all responses
                        latencies = [float(t) for t in times]
                        result['latency_ms'] = sum(latencies) / len(latencies)
                        break
                    else:
                        result['error'] = "Could not parse ping time from output"
                else:
                    result['error'] = "No reply received from host"
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            result['error'] = f"Ping error: {str(e)}"
        except Exception as e:
            result['error'] = f"Error: {str(e)}"
        
        # If we reach here and it's not the last attempt, try again
        if attempt < retry_count:
            time.sleep(1)  # Wait a bit before retrying
        
    return result

def check_device_connectivity(ip_address, location="unknown", ping_count=3, timeout=5, retry_count=2):
    """
    Check if a device is reachable and measure its network latency.
    
    Parameters:
    - ip_address: IP to check
    - location: Description of the device location
    - ping_count: Number of pings to send
    - timeout: Timeout in seconds
    - retry_count: Number of retries if ping fails
    
    Returns a dictionary with connectivity status and network metrics.
    """
    result = {
        'ip': ip_address,
        'status': 'offline',
        'timestamp': datetime.now().isoformat(),
        'latency_ms': None,
        'packet_loss': None,
        'error': None,
        'location': location
    }
    
    # Validate IP address
    if not is_valid_ipv4(ip_address):
        result['error'] = "Invalid IP address format"
        return result
    
    # Try to ping the device
    ping_result = measure_ping_latency(
        ip_address,
        count=ping_count,
        timeout=timeout,
        retry_count=retry_count
    )
    
    if ping_result['latency_ms'] is not None:
        result['status'] = 'online'
        result['latency_ms'] = ping_result['latency_ms']
        result['packet_loss'] = ping_result['packet_loss']
    else:
        result['error'] = ping_result['error']
        result['packet_loss'] = ping_result['packet_loss']
    
    return result

def check_internet_connectivity():
    """
    Check if the host machine has internet connectivity
    Returns True if it has internet access, False otherwise
    """
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    
    try:
        # Try to connect to Cloudflare's DNS server as a backup
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        pass
        
    return False

def check_port_connectivity(ip_address, ports, timeout=3):
    """
    Check connectivity to specific ports on a device
    
    Parameters:
    - ip_address: IP to check
    - ports: List of port numbers to check
    - timeout: Connection timeout in seconds
    
    Returns a dictionary with port status results
    """
    if not ports:
        return {'ports_checked': 0, 'ports_open': 0, 'status': 'skipped'}
    
    # Convert string of ports to a list if needed
    if isinstance(ports, str):
        try:
            ports = [int(p.strip()) for p in ports.split(',') if p.strip()]
        except ValueError:
            return {'error': 'Invalid port format', 'status': 'error'}
    
    results = {
        'ports_checked': len(ports),
        'ports_open': 0,
        'open_ports': [],
        'closed_ports': [],
        'status': 'offline'
    }
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, port))
            if result == 0:  # Port is open
                results['ports_open'] += 1
                results['open_ports'].append(port)
            else:
                results['closed_ports'].append(port)
            sock.close()
        except Exception as e:
            results['error'] = f"Error checking port {port}: {str(e)}"
            results['closed_ports'].append(port)
    
    # Consider device online if at least one port is open
    if results['ports_open'] > 0:
        results['status'] = 'online'
    
    return results

def check_device_connectivity_with_params(ip_address, device_type=None, ports=None, use_ping_fallback=True,
                                         ping_count=3, timeout=5, retry_count=2):
    """
    Enhanced device connectivity check supporting both port and ping checks
    
    Parameters:
    - ip_address: IP to check
    - device_type: Type of device (router, pc, etc.)
    - ports: Comma-separated string or list of ports to check
    - use_ping_fallback: Whether to use ping if port check fails
    - ping_count, timeout, retry_count: Parameters for ping check
    
    Returns a dictionary with connectivity status and detailed results
    """
    result = {
        'ip': ip_address,
        'status': 'offline',
        'timestamp': datetime.now().isoformat(),
        'device_type': device_type,
        'error': None,
        'port_check': None,
        'ping_check': None
    }
    
    # First try port check if ports are specified
    if ports:
        port_result = check_port_connectivity(ip_address, ports, timeout)
        result['port_check'] = port_result
        
        # If port check shows device is online, we're done
        if port_result['status'] == 'online':
            result['status'] = 'online'
            return result
    
    # If port check failed or wasn't performed, and ping fallback is enabled
    if use_ping_fallback:
        ping_result = measure_ping_latency(
            ip_address,
            count=ping_count,
            timeout=timeout,
            retry_count=retry_count
        )
        
        result['ping_check'] = {
            'latency_ms': ping_result['latency_ms'],
            'packet_loss': ping_result['packet_loss'],
            'error': ping_result['error']
        }
        
        if ping_result['latency_ms'] is not None:
            result['status'] = 'online'
    
    # If we got this far and status is still offline, record an error
    if result['status'] == 'offline':
        if result.get('port_check') and result.get('port_check', {}).get('error'):
            result['error'] = result['port_check']['error']
        elif result.get('ping_check') and result.get('ping_check', {}).get('error'):
            result['error'] = result['ping_check']['error']
        else:
            result['error'] = "Device is unreachable"
    
    return result

def check_ips_connectivity(ip_addresses, locations=None, ping_count=3, timeout=5, retry_count=2):
    """
    Check connectivity for a list of IP addresses and return detailed results.
    
    Parameters:
    - ip_addresses: List of IP addresses to check
    - locations: Dictionary mapping IPs to location descriptions (optional)
    - ping_count: Number of pings to send for each check
    - timeout: Timeout in seconds for each ping
    - retry_count: Number of retries if ping fails
    
    Returns a dictionary with overall results and individual IP details.
    """
    if locations is None:
        locations = {}
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_ips': len(ip_addresses),
        'online_count': 0,
        'offline_count': 0,
        'details': {}
    }
    
    for ip in ip_addresses:
        location = locations.get(ip, "unknown")
        ip_result = check_device_connectivity(
            ip,
            location=location,
            ping_count=ping_count,
            timeout=timeout,
            retry_count=retry_count
        )
        
        # Update counts
        if ip_result['status'] == 'online':
            results['online_count'] += 1
        else:
            results['offline_count'] += 1
        
        # Store detailed result
        results['details'][ip] = ip_result
    
    # Calculate summary statistics
    online_ips = [details for ip, details in results['details'].items() 
                  if details['status'] == 'online']
    
    if online_ips:
        latencies = [details['latency_ms'] for details in online_ips 
                     if details['latency_ms'] is not None]
        
        if latencies:
            results['avg_latency_ms'] = sum(latencies) / len(latencies)
            results['min_latency_ms'] = min(latencies)
            results['max_latency_ms'] = max(latencies)
        
        packet_losses = [details['packet_loss'] for details in online_ips 
                        if details['packet_loss'] is not None]
        
        if packet_losses:
            results['avg_packet_loss'] = sum(packet_losses) / len(packet_losses)
    
    return results







def check_device_internet_connectivity():
    """
    Check if the host machine has internet connectivity
    Returns True if it has internet access, False otherwise
    """
    import socket
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    
    try:
        # Try to connect to Cloudflare's DNS server as a backup
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        pass
        
    return False














