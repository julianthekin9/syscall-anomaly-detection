from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

PRODUCTS = {
    1: {"id": 1, "name": "Laptop", "price": 35000},
    2: {"id": 2, "name": "Keyboard", "price": 2500},
    3: {"id": 3, "name": "Mouse", "price": 1200},
    4: {"id": 4, "name": "Monitor", "price": 9000},
    5: {"id": 5, "name": "Headphones", "price": 4000},
    6: {"id": 6, "name": "Webcam", "price": 3000},
    7: {"id": 7, "name": "USB Hub", "price": 900},
    8: {"id": 8, "name": "SSD", "price": 5000},
}

USERS = {
    "alice": {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com"
    },
    "bob": {
        "id": 2,
        "name": "Bob",
        "email": "bob@example.com"
    },
    "charlie": {
        "id": 3,
        "name": "Charlie",
        "email": "charlie@example.com"
    }
}


@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    if username in USERS and password == "password":
        return jsonify({
            "success": True,
            "user_id": USERS[username]["id"],
            "token": "fake-token"
        })

    return jsonify({
        "success": False,
        "error": "invalid credentials"
    }), 401


@app.route("/api/logout", methods=["POST"])
def logout():

    return jsonify({
        "success": True
    })

@app.route("/api/profile")
def profile():

    return jsonify({
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com"
    })


@app.route("/api/users/<username>")
def get_user(username):

    user = USERS.get(username)

    if user is None:
        return jsonify({
            "error": "user not found"
        }), 404

    return jsonify(user)


@app.route("/api/products")
def products():

    return jsonify(
        list(PRODUCTS.values())
    )


@app.route("/api/products/<int:product_id>")
def product(product_id):

    product = PRODUCTS.get(product_id)

    if product is None:
        return jsonify({
            "error": "product not found"
        }), 404

    return jsonify(product)


@app.route("/api/search")
def search():

    query = request.args.get("q", "").lower()

    result = [
        product
        for product in PRODUCTS.values()
        if query in product["name"].lower()
    ]

    return jsonify(result)


@app.route("/api/cart")
def cart():

    return jsonify({
        "items": [
            {
                "product_id": 2,
                "quantity": 1
            }
        ],
        "total": 2500
    })


@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():

    data = request.get_json(silent=True) or {}

    return jsonify({
        "success": True,
        "product_id": data.get("product_id"),
        "quantity": data.get("quantity", 1)
    })


@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():

    data = request.get_json(silent=True) or {}

    return jsonify({
        "success": True,
        "removed": data.get("product_id")
    })


@app.route("/api/orders")
def orders():

    return jsonify([
        {
            "id": 1001,
            "status": "completed",
            "total": 2500
        },
        {
            "id": 1002,
            "status": "processing",
            "total": 9000
        }
    ])


@app.route("/api/orders/<int:order_id>")
def order(order_id):

    return jsonify({
        "id": order_id,
        "status": "processing",
        "items": [
            {
                "product_id": 4,
                "quantity": 1
            }
        ]
    })


@app.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json(silent=True) or {}

    return jsonify({
        "success": True,
        "order_id": 2001,
        "items": data.get("items", [])
    })



##################################################################################################



@app.route("/api/debug/process-info")
def debug_process_info():

    import ctypes

    libc = ctypes.CDLL(None)

    return jsonify({
        "success": True,
        "pid": libc.getpid(),
        "ppid": libc.getppid(),
        "uid": libc.getuid(),
        "euid": libc.geteuid(),
        "gid": libc.getgid(),
        "egid": libc.getegid()
    })

@app.route("/api/debug/network")
def debug_network():
    import socket

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(("127.0.0.1", port))
            connection, _ = server.accept()
            try:
                client.send(b"test")
                connection.recv(4)

            finally:
                connection.close()
        finally:
            client.close()

    finally:
        server.close()

    return {"status": "ok"}


@app.route("/api/debug/run")
def debug_run():

    data = request.get_json(silent=True) or {}

    command = data.get("command")

    if not command:
        return jsonify({
            "error": "command is required"
        }), 400

    allowed_commands = {
        "id": ["id"],
        "whoami": ["whoami"],
        "pwd": ["pwd"],
        "ls": ["ls"],
        "ls -la": ["ls", "-la"],
        "ps": ["ps"],
        "uname": ["uname", "-a"],
        "hostname": ["hostname"],
        "cat proc": ["cat", "/proc/self/status"],
        "cat environ": ["cat", "/proc/self/environ"],
        "mount": ["mount", "-t", "proc", "proc", "/mnt"],
        "ip addr": ["ip", "addr"]
    }

    if command not in allowed_commands:
        return jsonify({
            "error": "command is not allowed in this training endpoint"
        }), 403

    try:
        result = subprocess.run(
            allowed_commands[command],
            capture_output=True,
            text=True,
            timeout=3
        )

        return jsonify({
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "error": "command timeout"
        }), 500



if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )