#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""本机网络信息。

读取本机的网卡、IPv4 地址、子网掩码、默认网关、DNS 服务器和
ARP/邻居表，并查询出口公网 IP 及其归属信息。
"""

import re
import socket
import subprocess
import sys

from tools.Network.modules import common

IPV4_PATTERN = re.compile(r'\b(\d{1,3}(?:\.\d{1,3}){3})\b')
MAC_PATTERN = re.compile(r'\b([0-9A-Fa-f]{2}(?:[-:][0-9A-Fa-f]{2}){5})\b')


def _run(command, timeout=10):
    """执行系统命令并返回解码后的输出。"""
    try:
        process = subprocess.run(command, capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return ''
    encoding = 'mbcs' if sys.platform == 'win32' else 'utf-8'
    return process.stdout.decode(encoding, errors='replace')


def _windows_interfaces():
    """解析 ipconfig /all 的输出，提取 Windows 网卡信息。"""
    text = _run(['ipconfig', '/all'])
    interfaces = []
    entry = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^.*(?:adapter|适配器)[^:]*:\s*$', stripped, re.IGNORECASE):
            entry = {'name': stripped.rstrip(':').strip(), 'description': '',
                     'ipv4': [], 'mask': [], 'gateway': [], 'mac': '', 'dns': [], 'dhcp': False}
            interfaces.append(entry)
            continue
        if entry is None or ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        lowered_key = key.lower()
        addresses = IPV4_PATTERN.findall(value)
        if 'description' in lowered_key or '描述' in key:
            entry['description'] = value
            continue
        if 'physical' in lowered_key or '物理' in key:
            mac = MAC_PATTERN.search(value)
            entry['mac'] = mac.group(1).upper() if mac else ''
            continue
        if not addresses:
            if 'dhcp' in lowered_key and 'enabled' in lowered_key:
                entry['dhcp'] = value.lower().startswith(('yes', '是'))
            continue
        if 'ipv4' in lowered_key or lowered_key in ('ip address', 'ip 地址'):
            entry['ipv4'].extend(addresses)
        elif 'mask' in lowered_key or '掩码' in key:
            entry['mask'].extend(addresses)
        elif 'gateway' in lowered_key or '网关' in key:
            entry['gateway'].extend(addresses)
        elif 'dns' in lowered_key:
            entry['dns'].extend(addresses)
        elif not entry['ipv4']:
            entry['ipv4'].extend(addresses)

    result = []
    for item in interfaces:
        if not item['ipv4']:
            continue
        if item['description']:
            item['name'] = item['description']
        result.append(item)

    return result


def _linux_interfaces():
    """解析 ip 命令的输出，提取 Linux 网卡信息。"""
    interfaces = []
    output = _run(['ip', '-o', '-4', 'addr', 'show'])
    for line in output.splitlines():
        pieces = line.split()
        if len(pieces) < 4 or 'inet' not in pieces:
            continue
        name = pieces[1].rstrip(':')
        index = pieces.index('inet')
        address = pieces[index + 1].split('/')[0]
        prefix = pieces[index + 1].split('/')[1] if '/' in pieces[index + 1] else '24'
        netmask = (0xFFFFFFFF << (32 - int(prefix))) & 0xFFFFFFFF
        mask = socket.inet_ntoa(netmask.to_bytes(4, 'big'))
        mac = ''
        try:
            with open('/sys/class/net/%s/address' % name, 'r') as mac_file:
                mac = mac_file.read().strip().upper()
        except OSError:
            mac = ''
        interfaces.append({'name': name, 'description': '', 'ipv4': [address], 'mask': [mask],
                           'gateway': [], 'mac': mac, 'dns': [], 'dhcp': False})

    gateway = default_gateway()
    for entry in interfaces:
        if gateway:
            entry['gateway'].append(gateway)
    dns_servers = []
    try:
        with open('/etc/resolv.conf', 'r') as resolver_file:
            for line in resolver_file:
                pieces = line.split()
                if len(pieces) == 2 and pieces[0] == 'nameserver':
                    dns_servers.append(pieces[1])
    except OSError:
        dns_servers = []
    for entry in interfaces:
        entry['dns'] = list(dns_servers)

    return interfaces


def interfaces():
    """返回本机的网卡信息列表。"""
    if sys.platform == 'win32':
        return _windows_interfaces()
    return _linux_interfaces()


def default_gateway():
    """返回默认网关地址，找不到时返回空字符串。"""
    if sys.platform == 'win32':
        for entry in _windows_interfaces():
            if entry['gateway']:
                return entry['gateway'][0]
        return ''
    output = _run(['ip', 'route', 'show', 'default'])
    for line in output.splitlines():
        pieces = line.split()
        if len(pieces) >= 3 and pieces[0] == 'default':
            return pieces[2]
    return ''


def domain_name():
    """返回本机的主机名、域名和地址列表。"""
    try:
        hostname = socket.gethostname()
        addresses = socket.gethostbyname_ex(hostname)
    except OSError:
        return {'hostname': socket.gethostname(), 'domain': '', 'addresses': []}
    return {'hostname': addresses[0], 'domain': addresses[1], 'addresses': addresses[2]}


def arp_table():
    """返回本机 ARP / 邻居表中的条目。"""
    if sys.platform == 'win32':
        output = _run(['arp', '-a'])
        entries = []
        for line in output.splitlines():
            address = IPV4_PATTERN.search(line)
            mac = MAC_PATTERN.search(line)
            if address and mac:
                entries.append({'ip': address.group(1), 'mac': mac.group(1).upper()})
    else:
        output = _run(['ip', 'neigh'])
        entries = []
        for line in output.splitlines():
            pieces = line.split()
            if len(pieces) >= 2 and common.is_ipv4(pieces[0]):
                mac = ' '.join(pieces).lower()
                found = re.search(r'([0-9a-f]{2}(?::[0-9a-f]{2}){5})', mac)
                entries.append({'ip': pieces[0], 'mac': found.group(1).upper() if found else ''})

    unique = []
    seen = set()
    for entry in entries:
        key = (entry['ip'], entry['mac'])
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def public_ip(timeout=8):
    """查询本机的出口公网 IP 及归属信息。"""
    try:
        data = common.fetch_json('https://ipinfo.io/json?token=', timeout=timeout)
        if data.get('ip'):
            return {
                'ip': data.get('ip', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'country': data.get('country', ''),
                'org': data.get('org', ''),
                'loc': data.get('loc', ''),
            }
    except common.NetworkError:
        pass
    data = common.fetch_json('https://api.ipify.org?format=json', timeout=timeout)
    return {'ip': data.get('ip', ''), 'city': '', 'region': '', 'country': '', 'org': '', 'loc': ''}


def summarize():
    """把本机网络信息整理为可直接打印的文本行。"""
    lines = []
    host = domain_name()
    lines.append('Hostname    : %s' % host['hostname'])
    if host['addresses']:
        lines.append('Local IP    : %s' % ', '.join(host['addresses']))
    gateway = default_gateway()
    lines.append('Gateway     : %s' % (gateway or 'unknown'))
    for entry in interfaces():
        addresses = ', '.join('%s/%s' % (address, entry['mask'][0] if entry['mask'] else '?')
                              for address in entry['ipv4'])
        lines.append('Interface   : %-12s %s' % (entry['name'], addresses))
        if entry['mac']:
            lines.append('  MAC       : %s' % entry['mac'])
        if entry['dns']:
            lines.append('  DNS       : %s' % ', '.join(entry['dns']))
    return lines
