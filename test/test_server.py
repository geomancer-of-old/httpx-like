from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys


class EchoHandler(BaseHTTPRequestHandler):
    # Silence default logging; we print our own compact line
    def log_message(self, fmt, *args):
        pass

    def _handle(self):
        # Log exactly what the client sent
        print(f"\n>>> {self.command} {self.path}  from {self.client_address[0]}")
        for k, v in self.headers.items():
            print(f"    {k}: {v}")

        # Pick a status code from the path so you can test 2xx/3xx/4xx/5xx:
        #   /200 -> 200, /301 -> 301, /404 -> 404, /500 -> 500
        try:
            code = int(self.path.strip("/").split("/")[0])
            if code < 100 or code > 599:
                code = 200
        except ValueError:
            code = 200

        body = f"status={code} method={self.command} path={self.path}\n".encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        # for 3xx, add a Location so redirects look real
        if 300 <= code < 400:
            self.send_header("Location", "/200")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    # Route all the methods your tool supports to the same handler
    do_GET = _handle
    do_HEAD = _handle
    do_OPTIONS = _handle
    do_DELETE = _handle
    # handy extras
    do_POST = _handle
    do_PUT = _handle


def main():
    host = "127.0.0.1"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer((host, port), EchoHandler)
    print(f"listening on http://{host}:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.server_close()


if __name__ == "__main__":
    main()
