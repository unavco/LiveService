# LiveService
Restful services for interacting with Live Status.
This is a Python project built using Flask framework.
These sevices are being built for Python 2.7 release.

Current architecture - hard coded to run on nagios server<br>
<br>
Assumes that xinetd has been setup to pass request onto LiveStatus as shown in LiveStatus documentation<br>
-  xinetd has been setup to listen on 8080 on server to accept request - this should be configurable.<br>
TODO  - Make the address and port that LiveStatus listens on configurable<br>
<br>
-  Service.py currently assumes that flask web service server accepts request at localhost at port 5051.<br>
TODO   - The server address and port of server should also be configurable. 
