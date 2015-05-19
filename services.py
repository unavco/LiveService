#!/usr/bin/env python

import socket
from flask import Flask
from flask import request
from functools import partial
import json

app = Flask(__name__)
SOCKET_PATH = "/home/nagios/var/rw/live"


def standardize_json(result, headers = None):
    """
    LiveService returns json with the headers first (if no columns are specified) 
    and then each row of data, like a csv file.  This function will
    turn this result into a more standard version of json
    """
    json_result = json.loads(result)
    if headers is None:
        headers = json_result.pop(0)
    # Get a partial that we can pass to map
    # This partial will have headers as the first argument always
    header_zip = partial(zip, headers)
    # Map the header_zip partial with the json_result
    # and map the result of this to dict to get a list of dicts
    #TODO: do we really need to convert back to a string here?
    #TODO: also, this seems a bit complicated
    return json.dumps(map(dict,map(header_zip, json_result)))


def livestatus_query(table, columns=None, filters=None, limit=None):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCKET_PATH)
    query = "GET %s\n" % table
    
    if columns is not None:
        query += "Columns: %s\n" % " ".join(columns)
        
    if filters is not None:
        for filter in filters:
            query += "Filter:%s\n" % filter
    
    if limit is not None:
        query += "Limit: %d\n" % limit
    
    query += "OutputFormat: json\n"
    query += "ResponseHeader: fixed16\n"
    app.logger.debug('Query: %s', query)
    s.send(query)
    s.shutdown(socket.SHUT_WR)
    
    header = s.recv(16)
    status, bytes = parse_header(header)
    body = s.recv(bytes)
    app.logger.debug('Response: %s', body)
    #TODO: make the standardize optional
    return standardize_json(body, columns), status

def parse_header(header):
    app.logger.debug("LiveService Header: %s", header)
    status = int(header[0:3])
    bytes = int(header[3:15])
    return (status, bytes)

# @app.route("/hosts")
# def get_hosts():
#     return livestatus_query("hosts", columns =  ("name",  "alias"))

# @app.route("/hostgroups")
# @app.route("/hostgroups/<hostgroup>")
# def get_hostgroups(hostgroup=None):
#     if hostgroup is not None:
#         filters = ("name = %s" % hostgroup,)
#     else: 
#         filter = None
#     return livestatus_query("hostgroups", columns = ("name", "members"), filters=filter)

@app.route("/<table>")
def get_livestatus(table):
    """
    Currently supports column, filter, and list arguments
    """
    #TODO: Validate the table name
    columns = request.args.getlist("column")
    if len(columns)==0:
        columns = None
    app.logger.debug("Columns: %s", columns)
    #TODO: currently the filters need to be entered like this:
    # name+%3D+admins, which is not very nice
    filters = request.args.getlist("filter")
    if len(filters)==0:
        filters = None
    app.logger.debug("Filters: %s", filters)
    limit = request.args.get("limit", None, type=int)
    app.logger.debug("Limit: %d", limit)
    return livestatus_query(table, columns, filters, limit)

if __name__ == '__main__':
    app.run(debug=True)

