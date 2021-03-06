#!/usr/bin/env python

import socket
from flask import Flask
from flask import Request, request
from functools import partial
import json

from werkzeug.datastructures import ImmutableOrderedMultiDict

class OrderedRequest(Request):
    parameter_storage_class = ImmutableOrderedMultiDict

app = Flask(__name__)
app.request_class = OrderedRequest

SOCKET_HOST = "lsnag.int.unavco.org"
SOCKET_PORT = 8080



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



def get_bytes(s, bytes):
    """
    Read bytes from socket s and return when we get all of the bytes
    """
    if bytes<1024:
        read_bytes = bytes
    else:
        read_bytes = 1024
    buffer = ''
    while len(buffer) < bytes:
        buffer += s.recv(read_bytes)
        app.logger.debug(buffer)
        
    return buffer


def livestatus_query(table, columns=None,
                     filters=None, limit=None, stats=None,
                     normalize_results=True):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SOCKET_HOST, SOCKET_PORT))
    query = "GET %s\n" % table
    
    headers = []
    
    if columns is not None:
        query += "Columns: %s\n" % " ".join(columns)
        headers.extend(columns)
    
    if filters is not None:
        for filter in filters:
            query += "Filter:%s\n" % filter
    
    if stats is not None:
        for stat in stats:
            query += "Stats:%s\n" % stat
            headers.append(stat)
    
    if limit is not None:
        query += "Limit: %d\n" % limit
    
    query += "OutputFormat: json\n"
    query += "ResponseHeader: fixed16\n"
    app.logger.debug('Query: %s', query)
    s.send(query)
    s.shutdown(socket.SHUT_WR)
    
    header = s.recv(16)
    status, bytes = parse_header(header)
    if status != 200:
        normalize_results = False
        
    body = get_bytes(s, bytes)    
    
    app.logger.debug('Response: %s', body)

    if normalize_results is True:
        if len(headers) == 0:
            headers = None
        return standardize_json(body, headers), status
    else:
        return body, status

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
    
    stats = request.args.getlist("stats")
    if len(stats)==0:
        stats = None
    app.logger.debug("Stats: %s", stats)
    
    normalize_results = request.args.get("normalize", True)
    
    return livestatus_query(table, columns, filters, limit, stats, normalize_results)

if __name__ == '__main__':
    app.run("127.0.0.1", 5051, debug=True, use_reloader=True)

