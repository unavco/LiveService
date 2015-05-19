#!/usr/bin/env python

import socket
from flask import Flask

app = Flask(__name__)
SOCKET_PATH = '/home/nagios/var/rw/live'

def livestatus_query(query_string):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    s.send(query_string)
    s.send("OutputFormat: json\n")
    s.send("ResponseHeader: fixed16\n")
    s.shutdown(socket.SHUT_WR)
    return s.recv(100000000)


@app.route("/hosts")
def get_hosts():
    return livestatus_query("GET hosts\nColumns: name alias\n")

@app.route("/hostgroups")
@app.route("/hostgroups/<hostgroup>")
def get_hostgroups(hostgroup=None):
    if hostgroup is not None:
        filter = "Filter: name = %s\n" % hostgroup
    else: 
        filter = ""
    return livestatus_query("GET hostgroups\nColumns: name members\n%s" % filter)

if __name__ == '__main__':
    app.run(debug=True)

