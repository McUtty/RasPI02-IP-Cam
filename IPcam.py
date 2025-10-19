"""Simple MJPEG IP camera server using Picamera2.

This script configures the Raspberry Pi camera with a preview stream and serves
it over HTTP as an MJPEG stream. The configuration is based on the minimal
example provided by the Picamera2 documentation and can be adapted later for
additional requirements.
"""

from __future__ import annotations

import argparse
import logging
import ssl
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BufferedIOBase
from pathlib import Path
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput


class StreamingOutput(BufferedIOBase):
    """Holds the latest frame from the MJPEG encoder.

    The Picamera2 encoder writes frames to this object. Whenever a new JPEG
    frame is available, waiting HTTP clients are notified so they can retrieve
    the image.
    """

    def __init__(self) -> None:
        self.frame: bytes | None = None
        self.condition = Condition()

    def write(self, buf: bytes) -> int:
        """Receive encoded data from the camera encoder.

        The MJPEG encoder emits complete JPEG images, each starting with the
        JPEG start-of-image marker (0xFFD8). When such a marker is detected we
        store the frame and notify clients.
        """

        if buf.startswith(b"\xff\xd8"):
            with self.condition:
                self.frame = buf
                self.condition.notify_all()
        return len(buf)

    def writable(self) -> bool:
        """Report write capability for ``io.BufferedIOBase`` checks."""

        return True


output: StreamingOutput | None = None


class StreamingHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves a simple index page and the MJPEG stream."""

    PAGE = b"""\
<html>
<head>
<title>Raspberry Pi Camera</title>
</head>
<body>
<h1>Raspberry Pi Camera Stream</h1>
<img src="/stream.mjpg" width="640" height="480" />
</body>
</html>
"""

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        if self.path == "/":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(self.PAGE))
            self.end_headers()
            self.wfile.write(self.PAGE)
        elif self.path == "/stream.mjpg":
            if output is None:
                self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Camera not initialised")
                self.end_headers()
                return

            self.send_response(HTTPStatus.OK)
            self.send_header("Age", 0)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()

            while True:
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                if frame is None:
                    continue

                self.wfile.write(b"--FRAME\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", len(frame))
                self.end_headers()
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Suppress the default noisy logging to stderr."""

        logging.info("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format % args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Picamera2 MJPEG HTTPS server")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP to bind the HTTPS server")
    parser.add_argument("--port", type=int, default=8443, help="Port to bind the HTTPS server")
    parser.add_argument(
        "--cert",
        default="cert.pem",
        help="Path to the TLS certificate file (PEM)",
    )
    parser.add_argument(
        "--key",
        default="key.pem",
        help="Path to the TLS private key file (PEM)",
    )
    return parser.parse_args()


def create_ssl_context(cert_path: Path, key_path: Path) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    return context


def main() -> None:
    args = parse_args()

    logging.basicConfig(level=logging.INFO)

    cert_path = Path(args.cert)
    key_path = Path(args.key)
    if not cert_path.exists():
        raise FileNotFoundError(f"TLS certificate not found: {cert_path}")
    if not key_path.exists():
        raise FileNotFoundError(f"TLS private key not found: {key_path}")

    picam2 = Picamera2()
    camera_config = picam2.create_preview_configuration(
        main={"format": "XRGB8888", "size": (640, 480)}
    )
    picam2.configure(camera_config)

    global output
    output = StreamingOutput()

    picam2.start_recording(MJPEGEncoder(), FileOutput(output))

    address = (args.host, args.port)
    server = HTTPServer(address, StreamingHandler)

    ssl_context = create_ssl_context(cert_path, key_path)
    server.socket = ssl_context.wrap_socket(server.socket, server_side=True)

    scheme = "https"
    try:
        logging.info("Starting camera stream on %s://%s:%s", scheme, *address)
        server.serve_forever()
    finally:
        logging.info("Shutting down camera")
        picam2.stop_recording()
        picam2.close()
        server.server_close()


if __name__ == "__main__":
    main()
