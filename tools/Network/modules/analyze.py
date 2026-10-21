#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""综合网络诊断。

把一个目标的 DNS 解析、ICMP 连通性、TCP 端口、TLS 证书、HTTP
响应以及 whois 注册信息汇总到一次分析中，适合在排查“网站打不开”
一类问题时使用。
"""

from tools.Network.modules import common
from tools.Network.modules import dns
from tools.Network.modules import http as http_module
from tools.Network.modules import ping as ping_module
from tools.Network.modules import ports as ports_module
from tools.Network.modules import tls as tls_module
from tools.Network.modules import whois as whois_module


def analyze(target, port_specification='top', ping_count=4, timeout=8):
    """对目标执行一轮综合诊断，返回包含各阶段结果的字典。"""
    target = target.strip()
    if not target:
        raise common.NetworkError('the diagnostic target is empty.')
    scheme, host, port, path = common.parse_target(target)
    if '://' not in target and scheme == 'https' and port == 443:
        url = 'https://' + target + path
    else:
        url = target if '://' in target else '%s://%s%s' % (scheme, host, path)

    report = {
        'target': target,
        'host': host,
        'url': url,
        'dns': None,
        'ping': None,
        'tcp': None,
        'tls': None,
        'http': None,
        'whois': None,
        'errors': [],
    }

    try:
        report['dns'] = dns.resolve(host)
    except common.NetworkError as error:
        report['errors'].append('DNS: %s' % error)

    try:
        report['ping'] = ping_module.ping(host, count=ping_count, timeout=2)
    except common.NetworkError as error:
        report['errors'].append('PING: %s' % error)

    try:
        report['tcp'] = ports_module.scan(host, port_specification, timeout=0.8)
    except common.NetworkError as error:
        report['errors'].append('PORT: %s' % error)

    try:
        report['tls'] = tls_module.inspect(host, port, timeout=timeout)
    except common.NetworkError as error:
        report['errors'].append('TLS: %s' % error)

    try:
        report['http'] = http_module.analyze(url, timeout=timeout)
    except common.NetworkError as error:
        report['errors'].append('HTTP: %s' % error)

    if not common.is_ipv4(host):
        try:
            report['whois'] = whois_module.lookup(host, timeout=timeout)
        except common.NetworkError as error:
            report['errors'].append('WHOIS: %s' % error)

    return report


def summarize(report):
    """把综合诊断结果整理为可直接打印的文本行。"""
    lines = []
    lines.append('Target      : %s' % report['target'])
    lines.append('Host        : %s' % report['host'])
    lines.append('URL         : %s' % report['url'])

    dns_result = report['dns']
    if dns_result:
        addresses = ', '.join(dns_result.get('A', []) or dns_result.get('PTR', []))
        lines.append('DNS         : %s' % (addresses or 'no address record'))
        if dns_result.get('CNAME'):
            lines.append('  CNAME     : %s' % ', '.join(dns_result['CNAME']))
        if dns_result.get('MX'):
            lines.append('  MX        : %s' % ', '.join(dns_result['MX'][:3]))
        lines.append('  Resolver  : %s' % dns_result.get('server', ''))
    else:
        lines.append('DNS         : failed')

    ping_result = report['ping']
    if ping_result:
        latency = ('avg %s' % common.format_seconds(ping_result['avg'] / 1000.0)
                   if ping_result['avg'] is not None else 'no reply')
        lines.append('ICMP        : %d/%d replies, %s, %s'
                     % (ping_result['received'], ping_result['sent'], latency,
                        '%.1f%% loss' % ping_result['loss']))
    else:
        lines.append('ICMP        : failed')

    tcp_result = report['tcp']
    if tcp_result is not None:
        open_ports = ', '.join('%d/%s' % (item['port'], item['service']) for item in tcp_result)
        lines.append('TCP Ports   : %s' % (open_ports or 'all probed ports are filtered'))
    else:
        lines.append('TCP Ports   : failed')

    tls_result = report['tls']
    if tls_result:
        lines.append('TLS         : %s, %s, expires in %s days, %s'
                     % (tls_result['version'],
                        tls_result['cipher'] or 'unknown cipher',
                        tls_result['days_left'],
                        'verified' if tls_result['verified'] else 'verification failed'))
        if tls_result['issuer_name']:
            lines.append('  Issuer    : %s' % tls_result['issuer_name'])
    else:
        lines.append('TLS         : not available')

    http_result = report['http']
    if http_result:
        lines.append('HTTP        : %d %s, %s, %s'
                     % (http_result['status'], http_result['reason'],
                        http_result['content_type'] or 'unknown type',
                        common.format_bytes(http_result['size'])))
        timing = http_result['timing']
        lines.append('  Timing    : TTFB %s, total %s'
                     % (common.format_seconds(timing['ttfb']),
                        common.format_seconds(timing['total'])))
        missing = http_module.missing_security_headers(http_result['security'])
        lines.append('  Security  : %s' % ('complete' if not missing else 'missing ' + ', '.join(missing)))
    else:
        lines.append('HTTP        : not available')

    whois_result = report['whois']
    if whois_result:
        fields = whois_result['fields']
        registrar = fields.get('registrar', '') or fields.get('org', '')
        expiry = (fields.get('expiry date', '') or fields.get('expiration date', '')
                  or fields.get('registry expiry date', ''))
        lines.append('WHOIS       : %s' % (registrar or whois_result['server']))
        if expiry:
            lines.append('  Expires   : %s' % expiry)
    else:
        lines.append('WHOIS       : not available')

    if report['errors']:
        lines.append('Errors      :')
        for error in report['errors']:
            lines.append('  - %s' % error)

    return lines
