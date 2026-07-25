"""
update_dasboard.py
Atualiza a planilha do Google Sheets com layout idêntico à imagem de referência.

OTIMIZAÇÃO: Tudo em 1 requisição batch_update (valores + formatação + merge + largura + bordas).
"""

import sqlite3
import random
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    import pygsheets
    USE_PYGSCHEETS = True
except ImportError:
    USE_PYGSCHEETS = False

BATCH_LIMIT = 500 # Limite de requisições por lote para a API do Google Sheets

# ==========================
# CONFIGURAÇÃO
# ==========================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DB_PATH = BASE_DIR / "data" / "dataBase.db"

TURMA_COLORS = [
    (0.80, 0.0, 0.0),     # Vermelho (cor da Turma 1 na imagem)
    (0.55, 0.80, 0.55),   # Verde
    (0.55, 0.70, 1.0),    # Azul claro
    (1.0, 0.85, 0.40),    # Amarelo
    (0.70, 0.60, 0.90),   # Roxo
    (0.50, 0.85, 0.75),   # Verde-água
    (1.0, 0.70, 0.45),    # Laranja
    (1.0, 0.55, 0.75),    # Rosa
    (0.40, 0.60, 0.90),   # Azul escuro
    (0.45, 0.75, 0.45),   # Verde claro
]

HEADER_GRAY = (0.647, 0.647, 0.647)   # ~ RGB(165,165,165) - Cinza claro para títulos
DARK_GRAY = (0.4, 0.4, 0.4)           # ~ RGB(102,102,102) - Cinza escuro para cabeçalhos
ZEBRA_GRAY = (0.902, 0.902, 0.902)    # ~ RGB(230,230,230) - Cinza zebrado
ZEBRA_WHITE = (1.0, 1.0, 1.0)         # Branco zebrado

# ==========================
# HELPERS
# ==========================

def col_to_letter(n):
    result = ""
    while n > 0:
        n -= 1
        result = chr(65 + (n % 26)) + result
        n //= 26
    return result


def month_abbr(month_num):
    meses = {
        1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
        7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ"
    }
    return meses.get(month_num, "???")


def bg(r, g, b):
    return {"red": r, "green": g, "blue": b}


def zebra_bg(row_0based):
    return bg(*ZEBRA_GRAY) if row_0based % 2 == 1 else bg(*ZEBRA_WHITE)


def text_fmt(font="Arial", size=10, bold=False, fg=None):
    fmt = {"fontFamily": font, "fontSize": size, "bold": bold}
    if fg:
        fmt["foregroundColor"] = fg
    return fmt


def txt_color(r, g, b):
    return {"red": r, "green": g, "blue": b, "alpha": 1.0}


def repeat_cell(sheet_id, start_row, end_row, start_col, end_col,
                fmt_fields="userEnteredFormat", **format_props):
    cell = {"userEnteredFormat": format_props}
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row,
                "endRowIndex": end_row,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col
            },
            "cell": cell,
            "fields": fmt_fields
        }
    }


# ==========================
# QUERY DE DADOS
# ==========================

