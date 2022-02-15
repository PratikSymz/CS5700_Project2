#!/usr/bin/env python3

import sys

""" Constant set of fields to use for logging in to the server """
LOGIN_URL = '/accounts/login/'
NEXT_URL = '?next=/fakebook/'
HTTP_VERSION = 'HTTP/1.1'

""" Constant set of fields to use in HTTP request headers """
HOST_NAME_HEADER = 'Host: project2.5700.network'
CSRF_HEADER = 'Cookie: csrftoken='
SESSION_ID_HEADER = 'sessionid='
CONTENT_TYPE_HEADER = 'Content-Type: application/x-www-form-urlencoded'
CONTENT_LENGTH_HEADER = 'Content-Length: '
CONN_ALIVE_HEADER = 'Connection: keep-alive'

# MAX Message Buffer length
BUFFER_SIZE = 4096

""" Helper method to build HTTP GET request using the url, updated CSRF Token and Session ID. """
def build_GET_request(url, csrf_token, session_id):
    message_lines = [
        'GET ' + url + ' ' + HTTP_VERSION, 
        HOST_NAME_HEADER,
        CONN_ALIVE_HEADER
    ]
    
    cookie_message = ''
    if (not (csrf_token == '')):
        cookie_message += CSRF_HEADER + csrf_token
        if (not (session_id == '')):
            cookie_message += '; ' + SESSION_ID_HEADER + session_id
        message_lines.append(cookie_message)
    
    return '\r\n'.join(message_lines) + '\r\n\r\n'

""" Helper method to build the login HTTP POST request using the username, password and the updated CSRF Token. """
def build_login_message(username, password, csrf_token):
    content = ('username=' + username + '&' + 'password=' + password + '&' 
    + 'csrfmiddlewaretoken=' + csrf_token + '&' + 'next=%2Ffakebook%2F')
    
    message_lines = [
        'POST ' + LOGIN_URL + NEXT_URL + ' ' + HTTP_VERSION, 
        HOST_NAME_HEADER, 
        CSRF_HEADER + csrf_token, 
        CONTENT_TYPE_HEADER, 
        CONTENT_LENGTH_HEADER + str(len(content))
    ]
    
    # HTTP request payload
    return '\r\n'.join(message_lines) + '\r\n\r\n' + content + '\r\n\r\n'

""" Helper method to retrieve the initial CSRF Token for Login Homepage """
def get_CSRF_token(socket):
    # Send GET message and receive response from server
    http_message = build_GET_request(LOGIN_URL, '', '')
    response = request_respond(socket, http_message)
    
    # Split raw Headers and HTML data
    raw_headers, raw_HTML = parse_response(response)
    # Parse raw headers
    headers = parse_headers(raw_headers)
    
    return get_cookie_id(headers, 'csrftoken')

""" Helper method to send http request message to the server and retrieve the corresponding response """
def request_respond(socket, http_message):
    # Send message to server
    try: 
        socket.send(http_message)
    except:
        # IO Exception with socket stream
        close_stream(socket)
        sys.exit("LOL" + "\n")
    
    return socket.recv(BUFFER_SIZE)

""" Helper function to parse HTTP response to raw Headers and HTML data"""
def parse_response(response):
    sections = response.split('\r\n\r\n')
    # sections[0] - raw Headers, sections[1] - raw HTML data
    # The response is only HTTP Headers (i.e., just after log in)
    if (len(sections) < 2):
        return sections[0], ''
    
    return sections[0], sections[1]

""" Helper function to parse raw HTTP headers to key-value pair table """
def parse_headers(rawheaders):
    # Header dictionary
    headers = {}
    lines = rawheaders.splitlines()[1:]

    for line in lines:
        header = line.split(': ')
        # Add each header title and value to the dictionary
        # If header already exists - 'Set-Cookie' for CSRF and Session ID - Then merge the both
        if (header[0] in headers):
            headers[header[0]] = headers.get(header[0]) + '\n' + header[1]
        else:
            headers[header[0]] = header[1]
    
    return headers

""" Helper method to retrieve Cookie ID - CSRF or Session ID from the parsed headers """
def get_cookie_id(headers, cookie_type):
    # Retrieve the CSRF Token or Session ID
    cookie = headers['Set-Cookie']
    # Find first and last index of the csrf or session id
    cookie_start = cookie.find(cookie_type + '=') + len(cookie_type + '=')
    cookie_end = cookie.find(';', cookie_start)
    
    return cookie[cookie_start : cookie_end]

""" Helper method to retrieve response code from raw HTTP header information """
def get_response_code(raw_headers):
    # Default code: Server Error - try again
    response_code = 500
    if (len(raw_headers) > 0):
        response_code = int(raw_headers.splitlines()[0].split()[1])
    
    return response_code

""" Helper function to close socket """
def close_stream(socket):
    socket.close()
