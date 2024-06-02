import threading
import socket
import os
import hashlib
import datetime

# Proxy settings
LISTENING_ADDR = "0.0.0.0"
LISTENING_PORT = 8080
FORWARD_PORT = 80
CACHE_DIR = "./cache"
FILTERED_DOMAINS_FILE = "filtered_domains.txt"
LOG_FILE = "proxy_log.txt"

PASS_DICT = {}

ALLOWED_METHODS = ["GET", "HEAD", "POST", "OPTIONS"]

REQUEST_BODY_EXPECTED_METHODS = ["POST"]
SUCCESSFUL_RESPONSE_BODY_ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
SUCCESSFUL_RESPONSE_BODY_EXPECTED_METHODS = ["GET", "POST"]
CACHE_ALLOWED = ["GET", "HEAD"]

LOGIN_PAGE = b"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<html>
<body>
<h2>Login</h2>
<form method="POST" action="/">
  Token: <input type="text" name="token">
  <input type="submit" value="Submit">
</form>
</body>
</html>
"""

# Tokens
TOKEN_NO_FILTER = "8a21bce200"
TOKEN_ENABLE_FILTER = "51e2cba401"

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

cache_lock = threading.Lock()

class ProxyCore:
    def __init__(self, log_callback=None):
        self.proxy_thread = None
        self.proxy_running = False
        self.log_callback = log_callback
        self.filtered_domains = self.load_filtered_domains()

    def log(self, message):
        log_message = f"{datetime.datetime.now()} - {message}"
        with open(LOG_FILE, "a") as log_file:
            log_file.write(log_message + "\n")
        print(log_message)
        if self.log_callback:
            self.log_callback(log_message)

    def start_proxy(self):
        if not self.proxy_running:
            self.proxy_running = True
            self.proxy_thread = threading.Thread(target=self.run_proxy)
            self.proxy_thread.start()
            self.log("Proxy server started.")

    def stop_proxy(self):
        if self.proxy_running:
            self.proxy_running = False
            self.log("Proxy server stopped.")

    def run_proxy(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((LISTENING_ADDR, LISTENING_PORT))
            server_socket.listen(5)
            self.log(f"Listening on {LISTENING_ADDR}:{LISTENING_PORT}")

            while self.proxy_running:
                try:
                    self.log("Waiting for connections...")
                    client_socket, addr = server_socket.accept()
                    self.log(f"Accepted connection from {addr}")
                    client_handler = threading.Thread(
                        target=self.handle_http_client, args=(client_socket, addr)
                    )
                    client_handler.start()
                except Exception as e:
                    self.log(f"Error accepting connections: {e}")
                    break

    def handle_http_client(self, client_socket, addr):
        try:
            request = self.receive_full_request(client_socket)
            if not request:
                client_socket.close()
                return

            http_request = HTTPRequest(request)
            METHOD = http_request.method
            HOST = http_request.headers.get("Host")
            REQUEST_HAS_BODY = http_request.body is not None and len(http_request.body) > 0

            client_ip = addr[0]
            if client_ip not in PASS_DICT:
                # If client is not authenticated, send login page
                if METHOD == "POST":
                    # Handle token submission
                    token = self.extract_token_from_body(http_request.body)
                    self.log(f"Received token from {client_ip}: {token}")
                    if token == TOKEN_NO_FILTER:
                        PASS_DICT[client_ip] = [False, http_request]
                        self.log(f"Client {client_ip} authenticated with no filtering.")
                    elif token == TOKEN_ENABLE_FILTER:
                        PASS_DICT[client_ip] = [True, http_request]
                        self.log(f"Client {client_ip} authenticated with filtering.")
                    else:
                        self.log(f"Client {client_ip} provided an invalid token.")
                        client_socket.send(LOGIN_PAGE)
                        client_socket.close()
                        return
                else:
                    client_socket.send(LOGIN_PAGE)
                    client_socket.close()
                    return

            # Check if filtering is enabled for the client
            filter_enabled = PASS_DICT.get(client_ip)[0]
            http_request = PASS_DICT.get(client_ip)[1]

            if filter_enabled and any(
                filtered_domain in HOST for filtered_domain in self.filtered_domains
            ):
                client_socket.send(b"HTTP/1.1 401 Unauthorized\r\n\r\n")
                self.log(f"Blocked request to {HOST} from {addr}")
                client_socket.close()
                return

            if METHOD == "CONNECT":
                self.handle_https_tunnel(client_socket, http_request)
                return

            if METHOD not in ALLOWED_METHODS:
                client_socket.send(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
                self.log(f"Blocked {METHOD} request to {HOST} from {addr}")
                client_socket.close()
                return

            if METHOD in REQUEST_BODY_EXPECTED_METHODS and not REQUEST_HAS_BODY:
                client_socket.send(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
                self.log(f"Bad request from {addr} - {METHOD} request with no body.")
                client_socket.close()
                return

            if METHOD not in REQUEST_BODY_EXPECTED_METHODS and REQUEST_HAS_BODY:
                client_socket.send(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
                self.log(f"Bad request from {addr} - {METHOD} request with body.")
                client_socket.close()
                return

            if METHOD in CACHE_ALLOWED:
                cache_key = hashlib.md5(http_request.raw_request).hexdigest()
                cache_path = os.path.join(CACHE_DIR, cache_key)
                if self.read_from_cache(client_socket, cache_path, HOST, addr):
                    return
                self.forward_request(client_socket, http_request, cache_path=cache_path)
            else:
                self.forward_request(client_socket, http_request, None)

            client_socket.close()
        except Exception as e:
            self.log(f"Error handling HTTP client: {e}")
            client_socket.close()

    def forward_request(self, client_socket, http_request, cache_path):
        HOST = http_request.headers.get("Host")
        RAW_REQUEST = http_request.raw_request
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as forward_socket:
                forward_socket.connect((HOST, FORWARD_PORT))
                forward_socket.sendall(RAW_REQUEST)
                self.forward_response(
                    forward_socket, client_socket, http_request, cache_path
                )
        except Exception as e:
            self.log(f"Error forwarding request: {e}")
            client_socket.close()

    def forward_response(self, forward_socket, client_socket, http_request, cache_path):
        try:
            response = b""
            while b"\r\n\r\n" not in response:
                response += forward_socket.recv(4096)

            http_response = HTTPResponse(response)

            METHOD = http_request.method
            RAW_HEADERS = http_response.raw_headers
            RAW_BODY = http_response.raw_body
            SUCCESSFUL_RESPONSE = int(http_response.status) < 400
            RESPONSE_HAS_BODY = http_response.body is not None and len(http_response.body) > 0

            if METHOD not in SUCCESSFUL_RESPONSE_BODY_ALLOWED_METHODS and SUCCESSFUL_RESPONSE and RESPONSE_HAS_BODY:
                self.log("Successful response body not allowed but found.")
                client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
                return

            if METHOD in SUCCESSFUL_RESPONSE_BODY_EXPECTED_METHODS and SUCCESSFUL_RESPONSE and not RESPONSE_HAS_BODY:
                self.log("Successful response body expected but not found.")
                client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
                return

            # If caching is enabled, use the cache_path to save the response
            if cache_path:
                with cache_lock:
                    with open(cache_path, "wb") as cache_file:
                        client_socket.send(RAW_HEADERS + b"\r\n\r\n")
                        cache_file.write(RAW_HEADERS + b"\r\n\r\n")
                        if RAW_BODY:
                            client_socket.send(RAW_BODY)
                            cache_file.write(RAW_BODY)
                        for rest_of_body in range(len(RAW_BODY)):
                            data = forward_socket.recv(min(4096, rest_of_body))
                            if not data:
                                break
                            client_socket.send(data)
                            cache_file.write(data)
            else:
                # Forward the response without caching
                client_socket.send(RAW_HEADERS + b"\r\n\r\n")
                if RAW_BODY:
                    client_socket.send(RAW_BODY)
                for rest_of_body in range(len(RAW_BODY)):
                    data = forward_socket.recv(min(4096, rest_of_body))
                    if not data:
                        break
                    client_socket.send(data)
        except Exception as e:
            self.log(f"An error occurred while forwarding and possibly caching: {e}")
        finally:
            client_socket.close()

    def handle_https_tunnel(self, client_socket, http_request):
        try:
            host, port = http_request.path.split(':')
            port = int(port)
            self.log(f"Handling HTTPS tunnel for {host}:{port}")

            if any(filtered_domain in host for filtered_domain in self.filtered_domains):
                client_socket.send(b"HTTP/1.1 401 Unauthorized\r\n\r\n")
                self.log(f"Blocked HTTPS request to {host}")
                client_socket.close()
                return

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as forward_socket:
                forward_socket.connect((host, port))
                client_socket.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                self.tunnel_data(client_socket, forward_socket)
        except Exception as e:
            self.log(f"Error handling HTTPS tunnel: {e}")
            client_socket.close()

    def tunnel_data(self, client_socket, forward_socket):
        try:
            client_socket.setblocking(0)
            forward_socket.setblocking(0)
            while True:
                data_from_client = self.recv_data(client_socket)
                if data_from_client:
                    forward_socket.sendall(data_from_client)
                data_from_server = self.recv_data(forward_socket)
                if data_from_server:
                    client_socket.sendall(data_from_server)
        except Exception as e:
            self.log(f"Error tunneling data: {e}")
        finally:
            client_socket.close()
            forward_socket.close()

    def recv_data(self, sock):
        try:
            return sock.recv(4096)
        except socket.error:
            return b""

    def receive_full_request(self, client_socket):
        request_data = b""
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                request_data += data
                if b"\r\n\r\n" in request_data:
                    break
            except socket.timeout:
                break
        return request_data

    def add_host_to_filter(self, host):
        if host not in self.filtered_domains:
            self.filtered_domains.append(host)
            self.save_filtered_domains()
            self.log(f"Added {host} to filter list.")

    def remove_host_from_filter(self, host):
        if host in self.filtered_domains:
            self.filtered_domains.remove(host)
            self.save_filtered_domains()
            self.log(f"Removed {host} from filter list.")

    def get_filtered_hosts(self):
        return self.filtered_domains

    def generate_report(self, client_ip):
        try:
            with open(LOG_FILE, "r") as log_file:
                lines = log_file.readlines()
            report_lines = [line for line in lines if client_ip in line]
            report_content = "".join(report_lines)
            report_file_name = f"{client_ip}_report.txt"
            with open(report_file_name, "w") as report_file:
                report_file.write(report_content)
            self.log(f"Report generated for {client_ip}")
            return report_file_name
        except Exception as e:
            self.log(f"Error generating report: {e}")
            return None

    def read_from_cache(self, client_socket, cache_path, host, addr):
        cache_hit = False
        with cache_lock:
            if os.path.exists(cache_path):
                cache_hit = True

        if cache_hit:
            self.log(f"Cache hit for {host} - serving from cache.")
            with open(cache_path, "rb") as cache_file:
                while True:
                    chunk = cache_file.read(4096)
                    if not chunk:
                        break
                    client_socket.send(chunk)
            client_socket.close()
            self.log(f"Served cached response for {host} to {addr}")
            return True
        return False

    def load_filtered_domains(self):
        if os.path.exists(FILTERED_DOMAINS_FILE):
            with open(FILTERED_DOMAINS_FILE, "r") as file:
                return [line.strip() for line in file.readlines()]
        return []

    def save_filtered_domains(self):
        with open(FILTERED_DOMAINS_FILE, "w") as file:
            for domain in self.filtered_domains:
                file.write(f"{domain}\n")

    def extract_token_from_body(self, body):
        # Simple form parsing to extract the token
        if type(body) == bytes:
            body = body.decode()
        if body:
            if "token=" in body:
                self.log(body.split("token=")[1].split("&")[0])
                return body.split("token=")[1].split("&")[0]
        return None

class HTTPRequest:
    def __init__(self, request_text):
        self.headers = {}
        self.body = None
        self.raw_request = request_text
        self.parse_request(request_text)

    def parse_request(self, request_text):
        if b"\r\n\r\n" in request_text:
            header_part, self.body = request_text.split(b"\r\n\r\n", 1)
        else:
            header_part = request_text
            self.body = None

        request_lines = header_part.split(b"\r\n")
        self.raw_requestline = request_lines[0].decode()
        self.method, self.path, self.version = self.raw_requestline.split()

        for line in request_lines[1:]:
            if line:
                key, value = line.decode().split(": ", 1)
                self.headers[key] = value


class HTTPResponse:
    def __init__(self, response_text):
        self.headers = {}
        self.raw_headers = None
        self.body = None
        self.raw_body = None
        self.raw_response = response_text
        self.parse_response(response_text)

    def parse_response(self, response_text):
        if b"\r\n\r\n" in response_text:
            header_part, self.raw_body = response_text.split(b"\r\n\r\n", 1)
        else:
            header_part = response_text
            self.raw_body = None

        self.raw_headers = header_part
        response_lines = header_part.split(b"\r\n")
        self.raw_statusline = response_lines[0].decode()

        self.version, self.status, self.reason = self.raw_statusline.split(" ", 2)

        for line in response_lines[1:]:
            if line:
                key, value = line.decode().split(": ", 1)
                self.headers[key] = value
        self.body = self.raw_body.decode() if self.raw_body else None

