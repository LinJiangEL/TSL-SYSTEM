#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""WHOIS 查询。

先向 IANA 的 whois 服务查询目标的权威服务器，再向该服务器请求
完整的注册信息，并从中提取注册商、创建时间、到期时间等字段。
"""

import re
import socket

from tools.Network.modules import common

WHOIS_PORT = 43
IANA_SERVER = 'whois.iana.org'
DEFAULT_TIMEOUT = 10
FIELD_NAMES = (
    'domain name',
    'registrar',
    'registrar url',
    'creation date',
    'created',
    'updated date',
    'expiry date',
    'expiration date',
    'registry expiry date',
    'registrant',
    'registrant country',
    'name server',
    'status',
    'dnssec',
    'org',
    'organisation',
    'netname',
    'country',
    'descr',
    'inetnum',
)


def _request(server, target, timeout=DEFAULT_TIMEOUT):
    """向指定 whois 服务器的 43 端口发送查询并读取全部响应。"""
    try:
        connection = socket.create_connection((server, WHOIS_PORT), timeout=timeout)
    except OSError as error:
        raise common.NetworkError("cannot connect to the whois server '%s': %s." % (server, error))
    try:
        connection.sendall((target + '\r\n').encode('utf-8'))
        chunks = []
        while True:
            data = connection.recv(4096)
            if not data:
                break
            chunks.append(data)
    finally:
        connection.close()

    return b''.join(chunks).decode('utf-8', errors='replace')


def _referral(text):
    """从 IANA 的响应中提取权威 whois 服务器。"""
    for line in text.splitlines():
        lowered = line.lower().strip()
        for prefix in ('refer:', 'whois:', 'referralserver:'):
            if lowered.startswith(prefix):
                value = line.split(':', 1)[1].strip()
                if value:
                    return value
    return ''


def _fields(text):
    """把 whois 文本中的关键字段整理成字典。"""
    result = {}
    for line in text.splitlines():
        if ':' not in line or line.startswith('%') or line.startswith('#'):
            continue
        key, value = line.split(':', 1)
        key = key.strip().lower()
        value = value.strip()
        if not key or not value or key not in FIELD_NAMES:
            continue
        if key in result:
            if isinstance(result[key], list):
                result[key].append(value)
            else:
                result[key] = [result[key], value]
        else:
            result[key] = value
    return result


def lookup(target, timeout=DEFAULT_TIMEOUT):
    """查询域名或 IP 的 whois 信息，返回结构化结果。"""
    target = target.strip()
    if not target:
        raise common.NetworkError('the whois target is empty.')
    if '://' in target:
        target = common.parse_target(target)[1]
    target = target.split('/')[0]

    iana_text = _request(IANA_SERVER, target, timeout=timeout)
    referral = _referral(iana_text)
    server = referral or IANA_SERVER
    text = _request(server, target, timeout=timeout) if referral else iana_text
    if not text.strip():
        raise common.NetworkError("the whois server '%s' returned an empty response." % server)
    if 'no match' in text.lower() or 'not found' in text.lower():
        raise common.NetworkError("no whois record was found for '%s'." % target)

    return {
        'target': target,
        'server': server,
        'fields': _fields(text),
        'text': text,
        'truncated': len(text) >= 5000,
    }


def summarize(result):
    """把 whois 结果整理为可直接打印的文本行。"""
    fields = result['fields']
    lines = ['WHOIS Server: %s' % result['server']]
    for key in ('domain name', 'registrar', 'creation date', 'created', 'expiry date',
                'expiration date', 'updated date', 'name server', 'status', 'org', 'country'):
        if key not in fields:
            continue
        value = fields[key]
        if isinstance(value, list):
            value = ', '.join(value)
        lines.append('%-16s: %s' % (key.title(), value))
    if len(lines) == 1:
        lines.append('No structured field was recognized, see the raw record below.')
    return lines


def raw_text(result, limit=4000):
    """返回截断到指定长度的原始 whois 文本。"""
    text = result['text']
    if len(text) <= limit:
        return text
    return text[:limit] + '\n... (%d characters omitted)' % (len(text) - limit)
