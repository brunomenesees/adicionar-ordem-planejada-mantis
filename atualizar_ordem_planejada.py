"""
Automação: Atualizar campo 'Ordem_Plnj' no Mantis via API REST
---------------------------------------------------------------
Lê um arquivo CSV com as colunas:
  - Mantis        : ID da issue
  - Ordem Planejada: valor numérico da ordem de planejamento

Para cada linha, atualiza o campo customizado 'Ordem_Plnj' da issue via API.
"""

import csv
import requests
import sys
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIGURAÇÕES — altere conforme necessário
# ─────────────────────────────────────────────
MANTIS_URL  = "https://mantis.xcelis.com.br"      # URL base do servidor Mantis
API_TOKEN   = "SEU_TOKEN_AQUI"                                         # Token de API do Mantis
CSV_FILE    = "ordens.csv"                         # Caminho do arquivo CSV
CAMPO_NOME  = "Ordem_Plnj"                         # Nome exato do campo customizado
# ─────────────────────────────────────────────

API_BASE    = f"{MANTIS_URL}/api/rest"
HEADERS     = {
    "Authorization": API_TOKEN,
    "Content-Type":  "application/json"
}


def ler_csv(caminho: str) -> list[dict]:
    """Lê o CSV e retorna lista de dicts com 'id_issue' e 'ordem'."""
    registros = []

    if not os.path.exists(caminho):
        print(f"[ERRO] Arquivo CSV não encontrado: {caminho}")
        sys.exit(1)

    with open(caminho, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")

        # Valida colunas obrigatórias
        colunas = reader.fieldnames or []
        if "Mantis" not in colunas or "Ordem Planejada" not in colunas:
            print(f"[ERRO] O CSV deve conter as colunas 'Mantis' e 'Ordem Planejada'.")
            print(f"       Colunas encontradas: {colunas}")
            sys.exit(1)

        for linha in reader:
            id_issue = linha["Mantis"].strip()
            ordem    = linha["Ordem Planejada"].strip()

            if not id_issue or not ordem:
                print(f"[AVISO] Linha com dado vazio ignorada: {linha}")
                continue

            if not id_issue.isdigit() or not ordem.isdigit():
                print(f"[AVISO] Valores não numéricos ignorados — Mantis: '{id_issue}', Ordem: '{ordem}'")
                continue

            registros.append({"id_issue": id_issue, "ordem": ordem})

    return registros


def atualizar_campo_customizado(id_issue: str, ordem: str) -> bool:
    """
    Faz PATCH na issue informada atualizando o campo customizado Ordem_Plnj.
    Retorna True em caso de sucesso, False caso contrário.
    """
    url = f"{API_BASE}/issues/{id_issue}"

    payload = {
        "custom_fields": [
            {
                "field": {"name": CAMPO_NOME},
                "value": ordem
            }
        ]
    }

    try:
        response = requests.patch(url, json=payload, headers=HEADERS, timeout=15)

        if response.status_code in (200, 201, 204):
            return True
        else:
            print(f"  [FALHA] Issue #{id_issue} → HTTP {response.status_code}: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  [ERRO] Issue #{id_issue} → Não foi possível conectar ao servidor: {MANTIS_URL}")
        return False
    except requests.exceptions.Timeout:
        print(f"  [ERRO] Issue #{id_issue} → Timeout na requisição.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  [ERRO] Issue #{id_issue} → {e}")
        return False


def main():
    inicio = datetime.now()
    print("=" * 55)
    print("  Atualizar Ordem Planejada — Mantis API")
    print(f"  Início: {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 55)

    # Valida token configurado
    if API_TOKEN == "SEU_TOKEN_AQUI":
        print("[ERRO] Configure a variável API_TOKEN no script antes de executar.")
        sys.exit(1)

    registros = ler_csv(CSV_FILE)
    total = len(registros)

    if total == 0:
        print("[AVISO] Nenhum registro válido encontrado no CSV.")
        sys.exit(0)

    print(f"\n{total} issue(s) encontrada(s) no CSV. Iniciando atualização...\n")

    sucesso = 0
    falha   = 0

    for i, reg in enumerate(registros, start=1):
        id_issue = reg["id_issue"]
        ordem    = reg["ordem"]
        print(f"[{i:>3}/{total}] Issue #{id_issue} → {CAMPO_NOME} = {ordem} ... ", end="", flush=True)

        ok = atualizar_campo_customizado(id_issue, ordem)
        if ok:
            print("OK")
            sucesso += 1
        else:
            falha += 1

    fim = datetime.now()
    duracao = (fim - inicio).total_seconds()

    print("\n" + "=" * 55)
    print(f"  Concluído em {duracao:.1f}s")
    print(f"  Sucesso : {sucesso}")
    print(f"  Falha   : {falha}")
    print("=" * 55)


if __name__ == "__main__":
    main()
