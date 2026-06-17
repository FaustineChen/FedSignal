DROP TABLE IF EXISTS keyword_occurrences CASCADE;
DROP TABLE IF EXISTS keyword_terms CASCADE;
DROP TABLE IF EXISTS keyword_catalog CASCADE;


-- ==================
-- keyword_catalog
-- ==================

CREATE TABLE IF NOT EXISTS keyword_catalog (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL UNIQUE,
    category TEXT,
    description TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);


-- ==================
-- keyword_terms
-- ==================

CREATE TABLE IF NOT EXISTS keyword_terms (
    id SERIAL PRIMARY KEY,

    keyword_id INTEGER NOT NULL REFERENCES keyword_catalog(id) ON DELETE CASCADE,

    term TEXT NOT NULL,
    match_type TEXT NOT NULL DEFAULT 'exact_phrase',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_keyword_term UNIQUE (keyword_id, term)
);


-- ==================
-- keyword_occurences
-- ==================

CREATE TABLE IF NOT EXISTS keyword_occurrences (
    id SERIAL PRIMARY KEY,

    keyword_id INTEGER NOT NULL REFERENCES keyword_catalog(id) ON DELETE CASCADE,
    keyword_term_id INTEGER REFERENCES keyword_terms(id) ON DELETE CASCADE,
    
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id INTEGER NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    
    sentence_index INTEGER,

    char_start INTEGER,
    char_end INTEGER,

    matched_text TEXT,
    sentence TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

