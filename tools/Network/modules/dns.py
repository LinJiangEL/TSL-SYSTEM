#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""DNS 探测模块。

使用 UDP 直接与 DNS 服务器通信，不依赖 dnspython 等第三方库，
因此可以在 TSL-SYSTEM 的原始 Python 环境中运行。支持 A、AAAA、
CNAME、MX、NS、TXT、SOA、SRV、CAA 和 PTR 记录。
"""

import os
import random
import re
import socket
import struct
import sys

from tools.Network.modules import common

DNS_PORT = 53
DEFAULT_TIMEOUT = 3
RECORD_TYPES = {
    'A': 1,
    'NS': 2,
    'CNAME': 5,
    'SOA': 6,
    'PTR': 12,
    'MX': 15,
    'TXT': 16,
    'AAAA': 28,
    'SRV': 33,
    'CAA': 257,
}
TYPE_NAMES = {value: key for key, value in RECORD_TYPES.items()}
RCODE_TEXT = {
    0: 'NOERROR',
    1: 'FORMERR',
    2: 'SERVFAIL',
    3: 'NXDOMAIN',
    4: 'NOTIMP',
    5: 'REFUSED',
}
PUBLIC_RESOLVERS = ('223.5.5.5', '8.8.8.8', '1.1.1.1')


def get_resolvers():
    """读取本机配置的 DNS 服务器，失败时回退到公共 DNS。"""
    servers = []
    if sys.platform == 'win32':
        try:
            import subprocess
            output = subprocess.run(['ipconfig', '/all'], capture_output=True, timeout=10)
            text = output.stdout.decode('mbcs', errors='replace')
        except (OSError, subprocess.SubprocessError):
            text = ''
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if 'DNS' not in line.upper():
                continue
            if ':' in line:
                candidate = line.split(':', 1)[1].strip()
                if common.is_ipv4(candidate):
                    servers.append(candidate)
            for offset in range(1, 4):
                if index + offset >= len(lines):
                    break
                candidate = lines[index + offset].strip()
                if common.is_ipv4(candidate):
                    servers.append(candidate)
                else:
                    break
    else:
        try:
            with open('/etc/resolv.conf', 'r') as resolver_file:
                for line in resolver_file:
                    pieces = line.split()
                    if len(pieces) == 2 and pieces[0] == 'nameserver' and common.is_ipv4(pieces[1]):
                        servers.append(pieces[1])
        except OSError:
            servers = []

    unique = []
    for server in servers + list(PUBLIC_RESOLVERS):
        if server not in unique:
            unique.append(server)

    return unique


def _encode_name(name):
    """把域名编码为 DNS 报文中的标签序列。"""
    name = name.strip('.')
    if not name:
        return b'\x00'
    payload = b''
    for label in name.split('.'):
        if not label or len(label) > 63:
            raise common.NetworkError("the domain name '%s' is invalid." % name)
        payload += bytes([len(label)]) + label.encode('idna')
    return payload + b'\x00'


def _decode_name(packet, offset):
    """解析报文中的域名，处理 DNS 压缩指针。"""
    labels = []
    jumped = False
    original = offset
    while True:
        if offset >= len(packet):
            raise common.NetworkError('the DNS response is truncated.')
        length = packet[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0 == 0xC0:
            if offset + 1 >= len(packet):
                raise common.NetworkError('the DNS response is truncated.')
            pointer = ((length & 0x3F) << 8) | packet[offset + 1]
            if not jumped:
                original = offset + 2
                jumped = True
            offset = pointer
            continue
        offset += 1
        labels.append(packet[offset:offset + length].decode('latin-1'))
        offset += length
    if not jumped:
        original = offset

    return '.'.join(labels), original


def build_query(name, record_type='A', identify=None):
    """构造一个 DNS 查询报文。"""
    record_type = record_type.upper()
    if record_type not in RECORD_TYPES:
        raise common.NetworkError("the record type '%s' is not supported." % record_type)
    identify = random.randint(0, 0xFFFF) if identify is None else identify
    header = struct.pack('!HHHHHH', identify, 0x0100, 1, 0, 0, 0)
    question = _encode_name(name) + struct.pack('!HH', RECORD_TYPES[record_type], 1)
    return identify, header + question


def parse_response(packet, identify):
    """解析 DNS 响应，返回 (rcode, records) 二元组。"""
    if len(packet) < 12:
        raise common.NetworkError('the DNS response is truncated.')
    packet_id, flags, question_count, answer_count, authority_count, additional_count = \
        struct.unpack('!HHHHHH', packet[:12])
    if packet_id != identify:
        raise common.NetworkError('the DNS response id does not match the query.')
    rcode = flags & 0x000F
    offset = 12
    for _ in range(question_count):
        _, offset = _decode_name(packet, offset)
        offset += 4

    records = []
    for _ in range(answer_count + authority_count + additional_count):
        name, offset = _decode_name(packet, offset)
        if offset + 10 > len(packet):
            break
        record_type, record_class, ttl, length = struct.unpack('!HHIH', packet[offset:offset + 10])
        offset += 10
        payload = packet[offset:offset + length]
        offset += length
        text = _parse_rdata(packet, payload, record_type, offset - length)
        if text is not None and record_class == 1:
            records.append((TYPE_NAMES.get(record_type, str(record_type)), name, ttl, text))

    return RCODE_TEXT.get(rcode, str(rcode)), records


def _parse_rdata(packet, payload, record_type, payload_offset):
    """把资源记录的数据部分转换为可读文本。"""
    try:
        if record_type == 1 and len(payload) == 4:
            return socket.inet_ntoa(payload)
        if record_type == 28 and len(payload) == 16:
            return socket.inet_ntop(socket.AF_INET6, payload)
        if record_type in (2, 5, 12):
            name, _ = _decode_name(packet, payload_offset)
            return name
        if record_type == 15 and len(payload) >= 3:
            preference = struct.unpack('!H', payload[:2])[0]
            name, _ = _decode_name(packet, payload_offset + 2)
            return '%d %s' % (preference, name)
        if record_type == 16:
            pieces = []
            index = 0
            while index < len(payload):
                length = payload[index]
                pieces.append(payload[index + 1:index + 1 + length].decode('latin-1'))
                index += 1 + length
            return ''.join(pieces)
        if record_type == 6:
            mname, offset = _decode_name(packet, payload_offset)
            rname, offset = _decode_name(packet, offset)
            numbers = struct.unpack('!IIIII', packet[offset:offset + 20])
            return '%s %s %d %d %d %d %d' % ((mname, rname) + numbers)
        if record_type == 33 and len(payload) >= 7:
            priority, weight, port = struct.unpack('!HHH', payload[:6])
            target, _ = _decode_name(packet, payload_offset + 6)
            return '%d %d %d %s' % (priority, weight, port, target)
        if record_type == 257 and len(payload) >= 2:
            flags = payload[0]
            tag_length = payload[1]
            tag = payload[2:2 + tag_length].decode('latin-1')
            value = payload[2 + tag_length:].decode('latin-1')
            return '%d %s %s' % (flags, tag, value)
    except (struct.error, UnicodeDecodeError, IndexError):
        return payload.hex()

    return payload.hex()


def query(name, record_type='A', server=None, timeout=DEFAULT_TIMEOUT):
    """查询一条 DNS 记录，返回 (server, rcode, records) 三元组。"""
    if not name:
        raise common.NetworkError('the domain name is empty.')
    identify, request = build_query(name, record_type)
    servers = [server] if server else get_resolvers()
    last_error = None
    for resolver in servers:
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        connection.settimeout(timeout)
        try:
            connection.sendto(request, (resolver, DNS_PORT))
            packet, _ = connection.recvfrom(4096)
        except socket.timeout:
            last_error = common.NetworkError('the DNS server %s did not respond.' % resolver)
            continue
        except OSError as error:
            last_error = common.NetworkError('cannot reach the DNS server %s: %s.' % (resolver, error))
            continue
        finally:
            connection.close()

        rcode, records = parse_response(packet, identify)
        return resolver, rcode, records

    raise last_error if last_error else common.NetworkError('no DNS server is available.')


def resolve(name, server=None, timeout=DEFAULT_TIMEOUT):
    """解析域名的常用记录，返回 {记录类型: [记录]} 字典。"""
    if common.is_ipv4(name):
        return {'PTR': [reverse_lookup(name, server, timeout)]}

    result = {}
    resolver = server or get_resolvers()[0]
    for record_type in ('A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT'):
        try:
            resolver, rcode, records = query(name, record_type, server=server, timeout=timeout)
        except common.NetworkError:
            continue
        values = [text for name_type, _, _, text in records if name_type == record_type]
        if values:
            result[record_type] = values
        if rcode == 'NXDOMAIN' and record_type == 'A':
            raise common.NetworkError("the domain name '%s' does not exist." % name)

    result['server'] = resolver
    return result


def reverse_lookup(address, server=None, timeout=DEFAULT_TIMEOUT):
    """查询 IP 地址的 PTR 记录。"""
    if common.is_ipv4(address):
        name = '.'.join(reversed(address.split('.'))) + '.in-addr.arpa'
    else:
        name = address.replace(':', '')[::-1]
        name = '.'.join(name) + '.ip6.arpa'
    _, rcode, records = query(name, 'PTR', server=server, timeout=timeout)
    values = [text for _, _, _, text in records]
    return values[0] if values else ''


def dns_servers():
    """返回本机使用的 DNS 服务器列表。"""
    return get_resolvers()
