#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""ICMP 连通性探测。

调用操作系统自带的 ping 命令并解析输出，避免在纯 Python 中构造
原始套接字（Windows 下需要管理员权限）。同时兼容英文与中文系统
的 ping 输出格式。
"""

import re
import statistics
import subprocess
import sys

from tools.Network.modules import common

RTT_PATTERN = re.compile(r'(?:time|时间|tiempo|temps)[=<]\s*([\d.]+)\s*ms', re.IGNORECASE)
LOSS_PATTERN = re.compile(r'(\d+)%\s*(?:loss|丢失|verlust|perdidos)', re.IGNORECASE)


def ping(host, count=4, timeout=2.0):
    """向目标发送 ICMP 回显请求，返回统计结果字典。"""
    if not common.valid_host(host):
        raise common.NetworkError("the host '%s' is invalid." % host)
    count = max(1, min(int(count), 20))
    milliseconds = max(200, int(timeout * 1000))
    if sys.platform == 'win32':
        command = ['ping', '-n', str(count), '-w', str(milliseconds), host]
    else:
        command = ['ping', '-c', str(count), '-W', str(max(1, int(timeout))), host]

    try:
        process = subprocess.run(command, capture_output=True, timeout=count * timeout + 10)
    except FileNotFoundError:
        raise common.NetworkError('the ping command was not found on this system.')
    except subprocess.TimeoutExpired:
        raise common.NetworkError('the ping command did not finish in time.')

    text = process.stdout.decode('mbcs' if sys.platform == 'win32' else 'utf-8', errors='replace')
    rtts = [float(value) for value in RTT_PATTERN.findall(text)]
    received = len(rtts)
    loss = round((count - received) * 100.0 / count, 1)
    loss_match = LOSS_PATTERN.search(text)
    if loss_match:
        loss = float(loss_match.group(1))

    result = {
        'host': host,
        'sent': count,
        'received': received,
        'loss': loss,
        'rtts': rtts,
        'min': min(rtts) if rtts else None,
        'avg': statistics.mean(rtts) if rtts else None,
        'max': max(rtts) if rtts else None,
        'jitter': statistics.pstdev(rtts) if len(rtts) > 1 else 0.0,
        'output': text,
        'returncode': process.returncode,
    }
    if received == 0 and 'transmit failed' in text.lower():
        raise common.NetworkError('ICMP is blocked on this system '
                                  '(the ping command reported "transmit failed").')
    return result


def ping_once(host, timeout=2.0):
    """只发送一次请求，返回平均延迟或 None。"""
    result = ping(host, count=1, timeout=timeout)
    return result['avg']
