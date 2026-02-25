"""
Endpoint de autenticação simples.
Valida a senha contra a variável de ambiente APP_PASSWORD.
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/api/auth", methods=["POST"])
def auth():
    app_password = os.environ.get("APP_PASSWORD", "")
    if not app_password:
        return jsonify({"erro": "APP_PASSWORD não está configurada no servidor."}), 500

    data = request.get_json(silent=True) or {}
    senha = data.get("senha", "")

    if senha == app_password:
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "erro": "Senha incorreta."}), 401
