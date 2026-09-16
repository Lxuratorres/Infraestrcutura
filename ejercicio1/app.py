from flask import Flask, jsonify
import socket
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "Hola desde Flask!",
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname())
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "app": "up and running"
    })

if __name__ == '__main__':
    # Usamos la variable de entorno o 0.0.0.0 por defecto
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    app.run(host=host, port=5000)