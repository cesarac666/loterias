-- Rollback filter-versioning changes for Dia da Sorte
-- Safely removes dia_da_sorte_saved_filters and the filter_id column/indexes
-- from dia_da_sorte_saved_bets, restoring the original unique index.

BEGIN IMMEDIATE;
PRAGMA foreign_keys = OFF;

-- Drop dependent index if it exists
DROP INDEX IF EXISTS idx_saved_bets_filter;

-- Recreate dia_da_sorte_saved_bets without filter_id (if column exists)
-- Canonical SQLite table-rebuild procedure

-- Rename current table to backup if it exists
DROP TABLE IF EXISTS dia_da_sorte_saved_bets_backup;
ALTER TABLE dia_da_sorte_saved_bets RENAME TO dia_da_sorte_saved_bets_backup;

-- Create the original structure (without filter_id)
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

-- Restore data from backup, ignoring the dropped column
INSERT INTO dia_da_sorte_saved_bets (
    id, concurso, d1, d2, d3, d4, d5, d6, d7, acertos, created_at
)
SELECT id, concurso, d1, d2, d3, d4, d5, d6, d7, acertos, created_at
FROM dia_da_sorte_saved_bets_backup;

-- Drop the backup
DROP TABLE IF EXISTS dia_da_sorte_saved_bets_backup;

-- Recreate original indexes
DROP INDEX IF EXISTS idx_saved_bets_unique;
CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_bets_unique
ON dia_da_sorte_saved_bets(concurso, d1, d2, d3, d4, d5, d6, d7);

DROP INDEX IF EXISTS idx_saved_bets_concurso;
CREATE INDEX IF NOT EXISTS idx_saved_bets_concurso
ON dia_da_sorte_saved_bets(concurso);

-- Drop filters table if present
DROP TABLE IF EXISTS dia_da_sorte_saved_filters;

-- Ensure AUTOINCREMENT sequence matches current max(id)
UPDATE sqlite_sequence
   SET seq = (SELECT COALESCE(MAX(id), 0) FROM dia_da_sorte_saved_bets)
 WHERE name = 'dia_da_sorte_saved_bets';

PRAGMA foreign_keys = ON;
COMMIT;

