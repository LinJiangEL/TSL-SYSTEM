#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""带宽与延迟测试。

下载测试默认使用 Cloudflare 的测速端点，通过原始套接字分块读取
数据，统计实际下载速率；延迟测试则对目标重复建立 TCP 连接，取
平均值、最小值与抖动。
"""

import socket
import ssl
import statistics
import time

from tools.Network.modules import common

SPEED_TEST_URL = 'https://speed.cloudflare.com/__down?bytes=25000000'
DEFAULT_BYTES = 8 * 1024 * 1024
DEFAULT_DURATION = 6.0


def _connect(host, port, timeout):
    """建立到目标的 TCP（必要时 TLS）连接，返回套接字。"""
    family, sockaddr, _ = common.resolve(host, port)
    connection = socket.socket(family, socket.SOCK_STREAM)
    connection.settimeout(timeout)
    connection.connect(sockaddr)
    if port == 443:
        context = ssl.create_default_context()
        connection = context.wrap_socket(connection, server_hostname=host)
    return connection


def download(url=SPEED_TEST_URL, max_bytes=DEFAULT_BYTES, max_seconds=DEFAULT_DURATION, timeout=8):
    """下载测试数据并返回平均速率。"""
    scheme, host, port, path = common.parse_target(url)
    started = time.time()
    connection = _connect(host, port, timeout)
    received = 0
    try:
        request = ('GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: %s\r\n'
                   'Accept: */*\r\nConnection: close\r\n\r\n'
                   % (path, host, common.USER_AGENT)
                   )
        connection.sendall(request.encode('latin-1'))
        reader = connection.makefile('rb')
        while True:
            line = reader.readline(8192)
            if not line or line in (b'\r\n', b'\n'):
                break
        begin = time.time()
        while received < max_bytes:
            if time.time() - begin > max_seconds:
                break
            chunk = reader.read(common.CHUNK_SIZE)
            if not chunk:
                break
            received += len(chunk)
        elapsed = time.time() - begin
        reader.close()
    finally:
        connection.close()

    if elapsed <= 0:
        raise common.NetworkError('the download test finished too fast to be measured.')
    bits = received * 8
    return {
        'url': url,
        'bytes': received,
        'seconds': elapsed,
        'bytes_per_second': received / elapsed,
        'mbps': bits / elapsed / 1000000.0,
        'total_seconds': time.time() - started,
    }


def latency(host, port=443, count=5, timeout=3):
    """重复建立 TCP 连接，返回握手延迟统计。"""
    if not common.valid_host(host):
        raise common.NetworkError("the host '%s' is invalid." % host)
    samples = []
    for _ in range(max(1, min(count, 20))):
        started = time.time()
        try:
            connection = _connect(host, port, timeout)
        except (OSError, ssl.SSLError):
            continue
        elapsed = time.time() - started
        connection.close()
        samples.append(elapsed)
    if not samples:
        raise common.NetworkError('no TCP connection to %s:%d could be established.' % (host, port))
    return {
        'host': host,
        'port': port,
        'count': len(samples),
        'min': min(samples),
        'avg': statistics.mean(samples),
        'max': max(samples),
        'jitter': statistics.pstdev(samples) if len(samples) > 1 else 0.0,
        'samples': samples,
    }
