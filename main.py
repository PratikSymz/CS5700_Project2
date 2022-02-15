import socket, ssl, argparse, sys, utils
from frontier_finder import FrontierFinder


""" Main class to manage the server login and subsequent message collection
    1. Initialize the ssl socket and connect to the project hostname and the port. 
    2. start(): This method is the main method that:
        a. Collects the CSRF Token from the server by making the first GET request from the raw header information
        b. Initiates server login by sending the username and password as payload
        c. Collects the new CSRF Token and Session ID from the raw headers
        d. Runs a loop until the flag list length is full (5)
        e. In each cycle, the program collects the response code from the HTTP response, repeats step c. and takes appropriate action
        f. After detecting a specific response, it sends a HTTP response with the next action, and the cycle repeats again.
        g. If in a specific cycle, the server send a 'Connection: close' request, the program reestablishes 
            the socket connection again and resumes the program.
    """
class WebCrawler:
    """ Constant set of fields to use in connecting with socket """
    BASE_URL = 'project2.5700.network'
    PORT_NO = 443 # Default for HTTP requests
   
    # The SSL Client Socket 
    client_socket_ssl = None

    # Crawlable links domain name
    DOMAIN_NAME = '/fakebook/'

    # Flag to maintain last url that was popped from the queue and eventually generated 5xx code
    url_last_seen = ''

    """ Initiate ssl socket connection """
    def __init__(self):
        try:
            # Set up Socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Wrap Socket in SSL format, based on script input
            # Set up Handshake to establish security attributes (cipher suite) and, a valid session to read/write application data
            WebCrawler.client_socket_ssl = ssl.wrap_socket(client_socket, ssl_version=ssl.PROTOCOL_TLS)
            
            # Connect with socket
            addr = WebCrawler.BASE_URL, WebCrawler.PORT_NO
            WebCrawler.client_socket_ssl.connect(addr)
        except:
            # Can't connect with socket
            utils.close_stream(WebCrawler.client_socket_ssl)
            sys.exit("Can't connect with socket! Timeout " + "\n")
    
    """ Main method: Refer Step 2 in comments """
    @staticmethod
    def start(username, password):
        # Get initial CSRF Token
        csrf_token = utils.get_CSRF_token(WebCrawler.client_socket_ssl)

        # Login using this CSRF token
        # HTTP 'POST' message to log in to the Fakebook server
        http_message = utils.build_login_message(username, password, csrf_token)
        
        # Send message to server and retrieve response
        response = utils.request_respond(WebCrawler.client_socket_ssl, http_message)
        # Split raw Headers and HTML data
        raw_headers, raw_HTML = utils.parse_response(response)
        # Parse raw headers and make a header table
        headers = utils.parse_headers(raw_headers)
        
        # Retrieve the new CSRF Token and Session ID after Login
        csrf_token = utils.get_cookie_id(headers, 'csrftoken')
        session_id = utils.get_cookie_id(headers, 'sessionid')

        while (len(FrontierFinder.flags_secret) < 5):
            # Check HTTP Status Code from the raw HTML data
            response_code = utils.get_response_code(raw_headers)

            # Handle Status Codes:
            # 1. 200 - Response OK
            if (response_code in range(200, 299 + 1)):
                # Parse the raw HTML data
                frontier_finder = FrontierFinder()
                frontier_finder.feed(raw_HTML)
                # Set request message as to crawl the links after successful HTML parsing
                http_message = WebCrawler.crawl_page(csrf_token, session_id)
            
            # 2. 301 - Moved Permanently and 302 - Not Found [Redirect]
            if (response_code in range(300, 399 + 1)):
                # Redirected to new page and retrieve new URL path
                new_url = headers['Location']
                # Set request message to redirect to new url path
                http_message = utils.build_GET_request(new_url, csrf_token, session_id)

            # 3. 403 - Forbidden and 404 - Not Found [Abandon URL]
            elif (response_code in range(400, 499 + 1)):
                # Ignore this response (as per the specification) and crawl next link in queue
                http_message = WebCrawler.crawl_page(csrf_token, session_id)
            
            # 4. 500 - Internal Server Error and 503 - Service Unavailable [Retry]
            elif (response_code in range(500, 599 + 1)):
                # In this case, try crawling again
                http_message = utils.build_GET_request(WebCrawler.url_last_seen, csrf_token, session_id)
            
            # Send http request messages to the server
            response = utils.request_respond(WebCrawler.client_socket_ssl, http_message)
            # Split raw Headers and HTML data
            raw_headers, raw_HTML = utils.parse_response(response)
            # Parse raw headers
            headers = utils.parse_headers(raw_headers)

            # Update CSRF Token and Session ID from the response headers
            if ('Set-Cookie' in headers):
                csrf_token = utils.get_cookie_id(headers, 'csrftoken')
                session_id = utils.get_cookie_id(headers, 'sessionid')

            # Before checking for connnection close, check if I already have all the flags
            # Save code from extra effort to reconnect with the socket
            if (FrontierFinder.flags_secret == 5): 
                break

            # Check for Connection CLOSE
            if (('Connection' in headers) and headers['Connection'] == 'close'):
                # Close current socket
                utils.close_stream(WebCrawler.client_socket_ssl)
                
                # Reestablish connection with the socket
                while True:
                    try:
                        # Set up Socket
                        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        # Wrap Socket in SSL format, based on script input
                        # Set up Handshake to establish security attributes (cipher suite) and, a valid session to read/write application data
                        WebCrawler.client_socket_ssl = ssl.wrap_socket(client_socket, ssl_version=ssl.PROTOCOL_TLS)
                        
                        # Connect with socket
                        addr = WebCrawler.BASE_URL, WebCrawler.PORT_NO
                        WebCrawler.client_socket_ssl.connect(addr)

                        # Once socket connection established, continue with web crawling
                        break
                    except:
                        # Can't connect with socket
                        pass
        
        # Flags complete
        print('\n'.join(FrontierFinder.flags_secret))
        # Close socket
        utils.close_stream(WebCrawler.client_socket_ssl)


    """ Helper method that returns the http message to crawl the next url in the queue
        At each step it checks if the url is a 'Fakebook' url,
            1. If yes, remove it from the queue and add it to the crawled links list, and then crawl this link
            2. If not, ignore and remove url from another website from the queue.
    """
    @staticmethod
    def crawl_page(csrf_token, session_id):
        # Crawl links until we find a link that we can crawl further - exit loop
        # Otherwise, remove the unrecognized url
        
        while (True):
            url = FrontierFinder.frontier_queue[0]
            WebCrawler.url_last_seen = url

            # We only crawl Fakebook links
            if (WebCrawler.DOMAIN_NAME in url):
                FrontierFinder.frontier_queue.pop(0)
                FrontierFinder.frontier_crawled.add(url)
                http_message = utils.build_GET_request(url, csrf_token, session_id)
                break

            else:
                FrontierFinder.frontier_queue.pop(0)
        
        return http_message


""" Script argument parser """
if __name__ == "__main__":
    parser = argparse.ArgumentParser('Project 2: Web Crawler')

    # Store Username and Password from terminal
    parser.add_argument('USERNAME', action='store', type=str, help='[username]')    # Store value from input
    parser.add_argument('PASSWORD', action='store', type=str, help='[password]')    # Store value from input

    args = parser.parse_args()
    # Pass args to start() methods
    WebCrawler()
    WebCrawler.start(str(args.USERNAME).strip(), str(args.PASSWORD).strip())
