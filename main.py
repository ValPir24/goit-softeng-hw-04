import pathlib
import urllib.parse
import json
import socketserver
import http.server
import threading
from datetime import datetime

HOST = 'localhost'
HTTP_PORT = 3000
SOCKET_PORT = 5000
STORAGE_PATH = 'storage/data.json'

# HTTP Request Handler
class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {
            '/': 'index.html',
            '/message.html': 'message.html',
            '/style.css': 'style.css',
            '/logo.png': 'logo.png'
        }
        if self.path in routes:
            self.send_response(200)
            if self.path.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            elif self.path.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            elif self.path.endswith('.png'):
                self.send_header('Content-type', 'image/png')
            self.end_headers()
            with open(routes[self.path], 'rb') as file:
                self.wfile.write(file.read())
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)
        username = data.get('username', [''])[0]
        message = data.get('message', [''])[0]
        if username and message:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            message_data = {
                timestamp: {
                    'username': username,
                    'message': message
                }
            }
            self.save_to_storage(message_data)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Message received successfully')
        else:
            self.send_error(400, 'Bad Request')

    def save_to_storage(self, message_data):
        with open(STORAGE_PATH, 'r') as file:
            try:
                storage_data = json.load(file)
            except json.JSONDecodeError:
                storage_data = {}
        storage_data.update(message_data)
        with open(STORAGE_PATH, 'w') as file:
            json.dump(storage_data, file)

# Socket Server Handler
class SocketHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip().decode('utf-8')
        message_data = json.loads(data)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        message_data[timestamp] = {
            'username': message_data['username'],
            'message': message_data['message']
        }
        self.save_to_storage(message_data)

    def save_to_storage(self, message_data):
        with open(STORAGE_PATH, 'r') as file:
            try:
                storage_data = json.load(file)
            except json.JSONDecodeError:
                storage_data = {}
        storage_data.update(message_data)
        with open(STORAGE_PATH, 'w') as file:
            json.dump(storage_data, file)

# HTTP Server Thread
def http_server_thread():
    server_address = (HOST, HTTP_PORT)
    httpd = http.server.HTTPServer(server_address, HTTPRequestHandler)
    print(f"HTTP server running at http://{HOST}:{HTTP_PORT}")
    httpd.serve_forever()

# Socket Server Thread
def socket_server_thread():
    server_address = (HOST, SOCKET_PORT)
    with socketserver.UDPServer(server_address, SocketHandler) as server:
        print(f"Socket server running at {HOST}:{SOCKET_PORT}")
        server.serve_forever()

if __name__ == '__main__':
    # Create storage directory if not exists
    pathlib.Path('storage').mkdir(parents=True, exist_ok=True)

    # Start HTTP server thread
    http_thread = threading.Thread(target=http_server_thread)
    http_thread.start()

    # Start Socket server thread
    socket_thread = threading.Thread(target=socket_server_thread)
    socket_thread.start()

    # Wait for both threads to finish
    http_thread.join()
    socket_thread.join()
