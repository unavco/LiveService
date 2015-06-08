# LiveService
Restful services for interacting with Live Status.
This is a Python project built using Flask framework.
These sevices are being built for Python 2.7 release.

Current architecture - hard coded to run on nagios server<br>
TODO  - Make address and port the LiveStatus is configured to listen on
        Assumes that xinetd has been setup to pass request onto LiveStatus as shown in LiveStatus documentation
           -  xinetd has been setup to listen on 8080 on server to accept request - this should be configurable.
        Assume that flask server is accept request at localhost at port 5051.   This should also be configurable. 
