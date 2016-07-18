# `ephemeral-port-reserve`
Sometimes you need a networked program to bind to a port that can't be hard-coded.
Generally this is when you want to run several of them in parallel; if they all
bind to port 8080, only one of them can succeed.

The usual solution is the "port 0 trick". If you bind to port 0, your kernel will
find some arbitrary high-numbered port that's unused and bind to that. Afterward
you can query the actual port that was bound to if you need to use the port number
elsewhere. However, there are cases where the port 0 trick won't work. For example,
mysqld takes port 0 to mean "the port configured in my.cnf". Docker can bind your
containers to port 0, but uses its own implementation to find a free port which
races and fails in the face of parallelism.

`ephemeral-port-reserve` provides an implementation of the port 0 trick which
is reliable and race-free. You can use it like so:

```!bash
PORT="$(ephemeral-port-reserve)"
docker run -p 127.0.0.1:$PORT:5000 registry:2
```


`ephemeral-port-reserve` is a utility to bind to an ephemeral port, force it into
the `TIME_WAIT` state, and unbind it.

This means that further ephemeral port alloctions won't pick this "reserved" port,
but subprocesses can still bind to it explicitly, given that they use `SO_REUSEADDR`.
By default on linux you have a grace period of 60 seconds to reuse this port.
To check your own particular value:

```!bash
$ cat /proc/sys/net/ipv4/tcp_fin_timeout
60
```

**NOTE:** By default, the port returned is *specifically* for `localhost`, aka `127.0.0.1`.
If you bind instead to `0.0.0.0`, you may encounter a port conflict. If you need to
bind to a non-localhost IP, you can pass it as the first argument.
