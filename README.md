A utility to bind to an ephemeral port, force it into the TIME_WAIT state, and unbind it.

This means that further ephemeral port alloctions won't pick this "reserved" port,
but subprocesses can still bind to it explicitly, given that they use SO_REUSEADDR.
By default on linux you have a grace period of 60 seconds to reuse this port.
To check your own particular value:
$ cat /proc/sys/net/ipv4/tcp_fin_timeout
60
