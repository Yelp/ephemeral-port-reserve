#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import contextlib
import errno
import hashlib
from socket import error as SocketError
from socket import SO_REUSEADDR
from socket import socket
from socket import SOL_SOCKET

from pkg_resources import get_distribution

LOCALHOST = '127.0.0.1'


def reserve(ip=LOCALHOST, port=0):
    """Bind to an ephemeral port, force it into the TIME_WAIT state, and unbind it.

    This means that further ephemeral port alloctions won't pick this "reserved" port,
    but subprocesses can still bind to it explicitly, given that they use SO_REUSEADDR.
    By default on linux you have a grace period of 60 seconds to reuse this port.
    To check your own particular value:
    $ cat /proc/sys/net/ipv4/tcp_fin_timeout
    60

    By default, the port will be reserved for localhost (aka 127.0.0.1).
    To reserve a port for a different ip, provide the ip as the first argument.
    Note that IP 0.0.0.0 is interpreted as localhost.
    """
    port = int(port)
    with contextlib.closing(socket()) as s:
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            s.bind((ip, port))
        except SocketError as e:
            # socket.error: EADDRINUSE Address already in use
            if e.errno == errno.EADDRINUSE and port != 0:
                s.bind((ip, 0))
            else:
                raise

        # the connect below deadlocks on kernel >= 4.4.0 unless this arg is greater than zero
        s.listen(1)

        sockname = s.getsockname()

        # these three are necessary just to get the port into a TIME_WAIT state
        with contextlib.closing(socket()) as s2:
            s2.connect(sockname)
            sock, _ = s.accept()
            with contextlib.closing(sock):
                return sockname[1]


def get_port_from_hash_key(hash_key):
    """Take the value provided by --context and return a consistent port number"""
    hash_number = int(hashlib.sha1(hash_key.encode('utf8')).hexdigest(), 16)
    # clamp the port number between 33000 and 56000
    return 33000 + (hash_number % 25000)


def get_args_parser():  # pragma: no cover
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=get_distribution('ephemeral_port_reserve').version,
    )

    parser.add_argument(
        '-c', '--context',
        help='Optionally provide a string, used as a hash key to attempt to return a consistent port.',
    )

    parser.add_argument('ip', nargs='?', help='IP to reserve a port on.')
    parser.add_argument('port', nargs='?', help='preferred port to reserve. overrides --context if provided.')

    return parser


def main():  # pragma: no cover
    parser = get_args_parser()
    from sys import argv
    args = parser.parse_args(argv[1:])

    # hash --context into a valid port number
    port_from_context = get_port_from_hash_key(args.context) if args.context is not None else None

    port = reserve(
        ip=args.ip or LOCALHOST,
        port=args.port or port_from_context or 0,
    )

    print(port)


if __name__ == '__main__':
    exit(main())
