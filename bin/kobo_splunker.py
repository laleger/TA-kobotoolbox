#!/usr/bin/python

import os
import sys
import time
import urllib2
import json
import base64
import splunk.entity as entity

# Global variables
debug_mode = 0
script_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.dirname(script_dir)
app_data_dir = app_dir + '/data/'
session_key = sys.stdin.readline().strip()

# Check for Splunk session key before going any further
if len(session_key) == 0:
    print_status('ERROR', 'Did not receive session key from splunkd, passAuth missing from inputs.conf?')
    sys.exit()

# Function to get API config stored in Splunk config file/password store
def get_api_config(api):
    if api == 'kobotoolbox':
        url_field = 'kobo_api_url'
        username_field = 'kobo_api_username'
        credential_entity = 'kobo_api_password'
    if api == 'splunk':
        url_field = 'splunk_ec_url'
        credential_entity = 'splunk_ec_token'

    username = ''

    try:
        kobotoolbox_config = entity.getEntity(['admin', 'conf-app'], 'kobotoolbox', namespace='TA-kobotoolbox', owner='nobody', sessionKey=session_key)
        credential = entity.getEntity(['admin', 'passwords'], credential_entity, namespace='TA-kobotoolbox', owner='nobody', sessionKey=session_key)        

        url = kobotoolbox_config[url_field]

        if api == 'kobotoolbox':
            username = kobotoolbox_config[username_field]
 
    except Exception, e:
        print_status('ERROR', "Could not get API config for %s: %s" % (api, str(e)))
        sys.exit()

    api_config = {'url': url, 'username': username, 'credential': credential['clear_password']}

    return api_config

# Function to make web requests to the KoBoToolbox and Splunk API's
def request_api(api,uri='',data=None):
    api_config = get_api_config(api)

    if api == 'kobotoolbox':
        auth_header = 'Authorization', b'Basic ' + base64.b64encode(api_config['username'] + b':' + api_config['credential'])
    if api == 'splunk':
        auth_header = 'Authorization', b'Splunk ' + api_config['credential']

    url = api_config['url'] + uri

    request = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    request.add_header(*auth_header)

    print_status('DEBUG', "%s API request: %s" % (api, url))

    try:
        api_response = json.load(urllib2.urlopen(request))
        #api_response = json.load(response.read())

    except Exception, e:
        print_status('ERROR', "Could not access API for %s: %s" % (api, str(e)))
        sys.exit()

    print_status('DEBUG', "%s API response: %s" % (api, json.dumps(api_response)))

    return api_response

# Function to print status messages depending on whether or not debug mode is enabled
def print_status(message_type,message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    if debug_mode == 1:
        print '%s %s: %s' % (timestamp, message_type, message)
    elif message_type != 'DEBUG':
        print '%s %s: %s' % (timestamp, message_type, message)

print_status('DEBUG', 'Getting list of active surveys from KoBoToolbox API')

# Get list of surveys from KoBoToolbox API
api_response = request_api('kobotoolbox')

# Loop through surveys
for survey in api_response:
    survey_id = str(survey['id'])
    lastid_file = app_data_dir + survey_id + '.lastid'
    submissions_uri = '/' + survey_id

    # See if a marker file exists that contains the id of the last submission read into Splunk, if so we will
    # send a query to the API to only show later survey submissions
    if os.path.isfile(lastid_file):
        f = open(lastid_file, 'r')
        last_id = f.readline().rstrip('\n')
        f.close()
        submissions_uri = submissions_uri + '?query={"_id": {"$gt": ' + last_id + '}}'
    
    print_status('DEBUG', 'Getting list of submissions for survey ' + survey['id_string'] + ' from KoboToolbox API')

    # Get list of survey submissions from KoBoToolbox API
    api_response = request_api('kobotoolbox', uri=submissions_uri)
 
    submission_count = len(api_response)
    print_status('INFO', 'Found ' + str(submission_count) + ' new submissions for survey ' + survey['id_string'])

    # Loop through survey submissions
    for submission in api_response:
        submission_id = str(submission['_id'])

        # Create a JSON object which will contain required Splunk metadata and survey submission data
        splunk_json = {}
        splunk_json['time'] = int(time.mktime(time.strptime(submission['_submission_time'], '%Y-%m-%dT%H:%M:%S')))
        splunk_json['sourcetype'] = 'kobotoolbox:submission'
        splunk_json['index'] = 'kobotoolbox'
        splunk_json['event'] = submission

        print_status('DEBUG', 'Sending submission to Splunk HTTP Event Collector: ' + json.dumps(splunk_json))

        # Submit JSON object to Splunk HTTP Event Collector
        request_api('splunk', data=json.dumps(splunk_json))
    
        # Write latest survey submission id to tracker file
        f = open(lastid_file, 'w+')
        f.write(submission_id)
        f.close()