def get_all_data(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT id, tema, meeting_date FROM meetings ORDER BY meeting_date ASC")
    encontros = []
    for row in cursor.fetchall():
        d = dict(row)
        d["meeting_date"] = datetime.strptime(d["meeting_date"], "%Y-%m-%d")
        encontros.append(d)

    cursor.execute("SELECT id, turma_name FROM turmas ORDER BY turma_name")
    turmas = [dict(row) for row in cursor.fetchall()]

    presencas = {}
    if encontros:
        enc_ids = [e["id"] for e in encontros]
        ph = ",".join(["?"] * len(enc_ids))
        cursor.execute(f"""
            SELECT c.turma_id, c.id AS crismando_id, a.meeting_id, a.status
            FROM attendance a
            INNER JOIN crismandos c ON c.id = a.crismando_id
            WHERE a.meeting_id IN ({ph})
            ORDER BY c.turma_id, c.id
        """, enc_ids)
        for row in cursor.fetchall():
            tid = row["turma_id"]
            cid = row["crismando_id"]
            mid = row["meeting_id"]
            presencas.setdefault(tid, {}).setdefault(cid, {})[mid] = row["status"]

    turmas_crismandos = {}
    for t in turmas:
        cursor.execute(
            "SELECT id, name FROM crismandos WHERE turma_id = ? ORDER BY name",
            (t["id"],)
        )
        turmas_crismandos[t["id"]] = [dict(r) for r in cursor.fetchall()]

    return encontros, turmas, presencas, turmas_crismandos


# ==========================
# MONTAGEM
# ==========================

def montar_planilha(aba, encontros, turmas, presencas, turmas_crismandos, turma_colors):
    n_enc = len(encontros)
    if n_enc == 0:
        aba.update_value("C1", "Nenhum encontro registrado.")
        return

    sheet_id = aba.id  # ID numérico da aba (usado nos GridRange)
    spreadsheet_id = aba.spreadsheet.id  # ID da planilha (usado no batch_update)
    col_pres = 4 + n_enc
    col_falt = 4 + n_enc + 1
    col_fjust = 4 + n_enc + 2
    num_cols = col_fjust

    meses_grupo = {}
    for i, e in enumerate(encontros):
        m = e["meeting_date"].month
        meses_grupo.setdefault(m, []).append(4 + i)

    turmas_info = []
    current_row = 4  # 1-based
    for turma_idx, turma in enumerate(turmas):
        tid = turma["id"]
        alunos = turmas_crismandos.get(tid, [])
        n_linhas = max(len(alunos), 1)  # reserva ao menos 1 linha, mesmo sem alunos
        turmas_info.append({
            "start_row": current_row,
            "end_row": current_row + n_linhas - 1,
            "turma_idx": turma_idx,
            "turma_id": tid,
            "alunos": alunos,
        })
        current_row += n_linhas

    last_data_row = current_row - 1 if turmas_info else 3
    total_rows = last_data_row

    # ================================================================
    # PASSO 0: Desfazer merges antigos (ANTES de escrever valores!)
    # ================================================================
    # aba.clear() só limpa valores, não desfaz merges de execuções anteriores.
    # Se isso não for feito ANTES de escrever os valores, um valor pode ser
    # gravado numa célula que ainda está presa num merge antigo mas não é mais
    # a célula-âncora — o Sheets simplesmente descarta esse valor (é o que
    # causava o nome da turma sumir, ficando só a cor de fundo).
    try:
        aba.client.sheet.batch_update(spreadsheet_id, [{
            "unmergeCells": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": aba.rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": aba.cols
                }
            }
        }])
    except Exception as e:
        print(f"  Aviso: falha ao desfazer merges antigos: {e}")

    # ================================================================
    # PASSO 1: Valores
    # ================================================================

    matriz = [[""] * num_cols for _ in range(total_rows)]

    matriz[0][0] = "Crisma Comunidade São Francisco de Assis"
    matriz[1][0] = "Controle de Presença - Semestre 2 - Pág. 1"
    
    matriz[0][col_pres - 1] = "Presenças"
    matriz[0][col_falt - 1] = "Faltas"
    matriz[0][col_fjust - 1] = "Faltas Just."

    for m, cols in meses_grupo.items():
        matriz[1][cols[0] - 1] = month_abbr(m)

    for i, e in enumerate(encontros):
        matriz[2][3 + i] = f"{e['meeting_date'].day:02d}"

    for info in turmas_info:
        sr = info["start_row"] - 1
        tid = info["turma_id"]
        tname = turmas[info["turma_idx"]]["turma_name"]
        alunos = info["alunos"]

        if not alunos:
            matriz[sr][0] = tname
            matriz[sr][2] = "(Nenhum aluno cadastrado)"
            continue

        for aluno_idx, aluno in enumerate(alunos):
            ri = sr + aluno_idx
            cid = aluno["id"]

            if aluno_idx == 0:
                matriz[ri][0] = tname
            matriz[ri][1] = aluno_idx + 1
            matriz[ri][2] = aluno["name"]

            aluno_p = presencas.get(tid, {}).get(cid, {})
            for enc_idx, enc in enumerate(encontros):
                status = aluno_p.get(enc["id"])
                if status is None:
                    matriz[ri][3 + enc_idx] = "-"
                else:
                    matriz[ri][3 + enc_idx] = {0: "P", 2: "FJ"}.get(status, "F")

            rs = f"D{info['start_row'] + aluno_idx}:{col_to_letter(3 + n_enc)}{info['start_row'] + aluno_idx}"
            matriz[ri][col_pres - 1] = f'=CONT.SE({rs};"P")'
            matriz[ri][col_falt - 1] = f'=CONT.SE({rs};"F")'
            matriz[ri][col_fjust - 1] = f'=CONT.SE({rs};"FJ")'

    data = [{
        "dataFilter": {"a1Range": f"A1:{col_to_letter(num_cols)}{total_rows}"},
        "values": matriz,
        "majorDimension": "ROWS"
    }]
    aba.client.sheet.values_batch_update_by_data_filter(
        aba.spreadsheet.id, data, parse=True
    )

    # ================================================================
    # PASSO 2: Formatação + Merge + Largura + Bordas
    # ================================================================

    requests = []

    # --- Desfaz todos os merges existentes primeiro ---
    # aba.clear() só limpa valores, não desfaz merges de execuções anteriores.
    # Sem isso, um merge novo pode sobrepor parcialmente um merge antigo
    # (ex: turma mudou de tamanho porque um aluno trocou de turma) e a API
    # rejeita com "You must select all cells in a merged range to merge or unmerge them".
    requests.append({
        "unmergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": aba.rows,
                "startColumnIndex": 0,
                "endColumnIndex": aba.cols
            }
        }
    })

    # --- Merges ---
    for m, cols in meses_grupo.items():
        if len(cols) > 1:
            requests.append({
                "mergeCells": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": cols[0] - 1, "endColumnIndex": cols[-1]},
                    "mergeType": "MERGE_ALL"
                }
            })

    for info in turmas_info:
        sr = info["start_row"] - 1
        er = info["end_row"]
        if er > sr + 1:
            requests.append({
                "mergeCells": {
                    "range": {"sheetId": sheet_id, "startRowIndex": sr, "endRowIndex": er, "startColumnIndex": 0, "endColumnIndex": 1},
                    "mergeType": "MERGE_ALL"
                }
            })

    # Merge Título Principal (A1:C1)
    requests.append({
        "mergeCells": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 3},
            "mergeType": "MERGE_ALL"
        }
    })
    # Merge Subtítulo (A2:C2)
    requests.append({
        "mergeCells": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 3},
            "mergeType": "MERGE_ALL"
        }
    })
    # Merge cabeçalhos de resumo (Y1:AA3)
    for col in range(col_pres - 1, col_fjust):
        requests.append({
            "mergeCells": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 3, "startColumnIndex": col, "endColumnIndex": col + 1},
                "mergeType": "MERGE_ALL"
            }
        })

    # --- Formatação ---
    # --- Formatação do Corpo da Tabela ---
    for info in turmas_info:
        color = turma_colors[info["turma_idx"] % len(turma_colors)]
        # Cor de fundo para a coluna da turma (A)
        requests.append(repeat_cell(
            sheet_id, info["start_row"] - 1, info["end_row"], 0, 1,
            "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.textRotation,userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
            backgroundColor=bg(*color),
            textFormat=text_fmt(bold=True, fg=txt_color(1, 1, 1)),
            textRotation={"angle": 90}, horizontalAlignment="CENTER", verticalAlignment="MIDDLE"
        ))

        # Zebrado da coluna B até a última coluna de presença (antes do resumo)
        for aluno_idx in range(info["end_row"] - info["start_row"] + 1):
            row = info["start_row"] + aluno_idx
            bg_zebra = zebra_bg(row - 1) # row-1 para 0-based
            requests.append(repeat_cell(
                sheet_id, row - 1, row, 1, col_pres - 1,
                "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
                backgroundColor=bg_zebra,
                textFormat=text_fmt(font="Arial", size=10, bold=True, fg=txt_color(0, 0, 0)),
                horizontalAlignment="CENTER", verticalAlignment="MIDDLE"
            ))
            # Alinhamento à esquerda para a coluna C (Nome)
            requests.append(repeat_cell(
                sheet_id, row - 1, row, 2, 3,
                "userEnteredFormat.horizontalAlignment", horizontalAlignment="LEFT"
            ))

        # Colunas de resumo (Presenças, Faltas, Faltas Just.) - Fundo zebrado por linha
        for aluno_idx in range(info["end_row"] - info["start_row"] + 1):
            row = info["start_row"] + aluno_idx
            bg_zebra = zebra_bg(row - 1)
            requests.append(repeat_cell(
                sheet_id, row - 1, row, col_pres - 1, col_fjust,
                "userEnteredFormat.backgroundColor",
                backgroundColor=bg_zebra
            ))
        # Texto: Presenças = preto
        requests.append(repeat_cell(
            sheet_id, info["start_row"] - 1, info["end_row"], col_pres - 1, col_pres,
            "userEnteredFormat.textFormat",
            textFormat=text_fmt(bold=True, fg=txt_color(0, 0, 0))
        ))
        # Texto: Faltas = vermelho
        requests.append(repeat_cell(
            sheet_id, info["start_row"] - 1, info["end_row"], col_falt - 1, col_falt,
            "userEnteredFormat.textFormat",
            textFormat=text_fmt(bold=True, fg=txt_color(1, 0, 0))
        ))
        # Texto: Faltas Just. = azul
        requests.append(repeat_cell(
            sheet_id, info["start_row"] - 1, info["end_row"], col_fjust - 1, col_fjust,
            "userEnteredFormat.textFormat",
            textFormat=text_fmt(bold=True, fg=txt_color(0, 0, 1))
        ))




    # --- Títulos e Cabeçalhos ---
    # Título principal (A1:C1)
    requests.append(repeat_cell(
        sheet_id, 0, 1, 0, 3,
        "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
        backgroundColor=bg(*DARK_GRAY), textFormat=text_fmt(size=12, bold=True, fg=txt_color(1, 1, 1)),
        horizontalAlignment="CENTER", verticalAlignment="MIDDLE"
    ))
    # Subtítulo (A2:C2)
    requests.append(repeat_cell(
        sheet_id, 1, 2, 0, 3,
        "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
        backgroundColor=bg(*DARK_GRAY), textFormat=text_fmt(bold=True, fg=txt_color(1, 1, 1)),
        horizontalAlignment="LEFT", verticalAlignment="MIDDLE"
    ))
    # Cabeçalho de meses (D2:X2)
    requests.append(repeat_cell(
        sheet_id, 1, 2, 3, 3 + n_enc,
        "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
        backgroundColor=bg(*DARK_GRAY), textFormat=text_fmt(bold=True, fg=txt_color(1, 1, 1)),
        horizontalAlignment="CENTER", verticalAlignment="MIDDLE"
    ))
    # Cabeçalho de datas (D3:X3)
    requests.append(repeat_cell(
        sheet_id, 2, 3, 3, 3 + n_enc,
        "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
        backgroundColor=bg(*DARK_GRAY), textFormat=text_fmt(bold=True, fg=txt_color(1, 1, 1)),
        horizontalAlignment="CENTER", verticalAlignment="MIDDLE"
    ))
    # Cabeçalhos de resumo (Y1:AA3)
    requests.append(repeat_cell(
        sheet_id, 0, 3, col_pres - 1, col_fjust,
        "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment",
        backgroundColor=bg(*DARK_GRAY), textFormat=text_fmt(bold=True, fg=txt_color(1, 1, 1)),
        horizontalAlignment="CENTER", verticalAlignment="MIDDLE"
    ))

    # --- Cores de fonte para os sinalizadores P / F / FJ ---
    presenca_range = {
        "sheetId": sheet_id,
        "startRowIndex": 3,
        "endRowIndex": total_rows,
        "startColumnIndex": 3,
        "endColumnIndex": col_pres - 1
    }
    sinalizador_cores = [
        ("P", txt_color(0.0, 0.55, 0.0)),   # Verde
        ("F", txt_color(0.80, 0.0, 0.0)),   # Vermelho
        ("FJ", txt_color(0.0, 0.0, 0.85)),  # Azul
        ("-", txt_color(0.45, 0.45, 0.45)), # Cinza - sem registro
    ]
    for idx, (valor, cor) in enumerate(sinalizador_cores):
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [presenca_range],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": valor}]},
                        "format": {"textFormat": {"foregroundColor": cor, "bold": True}}
                    }
                },
                "index": idx
            }
        })

    # --- Bordas ---
    border_solid = {"style": "SOLID", "width": 1, "color": {"red": 0, "green": 0, "blue": 0}}
    requests.append({
        "updateBorders": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": total_rows, "startColumnIndex": 0, "endColumnIndex": num_cols},
            "top": border_solid, "bottom": border_solid, "left": border_solid, "right": border_solid,
            "innerHorizontal": border_solid, "innerVertical": border_solid
        }
    })





    if requests:
        print(f"  Enviando {len(requests)} operações de formatação. Enviando em lotes...")
        total_batches = (len(requests) + BATCH_LIMIT - 1) // BATCH_LIMIT
        for i in range(0, len(requests), BATCH_LIMIT):
            batch = requests[i:i + BATCH_LIMIT]
            batch_num = (i // BATCH_LIMIT) + 1
            print(f"    Lote {batch_num}/{total_batches} ({len(batch)} ops)...")

            max_tentativas = 5
            for tentativa in range(1, max_tentativas + 1):
                try:
                    aba.client.sheet.batch_update(spreadsheet_id, batch)
                    print(f"    OK!")
                    break
                except Exception as e:
                    if tentativa == max_tentativas:
                        print(f"    ERRO no lote {batch_num} após {max_tentativas} tentativas: {e}")
                        raise
                    espera = min(2 ** tentativa, 30)  # backoff exponencial, até 30s
                    print(f"    ERRO no lote {batch_num} (tentativa {tentativa}/{max_tentativas}): {e}. Tentando de novo em {espera}s...")
                    time.sleep(espera)

            # Pequena pausa entre lotes para não estourar a cota de escrita da API
            if batch_num < total_batches:
                time.sleep(1)
        print("  Formatação concluída!")

    # ================================================================
    # PASSO 3: Largura das colunas (métodos diretos do pygsheets)
    # ================================================================
    aba.adjust_column_width(1, pixel_size=120)
    aba.adjust_column_width(2, pixel_size=35)
    aba.adjust_column_width(3, pixel_size=250)

    for i in range(n_enc):
        aba.adjust_column_width(4 + i, pixel_size=35)

    aba.adjust_column_width(col_pres, pixel_size=90)
    aba.adjust_column_width(col_falt, pixel_size=60)
    aba.adjust_column_width(col_fjust, pixel_size=90)

    # ================================================================
    # PASSO 4: Congelar cabeçalho e colunas (métodos diretos do pygsheets)
    # ================================================================
    aba.frozen_rows = 3
    aba.frozen_cols = 3


# ==========================
# FUNÇÃO PRINCIPAL
# ==========================

def atualizar_dashboard():
    print("=" * 50)
    print("Atualizando dashboard...")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    encontros, turmas, presencas, turmas_crismandos = get_all_data(conn)
    print(f"Encontros: {len(encontros)}")
    print(f"Turmas: {len(turmas)}")

    if not encontros or not turmas:
        print("Nenhum dado encontrado. Abortando.")
        conn.close()
        return

    # Usando as cores fiéis da sua imagem manual
    colors = list(TURMA_COLORS)

    if not USE_PYGSCHEETS:
        print("ERRO: pygsheets não está instalado.")
        conn.close()
        return

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    credentials = os.getenv("CREDENTIALS_FILE", "credentials.json")

    try:
        gc = pygsheets.authorize(service_file=credentials)
        planilha = gc.open_by_key(sheet_id)
    except Exception as e:
        print(f"Erro ao conectar ao Google Sheets: {e}")
        conn.close()
        return

    try:
        aba = planilha.worksheet_by_title("Chamada")
        aba.clear(fields="*")
    except:
        aba = planilha.add_worksheet("Chamada", rows=500, cols=200)
        aba.clear(fields="*")

    montar_planilha(aba, encontros, turmas, presencas, turmas_crismandos, colors)
    conn.close()

    total_alunos = sum(len(turmas_crismandos.get(t["id"], [])) for t in turmas)
    print(f"\nDashboard atualizado com sucesso!")

if __name__ == "__main__":
    atualizar_dashboard()