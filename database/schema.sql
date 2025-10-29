-- Baseline schema for Dia da Sorte (SQLite)
-- This file defines the core tables and indexes used by the application.

PRAGMA foreign_keys = ON;

-- Resultados oficiais do Dia da Sorte
CREATE TABLE IF NOT EXISTS dia_da_sorte_results (
    concurso INTEGER PRIMARY KEY,
    data_sorteio TEXT NOT NULL,
    bola1 INTEGER NOT NULL,
    bola2 INTEGER NOT NULL,
    bola3 INTEGER NOT NULL,
    bola4 INTEGER NOT NULL,
    bola5 INTEGER NOT NULL,
    bola6 INTEGER NOT NULL,
    bola7 INTEGER NOT NULL,
    mes_da_sorte INTEGER NOT NULL,
    ganhadores_7_acertos INTEGER NOT NULL,
    pares INTEGER NOT NULL,
    impares INTEGER NOT NULL,
    nah_n INTEGER,
    nah_a INTEGER,
    nah_h INTEGER,
    max_consec INTEGER NOT NULL,
    maior_salto INTEGER NOT NULL,
    isoladas INTEGER NOT NULL,
    qdls TEXT NOT NULL,
    digit_stats TEXT NOT NULL
);

-- Universo de apostas com métricas calculadas
CREATE TABLE IF NOT EXISTS dia_da_sorte_bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    d1 INTEGER NOT NULL,
    d2 INTEGER NOT NULL,
    d3 INTEGER NOT NULL,
    d4 INTEGER NOT NULL,
    d5 INTEGER NOT NULL,
    d6 INTEGER NOT NULL,
    d7 INTEGER NOT NULL,
    pares INTEGER NOT NULL,
    impares INTEGER NOT NULL,
    max_consec INTEGER NOT NULL,
    maior_salto INTEGER NOT NULL,
    isoladas INTEGER NOT NULL,
    nah_n INTEGER,
    nah_a INTEGER,
    nah_h INTEGER,
    qdls_s1 INTEGER NOT NULL,
    qdls_s2 INTEGER NOT NULL,
    qdls_s3 INTEGER NOT NULL,
    qdls_s4 INTEGER NOT NULL,
    qdls_s5 INTEGER NOT NULL,
    unit_0 INTEGER NOT NULL,
    unit_1 INTEGER NOT NULL,
    unit_2 INTEGER NOT NULL,
    unit_3 INTEGER NOT NULL,
    unit_4 INTEGER NOT NULL,
    unit_5 INTEGER NOT NULL,
    unit_6 INTEGER NOT NULL,
    unit_7 INTEGER NOT NULL,
    unit_8 INTEGER NOT NULL,
    unit_9 INTEGER NOT NULL,
    ten_0 INTEGER NOT NULL,
    ten_1 INTEGER NOT NULL,
    ten_2 INTEGER NOT NULL,
    ten_3 INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dia_bets_pares      ON dia_da_sorte_bets(pares);
CREATE INDEX IF NOT EXISTS idx_dia_bets_impares    ON dia_da_sorte_bets(impares);
CREATE INDEX IF NOT EXISTS idx_dia_bets_isoladas   ON dia_da_sorte_bets(isoladas);
CREATE INDEX IF NOT EXISTS idx_dia_bets_maxconsec  ON dia_da_sorte_bets(max_consec);
CREATE INDEX IF NOT EXISTS idx_dia_bets_maiorsalto ON dia_da_sorte_bets(maior_salto);
CREATE INDEX IF NOT EXISTS idx_dia_bets_nahn       ON dia_da_sorte_bets(nah_n);
CREATE INDEX IF NOT EXISTS idx_dia_bets_naha       ON dia_da_sorte_bets(nah_a);
CREATE INDEX IF NOT EXISTS idx_dia_bets_nahh       ON dia_da_sorte_bets(nah_h);

-- Apostas salvas para conferência por concurso (sem filtro versionado)
CREATE TABLE IF NOT EXISTS dia_da_sorte_saved_bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concurso INTEGER NOT NULL,
    d1 INTEGER NOT NULL,
    d2 INTEGER NOT NULL,
    d3 INTEGER NOT NULL,
    d4 INTEGER NOT NULL,
    d5 INTEGER NOT NULL,
    d6 INTEGER NOT NULL,
    d7 INTEGER NOT NULL,
    acertos INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_bets_unique
    ON dia_da_sorte_saved_bets(concurso, d1, d2, d3, d4, d5, d6, d7);

CREATE INDEX IF NOT EXISTS idx_saved_bets_concurso
    ON dia_da_sorte_saved_bets(concurso);

