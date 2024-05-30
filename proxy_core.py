import threading
import socket
import os
import hashlib
import datetime

# Proxy settings
LISTENING_ADDR = '0.0.0.0'
LISTENING_PORT = 8080
FORWARD_PORT = 80
CACHE_DIR = './cache'
FILTERED_DOMAINS_FILE = 'filtered_domains.txt'
LOG_FILE = "proxy_log.txt"

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
        with open(LOG_FILE, 'a') as log_file:
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
            self.log(f'Listening on {LISTENING_ADDR}:{LISTENING_PORT}')

            while self.proxy_running:
                try:
                    client_socket, addr = server_socket.accept()
                    self.log(f'Accepted connection from {addr}')
                    client_handler = threading.Thread(target=self.handle_http_client, args=(client_socket, addr))
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
            host = http_request.headers.get('Host')
            self.log(f"Received request from {addr} for {host}")

            if any(filtered_domain in host for filtered_domain in self.filtered_domains):
                client_socket.send(b"HTTP/1.1 401 Unauthorized\r\n\r\n")
                self.log(f"Blocked request to {host} from {addr}")
                client_socket.close()
                return

            if http_request.command == 'CONNECT':
                self.handle_https_tunnel(client_socket, http_request)
                return

            cache_key = hashlib.md5(request).hexdigest()
            cache_path = os.path.join(CACHE_DIR, cache_key)

            if self.read_from_cache(client_socket, cache_path, host, addr):
                return

            self.log(f"Cache miss for {host} - forwarding request.")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as forward_socket:
                forward_socket.connect((host, FORWARD_PORT))
                forward_socket.sendall(request)
                self.write_to_cache_and_forward(forward_socket, client_socket, cache_path)

            self.log(f"Cached response for {host}")
            client_socket.close()
        except Exception as e:
            self.log(f"Error handling HTTP client: {e}")
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
            return b''

    def receive_full_request(self, client_socket):
        client_socket.settimeout(5)
        request_data = b''
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                request_data += data
                if b'\r\n\r\n' in request_data:
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
            with open(LOG_FILE, 'r') as log_file:
                lines = log_file.readlines()
            report_lines = [line for line in lines if client_ip in line]
            report_content = "".join(report_lines)
            report_file_name = f"{client_ip}_report.txt"
            with open(report_file_name, 'w') as report_file:
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
            with open(cache_path, 'rb') as cache_file:
                while True:
                    chunk = cache_file.read(4096)
                    if not chunk:
                        break
                    client_socket.send(chunk)
            client_socket.close()
            self.log(f"Served cached response for {host} to {addr}")
            return True
        return False

    def write_to_cache_and_forward(self, forward_socket, client_socket, cache_path):
        try:
            # Receive the initial part of the response to parse headers
            response = b""
            while b"\r\n\r\n" not in response:
                response += forward_socket.recv(4096)
            
            # Parse the headers
            headers_end = response.index(b"\r\n\r\n") + 4
            headers = response[:headers_end]
            body_start = response[headers_end:]
            
            http_request = HTTPRequest(headers)
            content_length = int(http_request.headers.get('Content-Length', 0))
            
            # Write the headers to the cache and client
            with cache_lock:
                with open(cache_path, 'wb') as cache_file:
                    client_socket.send(headers)
                    cache_file.write(headers)
                    
                    # Write the initial part of the body to cache and client
                    if body_start:
                        client_socket.send(body_start)
                        cache_file.write(body_start)
                        content_length -= len(body_start)
                    
                    # Read the remaining content based on content length
                    while content_length > 0:
                        data = forward_socket.recv(min(4096, content_length))
                        if not data:
                            print("Connection closed prematurely")
                            break
                        client_socket.send(data)
                        cache_file.write(data)
                        content_length -= len(data)
                        print(data)
        except Exception as e:
            print(f"An error occurred: {e}")

    def load_filtered_domains(self):
        if os.path.exists(FILTERED_DOMAINS_FILE):
            with open(FILTERED_DOMAINS_FILE, 'r') as file:
                return [line.strip() for line in file.readlines()]
        return []

    def save_filtered_domains(self):
        with open(FILTERED_DOMAINS_FILE, 'w') as file:
            for domain in self.filtered_domains:
                file.write(f"{domain}\n")

class HTTPRequest:
    def __init__(self, request_text):
        self.headers = {}
        self.parse_request(request_text)

    def parse_request(self, request_text):
        request_lines = request_text.decode().split('\r\n')
        self.raw_requestline = request_lines[0]
        self.command, self.path, self.version = self.raw_requestline.split()
        for line in request_lines[1:]:
            if line:
                key, value = line.split(': ', 1)
                self.headers[key] = value

