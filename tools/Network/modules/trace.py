#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""路由追踪。

调用系统的 tracert / traceroute 命令并解析每一跳的地址与延迟，
避免直接构造 TTL 递增的原始套接字。
"""

import re
import subprocess
import sys

from tools.Network.modules import common

IP_PATTERN = re.compile(r'(\d{1,3}(?:\.\d{1,3}){3})\s*$')
RTT_PATTERN = re.compile(r'(<?[\d.]+)\s*ms', re.IGNORECASE)
HOP_PATTERN = re.compile(r'^\s*(\d+)\s+(.*)$')
MAX_HOPS = 30


def trace(host, max_hops=MAX_HOPS, timeout=2.0):
    """追踪到目标主机的路由，返回跳数列表。"""
    if not common.valid_host(host):
        raise common.NetworkError("the host '%s' is invalid." % host)
    max_hops = max(1, min(int(max_hops), 64))
    milliseconds = max(200, int(timeout * 1000))
    if sys.platform == 'win32':
        command = ['tracert', '-d', '-h', str(max_hops), '-w', str(milliseconds), host]
    else:
        command = ['traceroute', '-n', '-m', str(max_hops), '-w', str(max(1, int(timeout))), host]

    try:
        process = subprocess.run(command, capture_output=True, timeout=max_hops * timeout + 20)
    except FileNotFoundError:
        raise common.NetworkError('the traceroute command was not found on this system.')
    except subprocess.TimeoutExpired:
        raise common.NetworkError('the traceroute command did not finish in time.')

    text = process.stdout.decode('mbcs' if sys.platform == 'win32' else 'utf-8', errors='replace')
    hops = []
    for line in text.splitlines():
        match = HOP_PATTERN.match(line)
        if not match:
            continue
        hop = int(match.group(1))
        rest = match.group(2)
        if hop <= 0:
            continue
        address_match = IP_PATTERN.search(rest)
        address = address_match.group(1) if address_match else '*'
        rtts = []
        for value in RTT_PATTERN.findall(rest):
            rtts.append(0.5 if value.startswith('<') else float(value))
        hops.append({
            'hop': hop,
            'address': address,
            'rtts': rtts,
            'average': sum(rtts) / len(rtts) if rtts else None,
        })

    if not hops:
        raise common.NetworkError('the traceroute command returned no hop information.')
    if len(hops) == 1 and hops[0]['address'] == '*' and 'transmit error' in text.lower():
        raise common.NetworkError('ICMP is blocked on this system '
                                  '(the traceroute command reported a transmit error).')

    return {
        'host': host,
        'hops': hops,
        'reached': hops[-1]['address'] != '*',
        'output': text,
    }
