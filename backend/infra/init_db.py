import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / 'lotofacil.db'
CSV_PATH = BASE_DIR.parent / 'ultimos500_lotofacil_05062023.csv'

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS results')
    cur.execute('''
        CREATE TABLE results (
            concurso INTEGER PRIMARY KEY,
            data TEXT,
            n1 INTEGER, n2 INTEGER, n3 INTEGER, n4 INTEGER, n5 INTEGER,
            n6 INTEGER, n7 INTEGER, n8 INTEGER, n9 INTEGER, n10 INTEGER,
            n11 INTEGER, n12 INTEGER, n13 INTEGER, n14 INTEGER, n15 INTEGER,
            ganhador INTEGER
        )
    ''')
    with CSV_PATH.open() as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        rows = [
            [int(r[0]), r[1], *map(int, r[2:17]), int(r[17])]
            for r in reader if r
        ]
    cur.executemany(
        'INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        rows
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
