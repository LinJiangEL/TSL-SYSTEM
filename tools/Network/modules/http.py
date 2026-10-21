#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""HTTP / HTTPS 站点分析。

在 common.fetch 的基础上检查状态码、跳转链、响应头、安全响应头、
Cookie 属性以及各阶段耗时，用于快速判断一个站点是否可访问、
是否启用了常见的安全策略。
"""

from tools.Network.modules import common

SECURITY_HEADERS = {
    'strict-transport-security': 'HSTS',
    'content-security-policy': 'CSP',
    'x-frame-options': 'X-Frame-Options',
    'x-content-type-options': 'X-Content-Type-Options',
    'referrer-policy': 'Referrer-Policy',
    'permissions-policy': 'Permissions-Policy',
    'cross-origin-opener-policy': 'COOP',
}


def check_headers(headers):
    """检查安全响应头的存在情况，返回 {名称: 是否存在} 字典。"""
    return {name: (name in headers) for name in SECURITY_HEADERS}


def check_cookies(headers):
    """检查 Set-Cookie 中是否设置了 Secure 与 HttpOnly 属性。"""
    cookie = headers.get('set-cookie', '')
    if not cookie:
        return {'present': False, 'secure': False, 'httponly': False, 'samesite': False}
    lowered = cookie.lower()
    return {
        'present': True,
        'secure': 'secure' in lowered,
        'httponly': 'httponly' in lowered,
        'samesite': 'samesite' in lowered,
    }


def analyze(url, timeout=common.DEFAULT_TIMEOUT):
    """请求 URL 并汇总状态、耗时、安全头与 Cookie 信息。"""
    result = common.fetch(url, timeout=timeout, max_bytes=512 * 1024)
    headers = result['headers']
    security = check_headers(headers)
    return {
        'url': result['url'],
        'status': result['status'],
        'reason': result['reason'],
        'remote_ip': result['remote_ip'],
        'content_type': result['content_type'],
        'size': result['size'],
        'server': headers.get('server', ''),
        'powered_by': headers.get('x-powered-by', ''),
        'redirects': result['redirects'],
        'security': security,
        'cookies': check_cookies(headers),
        'timing': result['timing'],
        'tls_error': result['tls_error'],
        'headers': headers,
    }


def missing_security_headers(security):
    """返回缺失的安全响应头名称列表。"""
    return [label for name, label in SECURITY_HEADERS.items() if not security.get(name)]


def summarize(analysis):
    """把分析结果整理为可直接打印的文本行列表。"""
    lines = []
    lines.append('URL         : %s' % analysis['url'])
    lines.append('Status      : %d %s' % (analysis['status'], analysis['reason']))
    lines.append('Remote IP   : %s' % analysis['remote_ip'])
    lines.append('Content-Type: %s' % (analysis['content_type'] or 'unknown'))
    lines.append('Body Size   : %s' % common.format_bytes(analysis['size']))
    if analysis['server']:
        lines.append('Server      : %s' % analysis['server'])
    if analysis['powered_by']:
        lines.append('Powered By  : %s' % analysis['powered_by'])
    if analysis['tls_error']:
        lines.append('TLS Warning : %s' % analysis['tls_error'])
    if analysis['redirects']:
        lines.append('Redirects   : %d' % len(analysis['redirects']))
        for source, status, target in analysis['redirects']:
            lines.append('  %d %s -> %s' % (status, source, target))
    else:
        lines.append('Redirects   : none')

    timing = analysis['timing']
    lines.append('Timing      : DNS %s | TCP %s | TLS %s | TTFB %s | Total %s' % (
        common.format_seconds(timing['dns']),
        common.format_seconds(timing['connect']),
        common.format_seconds(timing['tls']),
        common.format_seconds(timing['ttfb']),
        common.format_seconds(timing['total']),
    ))

    missing = missing_security_headers(analysis['security'])
    lines.append('Security    : %s' % ('all recommended headers are present'
                                      if not missing
                                      else 'missing ' + ', '.join(missing)))
    cookie = analysis['cookies']
    if cookie['present']:
        flags = [name for name in ('secure', 'httponly', 'samesite') if cookie[name]]
        lines.append('Cookies     : %s' % (', '.join(flags) if flags else 'no protective attribute'))
    return lines
