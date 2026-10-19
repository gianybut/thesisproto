"""This server's own address on the local network, for connecting the phone app.

The web app shows it on the Overview page ("Connect a phone"), so nobody has to run ipconfig
to find what to type into the phone's sign-in screen. Signed-in users only, like every route.
"""

import ipaddress
import socket

from flask import Blueprint, jsonify, request

server_info_bp = Blueprint('server_info', __name__)


def _primary_ipv4():
    """The address of the interface the OS would route LAN traffic through.

    Connecting a UDP socket sends nothing; it only makes the OS pick a source address. A
    private target is tried first so it works on a Wi-Fi network with no internet.
    """
    for target in ('10.255.255.255', '192.168.255.255', '8.8.8.8'):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target, 1))
            ip = s.getsockname()[0]
            if not ip.startswith(('127.', '0.')):
                return ip
        except OSError:
            continue
        finally:
            s.close()
    return None


def _other_ipv4():
    """Further private addresses (a second adapter, Ethernet plus Wi-Fi), best effort."""
    found = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            addr = ipaddress.ip_address(ip)
            if addr.is_private and not addr.is_loopback and not addr.is_link_local:
                found.add(ip)
    except OSError:
        pass
    return found


@server_info_bp.route('/info', methods=['GET'])
def server_info():
    port = request.host.rsplit(':', 1)[1] if ':' in request.host else '5000'
    primary = _primary_ipv4()
    others = sorted(_other_ipv4() - {primary})
    return jsonify({
        'port': int(port) if port.isdigit() else 5000,
        'address': f'http://{primary}:{port}' if primary else None,
        'other_addresses': [f'http://{ip}:{port}' for ip in others],
        'hostname': socket.gethostname(),
    }), 200
