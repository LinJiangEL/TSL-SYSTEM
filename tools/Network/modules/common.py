#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""网络探测模块的公共工具。

这里集中放置 HTTP 请求、目标解析和格式化输出等基础函数，供
probe 目录下的其它模块复用。所有函数都只依赖 Python 标准库，
以保持与项目其它模块一致的 Python 3.9.6 运行环境。
"""

import json
import socket
import ssl
import time
import urllib.parse

DEFAULT_TIMEOUT = 10
MAX_REDIRECTS = 5
CHUNK_SIZE = 64 * 1024
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/124.0 Safari/537.36')


class NetworkError(Exception):
    """网络探测模块抛出的错误，异常信息本身即为错误提示。"""


def is_ipv4(address):
    """判断字符串是否为合法的 IPv4 地址。"""
    try:
        socket.inet_aton(address)
    except OSError:
        return False

    return address.count('.') == 3


def is_ipv6(address):
    """判断字符串是否为合法的 IPv6 地址。"""
    return ':' in address and _is_inet_pton(address)


def _is_inet_pton(address):
    """在支持 inet_pton 的平台上校验 IPv6 地址。"""
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except OSError:
        return False

    return True


def valid_host(host):
    """校验主机名或 IP 地址的格式。"""
    if not host or len(host) > 253:
        return False
    if is_ipv4(host) or (':' in host and _is_inet_pton(host)):
        return True
    labels = host.rstrip('.').split('.')
    for label in labels:
        if not label or len(label) > 63:
            return False
        if label[0] == '-' or label[-1] == '-':
            return False
        for character in label:
            if not (character.isalnum() or character in '-_'):
                return False

    return True


def parse_target(target):
    """把 URL 或主机名解析为 (scheme, host, port, path) 四元组。"""
    target = target.strip()
    if not target:
        raise NetworkError('the target is empty.')
    if '://' not in target:
        target = 'https://' + target
    parts = urllib.parse.urlsplit(target)
    scheme = parts.scheme.lower()
    if scheme not in ('http', 'https'):
        raise NetworkError("the scheme '%s' is not supported." % scheme)
    host = parts.hostname or ''
    if not valid_host(host):
        raise NetworkError("the host '%s' is invalid." % host)
    port = parts.port or (443 if scheme == 'https' else 80)
    path = parts.path or '/'
    if parts.query:
        path += '?' + parts.query

    return scheme, host, port, path


def resolve(host, port=0):
    """解析主机名，返回 (family, sockaddr, address) 三元组。"""
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as error:
        raise NetworkError("cannot resolve the host '%s': %s." % (host, error.strerror or error))

    family, _, _, _, sockaddr = infos[0]
    return family, sockaddr, sockaddr[0]


def fetch(url, timeout=DEFAULT_TIMEOUT, max_bytes=256 * 1024, allow_redirects=True, method='GET'):
    """用原始套接字请求一个 URL，并记录各阶段的耗时。

    返回一个字典，包含状态码、响应头、响应体、远端地址和耗时信息。
    使用套接字而非 urllib 是为了测量 DNS、TCP、TLS 和首字节时间。
    """
    redirects = []
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        result = _fetch_once(current, timeout, max_bytes, method)
        if not allow_redirects or result['status'] not in (301, 302, 303, 307, 308):
            result['redirects'] = redirects
            return result
        location = result['headers'].get('location', '')
        if not location:
            result['redirects'] = redirects
            return result
        redirects.append((result['url'], result['status'], location))
        current = urllib.parse.urljoin(result['url'], location)

    raise NetworkError('too many HTTP redirects (more than %d).' % MAX_REDIRECTS)


def _fetch_once(url, timeout, max_bytes, method):
    """执行一次 HTTP 请求，不处理重定向。"""
    scheme, host, port, path = parse_target(url)
    start = time.time()

    family, sockaddr, address = resolve(host, port)
    dns_done = time.time()

    connection = socket.socket(family, socket.SOCK_STREAM)
    connection.settimeout(timeout)
    try:
        connection.connect(sockaddr)
        connect_done = time.time()

        tls_error = None
        if scheme == 'https':
            context = ssl.create_default_context()
            try:
                connection = context.wrap_socket(connection, server_hostname=host)
            except ssl.SSLCertVerificationError as error:
                tls_error = str(error)
                connection.close()
                connection = socket.create_connection(sockaddr, timeout=timeout)
                context = ssl._create_unverified_context()
                connection = context.wrap_socket(connection, server_hostname=host)
            tls_done = time.time()
        else:
            tls_done = connect_done

        request = ('%s %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: %s\r\n'
                   'Accept: */*\r\nAccept-Encoding: identity\r\n'
                   'Connection: close\r\n\r\n' % (method, path, host, USER_AGENT)
                   )
        connection.sendall(request.encode('latin-1'))

        reader = connection.makefile('rb')
        status_line = reader.readline(1024).decode('latin-1').strip()
        first_byte = time.time()
        if not status_line:
            raise NetworkError('the server returned an empty response.')
        pieces = status_line.split(' ', 2)
        if len(pieces) < 2 or not pieces[0].startswith('HTTP/'):
            raise NetworkError('the server returned an invalid HTTP response.')
        status = int(pieces[1])
        reason = pieces[2] if len(pieces) > 2 else ''

        headers = {}
        while True:
            line = reader.readline(8192)
            if not line or line in (b'\r\n', b'\n'):
                break
            text = line.decode('latin-1').rstrip('\r\n')
            if ':' not in text:
                continue
            name, value = text.split(':', 1)
            name = name.strip().lower()
            value = value.strip()
            if name in headers:
                headers[name] += ', ' + value
            else:
                headers[name] = value

        body = b''
        content_length = headers.get('content-length', '')
        while len(body) < max_bytes:
            chunk = reader.read(min(CHUNK_SIZE, max_bytes - len(body)))
            if not chunk:
                break
            body += chunk
        reader.close()
        finish = time.time()
    finally:
        connection.close()

    encoding = 'utf-8'
    content_type = headers.get('content-type', '')
    if 'charset=' in content_type.lower():
        encoding = content_type.lower().split('charset=', 1)[1].split(';', 1)[0].strip() or 'utf-8'
    try:
        text = body.decode(encoding, errors='replace')
    except LookupError:
        encoding = 'utf-8'
        text = body.decode(encoding, errors='replace')

    return {
        'url': url,
        'scheme': scheme,
        'host': host,
        'port': port,
        'status': status,
        'reason': reason,
        'headers': headers,
        'body': body,
        'text': text,
        'size': len(body),
        'content_length': content_length,
        'content_type': content_type,
        'remote_ip': address,
        'tls_error': tls_error,
        'timing': {
            'dns': dns_done - start,
            'connect': connect_done - dns_done,
            'tls': max(tls_done - connect_done, 0.0),
            'ttfb': first_byte - tls_done,
            'download': finish - first_byte,
            'total': finish - start,
        },
    }


def fetch_json(url, timeout=DEFAULT_TIMEOUT):
    """请求一个 JSON 接口并返回解析后的对象。"""
    result = fetch(url, timeout=timeout)
    if result['status'] != 200:
        raise NetworkError('the server returned HTTP %d.' % result['status'])
    try:
        return json.loads(result['text'])
    except ValueError:
        raise NetworkError('the server returned invalid JSON.')


def format_seconds(seconds):
    """把秒数格式化为便于阅读的字符串。"""
    if seconds < 1:
        return '%.0f ms' % (seconds * 1000)
    return '%.2f s' % seconds


def format_bytes(size):
    """把字节数格式化为便于阅读的字符串。"""
    units = ('B', 'KB', 'MB', 'GB', 'TB')
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return '%.2f %s' % (value, unit)
        value /= 1024.0

    return '%.2f TB' % value


def short_host(host):
    """截断过长的主机名，保证表格输出整齐。"""
    return host if len(host) <= 40 else host[:37] + '...'
