import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "decisoes_v41.db"

def init_log_database() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                nome_reu TEXT NOT NULL,
                numero_processo TEXT NOT NULL,
                status TEXT NOT NULL,
                motivo TEXT NOT NULL,
                fundamento_legal TEXT NOT NULL
            )
        ''')
        conn.commit()

def registrar_log_sqlite(entry: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            '''INSERT INTO logs
               (data_hora, nome_reu, numero_processo, status, motivo, fundamento_legal)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                entry["data_hora"], entry["nome_reu"], entry["numero_processo"],
                entry["status"], entry["motivo"], entry["fundamento_legal"]
            )
        )
        conn.commit()
    print("Decisão registrada no banco de dados.")
