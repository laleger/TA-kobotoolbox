# TA-kobotoolbox

Splunk Technology Add-on (TA) for KoBoToolbox

NOTE: This TA makes use of the Splunk HTTP Event Collector and the new passwords.conf file and therefore requires Splunk version 6.3

## Installation instructions

1. Install App tgz file via Splunk web or manually untar in $SPLUNK_HOME/etc/apps and restart Splunk
2. Add HTTP Event Collector token which grants access to index "kobotoolbox" - See http://docs.splunk.com/Documentation/Splunk/6.3.0/Data/UsetheHTTPEventCollector
3. Go to Manage Apps and choose action to "Set up" TA-kobotoolbox
4. Enter your KoBoToolbox user credentials and EC token and then check box to Enable Scripted Input

## App sourcetypes

* kobotoolbox:status - Provides status from the main kobo_splunker.py script, additional verbosity can be enabled by changing the debug variable value to 1
* kobotoolbox:submission - Provides raw json data from survey submissions

Enjoy! If you have any questions or recommendations on how this TA could be improved, please contact me at lance@datageek.org

