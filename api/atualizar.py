"""
Vercel Serverless Function (Python/Flask)
Recebe upload de CSV e atualiza o campo Ordem_Plnj no Mantis via API REST.
O token de autenticação é lido da variável de ambiente MANTIS_API_TOKEN.
"""

import csv
import io
import os

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MANTIS_URL = "https://mantis.xcelis.com.br/mantis"
CAMPO_NOME = "Ordem_Plnj"
API_BASE   = f"{MANTIS_URL}/api/rest"


@app.route("/api/atualizar", methods=["POST"])
def atualizar():
    api_token = os.environ.get("MANTIS_API_TOKEN", "")
    if not api_token:
        return jsonify({"erro": "MANTIS_API_TOKEN não está configurado no servidor."}), 500

    if "csv" not in request.files:
        return jsonify({"erro": "Nenhum arquivo CSV foi enviado."}), 400

    file = request.files["csv"]

    try:
        content = file.stream.read().decode("utf-8-sig")

        # Detecta separador automaticamente (;  ou  ,)
        amostra   = content[:2048]
        delimiter = ";" if amostra.count(";") >= amostra.count(",") else ","

        reader  = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        colunas = reader.fieldnames or []

        if "Mantis" not in colunas or "Ordem Planejada" not in colunas:
            return jsonify({
                "erro": (
                    f"Colunas inválidas. Encontradas: {colunas}. "
                    "O CSV deve ter as colunas 'Mantis' e 'Ordem Planejada' (separador ',' ou ';')."
                )
            }), 400

        headers_api = {
            "Authorization": api_token,
            "Content-Type":  "application/json"
        }

        resultados = []
        for linha in reader:
            id_issue = linha["Mantis"].strip()
            ordem    = linha["Ordem Planejada"].strip()

            if not id_issue or not ordem:
                resultados.append({
                    "issue": id_issue or "(vazio)",
                    "status": "ignorado",
                    "mensagem": "Linha com dado vazio."
                })
                continue

            if not id_issue.isdigit() or not ordem.isdigit():
                resultados.append({
                    "issue": id_issue,
                    "status": "ignorado",
                    "mensagem": "Valor não numérico."
                })
                continue

            payload = {
                "custom_fields": [
                    {"field": {"name": CAMPO_NOME}, "value": ordem}
                ]
            }

            try:
                resp = requests.patch(
                    f"{API_BASE}/issues/{id_issue}",
                    json=payload,
                    headers=headers_api,
                    timeout=12
                )

                if resp.status_code in (200, 201, 204):
                    resultados.append({
                        "issue": id_issue,
                        "status": "sucesso",
                        "mensagem": f"Ordem '{ordem}' aplicada com sucesso."
                    })
                else:
                    resultados.append({
                        "issue": id_issue,
                        "status": "falha",
                        "mensagem": f"HTTP {resp.status_code}: {resp.text[:150]}"
                    })

            except requests.exceptions.Timeout:
                resultados.append({
                    "issue": id_issue,
                    "status": "erro",
                    "mensagem": "Timeout ao chamar a API do Mantis."
                })
            except requests.exceptions.RequestException as e:
                resultados.append({
                    "issue": id_issue,
                    "status": "erro",
                    "mensagem": str(e)
                })

        sucesso  = sum(1 for r in resultados if r["status"] == "sucesso")
        ignorado = sum(1 for r in resultados if r["status"] == "ignorado")
        falha    = sum(1 for r in resultados if r["status"] in ("falha", "erro"))

        return jsonify({
            "total":      len(resultados),
            "sucesso":    sucesso,
            "falha":      falha,
            "ignorado":   ignorado,
            "resultados": resultados
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
