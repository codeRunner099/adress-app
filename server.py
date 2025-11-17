import sqlite3
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import mimetypes

DB_PATH = "addresses.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS addresses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, street TEXT, zip TEXT, city TEXT)")
    conn.commit()
    conn.close()

class AddressHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_get(parsed.path)
        else:
            self.handle_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/addresses":
            self.handle_api_post()
        else:
            self.send_error(404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/addresses/"):
            self.handle_api_put(parsed.path)
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/addresses/"):
            self.handle_api_delete(parsed.path)
        else:
            self.send_error(404)

    def handle_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"
        file_path = "." + path
        if not os.path.isfile(file_path):
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body.decode("utf-8"))

    def handle_api_get(self, path):
        if path == "/api/addresses":
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT id, name, street, zip, city FROM addresses ORDER BY id")
            rows = cur.fetchall()
            conn.close()
            data = []
            for r in rows:
                data.append({"id": r[0], "name": r[1], "street": r[2], "zip": r[3], "city": r[4]})
            payload = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_error(404)

    def handle_api_post(self):
        body = self.read_json()
        name = body.get("name", "").strip()
        street = body.get("street", "").strip()
        zip_code = body.get("zip", "").strip()
        city = body.get("city", "").strip()
        if not name:
            self.send_error(400)
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO addresses (name, street, zip, city) VALUES (?, ?, ?, ?)", (name, street, zip_code, city))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        payload = json.dumps({"id": new_id}).encode("utf-8")
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_api_put(self, path):
        parts = path.rstrip("/").split("/")
        try:
            address_id = int(parts[2])
        except:
            self.send_error(400)
            return
        body = self.read_json()
        name = body.get("name", "").strip()
        street = body.get("street", "").strip()
        zip_code = body.get("zip", "").strip()
        city = body.get("city", "").strip()
        if not name:
            self.send_error(400)
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE addresses SET name=?, street=?, zip=?, city=? WHERE id=?", (name, street, zip_code, city, address_id))
        conn.commit()
        conn.close()
        self.send_response(204)
        self.end_headers()

    def handle_api_delete(self, path):
        parts = path.rstrip("/").split("/")
        try:
            address_id = int(parts[2])
        except:
            self.send_error(400)
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM addresses WHERE id=?", (address_id,))
        conn.commit()
        conn.close()
        self.send_response(204)
        self.end_headers()

def run():
    init_db()
    server = HTTPServer(("127.0.0.1", 8000), AddressHandler)
    print("Server läuft auf http://127.0.0.1:8000")
    server.serve_forever()

if __name__ == "__main__":
    run()
