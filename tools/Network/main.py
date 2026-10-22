#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""Network 模块入口。

提供一组网络探测与分析命令：DNS 查询、ICMP 连通性、TCP 端口
探测、路由追踪、HTTP 站点分析、TLS 证书检查、whois 查询、本机
网络信息、带宽测速以及综合诊断。所有功能只使用标准库实现。
"""

import os

from loguru import logger
from prettytable import PrettyTable

from config import Tools_DIR, PageReader
from tools.__built_in__ import style
from tools.__built_in__.helptool import HelpTool
from tools.__built_in__.IOProcessor import read_input
from tools.Network.modules import analyze as analyze_module
from tools.Network.modules import common
from tools.Network.modules import dns
from tools.Network.modules import http
from tools.Network.modules import local
from tools.Network.modules import ping
from tools.Network.modules import ports
from tools.Network.modules import speed
from tools.Network.modules import tls
from tools.Network.modules import trace
from tools.Network.modules import whois

networkdir = os.path.join(Tools_DIR, 'Network')
COMMANDS = (
    ('help', 'print this help page.'),
    ('list', 'list the available commands.'),
    ('dns HOST [TYPE]', 'resolve the DNS records of a host.'),
    ('ping HOST [COUNT]', 'test the ICMP reachability of a host.'),
    ('port HOST [PORTS]', 'scan TCP ports (top, 80,443, 1-1024).'),
    ('trace HOST [HOPS]', 'trace the route to a host.'),
    ('http URL', 'analyze an HTTP/HTTPS response.'),
    ('tls HOST [PORT]', 'inspect the TLS certificate of a host.'),
    ('whois TARGET', 'query the whois record of a domain or IP.'),
    ('local', 'show the local network interfaces and ARP table.'),
    ('public', 'show the public IP address of this host.'),
    ('speed [URL]', 'measure the download speed and TCP latency.'),
    ('analyze TARGET', 'run a full diagnosis of a host or URL.'),
    ('@help', 'print this help page.'),
    ('@flush', 'flush the module cache.'),
    ('@exit', 'return to the ExecuteShell or Terminal.'),
)


def _require(arguments, count, usage):
    """检查参数个数，不足时抛出错误。"""
    if len(arguments) < count:
        raise common.NetworkError('incorrectly usage, please input %s.' % usage)


def _print_dns(host, record_type=None):
    """解析并打印 DNS 记录。"""
    if record_type:
        server, rcode, records = dns.query(host, record_type)
        style.key_value('Resolver', server)
        style.key_value('Status', rcode)
        if not records:
            style.warning("No '%s' record was found for '%s'." % (record_type.upper(), host))
            return
        table = PrettyTable(['Type', 'Name', 'TTL', 'Value'])
        for name_type, name, ttl, value in records:
            table.add_row([name_type, name, ttl, value])
    else:
        result = dns.resolve(host)
        style.key_value('Resolver', result.get('server', ''))
        table = PrettyTable(['Type', 'Value'])
        for name_type in ('A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'PTR'):
            for value in result.get(name_type, []):
                table.add_row([name_type, value])
    table.align = 'l'
    print(table, '\n')


def _print_ping(host, count=4):
    """执行 ping 并打印统计结果。"""
    result = ping.ping(host, count=count)
    style.key_value('Target', result['host'])
    style.key_value('Packets', '%d sent, %d received, %.1f%% loss'
                    % (result['sent'], result['received'], result['loss']))
    if result['rtts']:
        style.key_value('RTT', 'min %.1f ms, avg %.1f ms, max %.1f ms, jitter %.1f ms'
                        % (result['min'], result['avg'], result['max'], result['jitter']))
    else:
        style.warning('No ICMP reply was received.')


def _print_ports(host, specification=None):
    """扫描并打印开放的 TCP 端口。"""
    style.muted('Scanning %s, this may take a while ...' % host)
    result = ports.scan(host, specification)
    if not result:
        style.warning("No open TCP port was found on '%s' in the given range." % host)
        return
    table = PrettyTable(['Port', 'Service', 'Latency', 'Banner'])
    table.align = 'l'
    for item in result:
        table.add_row([item['port'], item['service'],
                       '%.0f ms' % (item['latency'] * 1000), item['banner']])
    print(table, '\n')


def _print_trace(host, max_hops=30):
    """追踪路由并打印每一跳。"""
    result = trace.trace(host, max_hops=max_hops)
    table = PrettyTable(['Hop', 'Address', 'Average RTT'])
    table.align = 'l'
    for hop in result['hops']:
        average = '--' if hop['average'] is None else '%.1f ms' % hop['average']
        table.add_row([hop['hop'], hop['address'], average])
    print(table, '\n')
    if not result['reached']:
        style.warning('The destination was not reached within %d hops.' % max_hops)


def _print_http(url):
    """分析并打印 HTTP 响应。"""
    result = http.analyze(url)
    for line in http.summarize(result):
        style.info(line)
    table = PrettyTable(['Header', 'Value'])
    table.align = 'l'
    for name in ('server', 'content-type', 'content-length', 'content-encoding',
                 'cache-control', 'location'):
        if name in result['headers']:
            table.add_row([name, result['headers'][name]])
    print('')
    print(table, '\n')


def _print_tls(host, port=443):
    """检查并打印 TLS 证书信息。"""
    result = tls.inspect(host, port)
    style.key_value('Endpoint', '%s:%d' % (result['host'], result['port']))
    style.key_value('Protocol', result['version'])
    style.key_value('Cipher', '%s (%d bits)' % (result['cipher'], result['cipher_bits']))
    style.key_value('Verified', 'yes' if result['verified'] else 'no')
    if result['verification_error']:
        style.error(result['verification_error'])
    style.key_value('Subject', result['common_name'])
    style.key_value('Issuer', result['issuer_name'])
    style.key_value('Validity', '%s -> %s' % (result['not_before'], result['not_after']))
    if result['days_left'] is not None:
        color = 'green' if result['days_left'] > 30 else 'yellow'
        if result['days_left'] <= 0:
            color = 'red'
        style.key_value('Expires In', style.highlight('%d days' % result['days_left'], color))
    if result['alt_names']:
        style.key_value('Alt Names', ', '.join(result['alt_names'][:10]))
    print('')


def _print_whois(target):
    """查询并打印 whois 信息。"""
    result = whois.lookup(target)
    style.heading('WHOIS %s' % result['target'])
    for line in whois.summarize(result):
        style.info(line)
    print('')
    print(whois.raw_text(result), '\n')


def _print_local():
    """打印本机网络信息与 ARP 表。"""
    style.heading('Local Network')
    for line in local.summarize():
        style.info(line)
    entries = local.arp_table()
    if entries:
        print('')
        table = PrettyTable(['IP Address', 'MAC Address'])
        for entry in entries[:20]:
            table.add_row([entry['ip'], entry['mac']])
        print(table, '\n')


def _print_public():
    """打印出口公网 IP 信息。"""
    result = local.public_ip()
    style.key_value('Public IP', result['ip'])
    if result['org']:
        style.key_value('Organization', result['org'])
    location = ' '.join(item for item in (result['city'], result['region'], result['country']) if item)
    if location:
        style.key_value('Location', location)


def _print_speed(url=None):
    """执行下载测速与延迟测试。"""
    target = url or speed.SPEED_TEST_URL
    style.muted('Downloading test data from %s ...' % target)
    result = speed.download(target)
    style.key_value('Download', '%.2f Mbps' % result['mbps'])
    style.key_value('Data', '%s in %s'
                    % (common.format_bytes(result['bytes']),
                       common.format_seconds(result['seconds'])))
    handshake = speed.latency(common.parse_target(target)[1], 443)
    style.key_value('Latency', 'avg %.1f ms, min %.1f ms, jitter %.1f ms'
                    % (handshake['avg'] * 1000, handshake['min'] * 1000,
                       handshake['jitter'] * 1000))


def _print_analyze(target):
    """执行综合诊断并打印结果。"""
    report = analyze_module.analyze(target)
    for line in analyze_module.summarize(report):
        style.info(line)
    print('')


def _list_commands():
    """打印命令列表。"""
    table = PrettyTable(['Command', 'Description'])
    table.align = 'l'
    for command, description in COMMANDS:
        table.add_row([command, description])
    print(table, '\n')


def run():
    """运行 Network 模块的交互式界面。"""
    style.banner('TSL-SYSTEM Network Module', width=37)
    style.muted("Input 'help' to list the available commands, '@exit' to leave.")
    while True:
        try:
            command = read_input(style.prompt('(network) >> '), 'terminal', strip=True)
            if not command:
                continue
            tokens = command.split()
            name = tokens[0].lower()
            arguments = tokens[1:]
            logger.debug("Network Module received a command. [CMDINFO:('%s')]" % command)

            if name in ('help', '@help'):
                HelpTool(networkdir, PageReader, 'network')
            elif name in ('list', 'commands', '@available'):
                _list_commands()
            elif name == 'dns':
                _require(arguments, 1, 'dns HOST [TYPE]')
                _print_dns(arguments[0], arguments[1] if len(arguments) > 1 else None)
            elif name == 'ping':
                _require(arguments, 1, 'ping HOST [COUNT]')
                _print_ping(arguments[0], int(arguments[1]) if len(arguments) > 1 else 4)
            elif name == 'port':
                _require(arguments, 1, 'port HOST [PORTS]')
                _print_ports(arguments[0], arguments[1] if len(arguments) > 1 else None)
            elif name == 'trace':
                _require(arguments, 1, 'trace HOST [HOPS]')
                _print_trace(arguments[0], int(arguments[1]) if len(arguments) > 1 else 30)
            elif name == 'http':
                _require(arguments, 1, 'http URL')
                _print_http(arguments[0])
            elif name == 'tls':
                _require(arguments, 1, 'tls HOST [PORT]')
                _print_tls(arguments[0], int(arguments[1]) if len(arguments) > 1 else 443)
            elif name == 'whois':
                _require(arguments, 1, 'whois TARGET')
                _print_whois(arguments[0])
            elif name == 'local':
                _print_local()
            elif name == 'public':
                _print_public()
            elif name == 'speed':
                _print_speed(arguments[0] if arguments else None)
            elif name == 'analyze':
                _require(arguments, 1, 'analyze TARGET')
                _print_analyze(arguments[0])
            elif name in ('@exit', 'exit', 'quit'):
                print('')
                break
            elif name == '@flush':
                from sysmgr import TempManager
                TempManager().Flush('Network Module')
            else:
                style.error("NameError:command '%s' is not defined in Network Module." % tokens[0])
        except common.NetworkError as error:
            logger.warning("Network command failed. [NETWORKINFO:('%s')]" % error)
            style.error('NetworkError:%s' % error)
        except KeyboardInterrupt:
            print('\nCtrl-C')
            continue
        except (ValueError, IndexError) as error:
            style.error('%s:%s' % (type(error).__name__, error))
