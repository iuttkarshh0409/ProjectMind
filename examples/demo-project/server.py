from http.server import HTTPServer, BaseHTTPRequestHandler
from config import PORT
from auth import AuthManager

# Responsibility: Entrypoint HTTP server routing and connection bootstrap
class TaskRequestHandler(BaseHTTPRequestHandler):
    # External Interfaces: /api/tasks, /api/users
    def do_GET(self):
        if self.path == "/api/tasks":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"tasks": []}')
        else:
            self.send_response(404)
            self.end_headers()

def run():
    # Exposing PORT
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, TaskRequestHandler)
    print(f"Server running on port {PORT}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
