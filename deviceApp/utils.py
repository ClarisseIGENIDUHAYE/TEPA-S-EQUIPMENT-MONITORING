import socket
import subprocess
import platform
from datetime import datetime

def check_device_internet_connectivity():
    """
    Check if the host machine has internet connectivity.
    Returns True if it has internet access, False otherwise.
    """
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        pass
        
    return False

def check_device_connectivity_with_params(ip_address, device_type='other', ports=None, use_ping_fallback=True):
    result = {
        'reachable': False,
        'has_internet': False,
        'status': 'offline',
        'check_time': datetime.now().isoformat(),
        'error': None,
        'host_has_internet': check_device_internet_connectivity()
    }

    if not result['host_has_internet']:
        result['error'] = "Host has no internet connectivity"
        return result

    is_external_ip = not (ip_address.startswith('192.168.') or 
                          ip_address.startswith('10.') or 
                          ip_address.startswith('172.'))
    
    if is_external_ip and not result['host_has_internet']:
        result['error'] = "Host has no internet connectivity to reach external IP"
        return result

    ports_to_check = ports or [80, 443, 22, 8080]
    port_open = False

    for port in ports_to_check:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            connect_result = sock.connect_ex((ip_address, port))
            sock.close()
            if connect_result == 0:
                port_open = True
                result['reachable'] = True
                break
        except (socket.error, socket.timeout, socket.gaierror):
            continue

    if not port_open and use_ping_fallback:
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', ip_address]
            
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=2)
            stdout_str = stdout.decode(errors='ignore').lower()
            
            if "bytes=32" in stdout_str and "ttl=" in stdout_str:
                result['reachable'] = True
            elif "destination host unreachable" in stdout_str:
                result['error'] = "Ping failed: Host unreachable"
            elif "request timed out" in stdout_str:
                result['error'] = "Ping failed: Request timed out"
            else:
                result['reachable'] = (process.returncode == 0)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            result['error'] = f"Ping error: {str(e)}"

    if result['reachable']:
        result['has_internet'] = result['host_has_internet']
        result['status'] = 'online' if result['has_internet'] else 'offline'
    
    return result
  
    

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














