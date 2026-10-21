#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""TCP 端口探测与端口服务识别。

使用非阻塞 connect 加线程池并发扫描，不发送任何攻击性载荷，
只用于检查本机或已授权主机上哪些端口处于监听状态。
"""

import concurrent.futures
import re
import socket
import time

from tools.Network.modules import common

COMMON_PORTS = {
    21: 'ftp',
    22: 'ssh',
    23: 'telnet',
    25: 'smtp',
    53: 'dns',
    67: 'dhcp',
    69: 'tftp',
    80: 'http',
    110: 'pop3',
    123: 'ntp',
    135: 'msrpc',
    137: 'netbios-ns',
    138: 'netbios-dgm',
    139: 'netbios-ssn',
    143: 'imap',
    161: 'snmp',
    162: 'snmptrap',
    179: 'bgp',
    389: 'ldap',
    443: 'https',
    445: 'microsoft-ds',
    465: 'smtps',
    500: 'isakmp',
    514: 'syslog',
    515: 'lpd',
    587: 'submission',
    631: 'ipp',
    636: 'ldaps',
    873: 'rsync',
    993: 'imaps',
    995: 'pop3s',
    1080: 'socks',
    1433: 'mssql',
    1521: 'oracle',
    1723: 'pptp',
    1883: 'mqtt',
    2049: 'nfs',
    2375: 'docker',
    2376: 'docker-tls',
    3128: 'squid',
    3306: 'mysql',
    3389: 'rdp',
    5432: 'postgresql',
    5672: 'amqp',
    5900: 'vnc',
    5984: 'couchdb',
    6379: 'redis',
    6443: 'kubernetes',
    7001: 'weblogic',
    8000: 'http-alt',
    8008: 'http-alt',
    8080: 'http-proxy',
    8081: 'http-alt',
    8443: 'https-alt',
    8888: 'http-alt',
    9000: 'php-fpm',
    9090: 'zeus-admin',
    9200: 'elasticsearch',
    11211: 'memcached',
    27017: 'mongodb',
}
TOP_PORTS = tuple(sorted(COMMON_PORTS))
MAX_PORTS = 2048
MAX_WORKERS = 128
DEFAULT_RANGE = 'top'


def parse_ports(specification):
    """解析端口表达式，支持 '80,443'、'1-1024' 与 'top'。"""
    if specification is None:
        return list(TOP_PORTS)
    text = str(specification).strip().lower()
    if not text or text == 'top':
        return list(TOP_PORTS)
    if text == 'all':
        return list(range(1, 65536))

    ports = []
    for piece in re.split(r'[,\s]+', text):
        if not piece:
            continue
        if '-' in piece:
            start_text, end_text = piece.split('-', 1)
            if not start_text.isdigit() or not end_text.isdigit():
                raise common.NetworkError("the port range '%s' is invalid." % piece)
            start, end = int(start_text), int(end_text)
            if start < 1 or end > 65535 or start > end:
                raise common.NetworkError("the port range '%s' is invalid." % piece)
            ports.extend(range(start, end + 1))
        else:
            if not piece.isdigit():
                raise common.NetworkError("the port '%s' is invalid." % piece)
            port = int(piece)
            if not 1 <= port <= 65535:
                raise common.NetworkError("the port '%d' is out of range." % port)
            ports.append(port)

    unique = []
    for port in ports:
        if port not in unique:
            unique.append(port)
    if len(unique) > MAX_PORTS:
        raise common.NetworkError('the port number is too large to scan (more than %d).' % MAX_PORTS)

    return unique


def _probe(host, port, timeout):
    """尝试连接单个端口，成功时返回服务信息和横幅。"""
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(timeout)
    started = time.time()
    try:
        code = connection.connect_ex((host, port))
        elapsed = time.time() - started
        if code != 0:
            return None
        banner = ''
        connection.settimeout(0.6)
        try:
            data = connection.recv(256)
            banner = data.decode('latin-1', errors='replace').strip()
        except (socket.timeout, OSError):
            banner = ''
        return {
            'port': port,
            'service': COMMON_PORTS.get(port, 'unknown'),
            'latency': elapsed,
            'banner': ' '.join(banner.split())[:120],
        }
    finally:
        connection.close()


def scan(host, ports=None, timeout=1.0, workers=MAX_WORKERS):
    """并发扫描目标主机的 TCP 端口，返回开放端口列表。"""
    if not common.valid_host(host):
        raise common.NetworkError("the host '%s' is invalid." % host)
    targets = parse_ports(ports)
    timeout = max(0.2, min(float(timeout), 5.0))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, len(targets))) as executor:
        futures = [executor.submit(_probe, host, port, timeout) for port in targets]
        for future in concurrent.futures.as_completed(futures):
            try:
                item = future.result()
            except OSError:
                item = None
            if item:
                results.append(item)

    results.sort(key=lambda item: item['port'])
    return results


def is_open(host, port, timeout=1.0):
    """检查单个端口是否开放。"""
    return _probe(host, int(port), timeout) is not None
