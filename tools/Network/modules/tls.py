#  Copyright (c) 2024-2026. L.J.Afres, All rights reserved.

"""TLS / SSL 证书探测。

连接目标端口并读取对端证书，验证证书链，同时输出证书主体、
签发者、有效期、剩余天数、SAN 列表和协商使用的加密套件。
Windows 上 getpeercert() 常常返回空字典，这时回退到解析
DER 证书的兼容路径。
"""

import os
import socket
import ssl
import tempfile
import time

from tools.Network.modules import common

CERT_TIME_FORMAT = '%b %d %H:%M:%S %Y %Z'


class TLSError(common.NetworkError):
    """TLS 探测失败时抛出的错误。"""


def _decode_certificate(binary):
    """用标准库解码 DER 证书，返回与 getpeercert() 相同结构的字典。"""
    pem = ssl.DER_cert_to_PEM_cert(binary)
    handle, path = tempfile.mkstemp(suffix='.pem')
    try:
        with os.fdopen(handle, 'w') as certificate_file:
            certificate_file.write(pem)
        return ssl._ssl._test_decode_cert(path)
    except (ssl.SSLError, OSError):
        return {}
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _subject_dict(subject):
    """把证书主体转换为普通字典。"""
    result = {}
    for group in subject or ():
        for key, value in group:
            result.setdefault(key, value)
    return result


def _alt_names(certificate):
    """读取证书中的 subjectAltName 列表。"""
    names = certificate.get('subjectAltName', ())
    return [value for _, value in names]


def _days_left(not_after):
    """计算证书剩余有效天数。"""
    try:
        expires = time.mktime(time.strptime(not_after, CERT_TIME_FORMAT))
    except (ValueError, OverflowError):
        return None
    return int((expires - time.time()) // 86400)


def inspect(host, port=443, timeout=8):
    """连接主机并返回证书与加密套件信息。"""
    if not common.valid_host(host):
        raise TLSError("the host '%s' is invalid." % host)
    port = int(port)
    if not 1 <= port <= 65535:
        raise TLSError("the port '%d' is out of range." % port)

    try:
        connection = socket.create_connection((host, port), timeout=timeout)
    except OSError as error:
        raise TLSError("cannot connect to '%s:%d': %s." % (host, port, error))

    verified = True
    verification_error = ''
    try:
        context = ssl.create_default_context()
        try:
            tls = context.wrap_socket(connection, server_hostname=host)
        except ssl.SSLCertVerificationError as error:
            verified = False
            verification_error = str(error)
            connection.close()
            connection = socket.create_connection((host, port), timeout=timeout)
            insecure = ssl._create_unverified_context()
            tls = insecure.wrap_socket(connection, server_hostname=host)
        try:
            certificate = tls.getpeercert()
            binary = tls.getpeercert(binary_form=True)
            version = tls.version()
            cipher = tls.cipher()
        finally:
            tls.close()
    except ssl.SSLError as error:
        connection.close()
        raise TLSError("the TLS handshake with '%s:%d' failed: %s." % (host, port, error))
    except socket.timeout:
        connection.close()
        raise TLSError("the TLS handshake with '%s:%d' timed out." % (host, port))
    finally:
        try:
            connection.close()
        except OSError:
            pass

    if not certificate and binary:
        certificate = _decode_certificate(binary)

    subject = _subject_dict(certificate.get('subject', ()))
    issuer = _subject_dict(certificate.get('issuer', ()))
    return {
        'host': host,
        'port': port,
        'verified': verified,
        'verification_error': verification_error,
        'subject': subject,
        'issuer': issuer,
        'common_name': subject.get('commonName', ''),
        'issuer_name': issuer.get('commonName', '') or issuer.get('organizationName', ''),
        'not_before': certificate.get('notBefore', ''),
        'not_after': certificate.get('notAfter', ''),
        'days_left': _days_left(certificate.get('notAfter', '')),
        'serial': certificate.get('serialNumber', ''),
        'alt_names': _alt_names(certificate),
        'version': version or '',
        'cipher': cipher[0] if cipher else '',
        'cipher_bits': cipher[2] if cipher and len(cipher) > 2 else 0,
        'has_certificate': bool(certificate),
    }


def days_left(host, port=443, timeout=8):
    """只返回证书的剩余有效天数。"""
    info = inspect(host, port, timeout)
    return info['days_left']
