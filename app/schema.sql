-- SQL create table

DROP TABLE IF EXISTS keyword_occurrences CASCADE;
DROP TABLE IF EXISTS document_semantic CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS processing_jobs CASCADE;
DROP TABLE IF EXISTS keyword_catalog CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- ==================
-- documents
-- ==================

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,

    title TEXT NOT NULL,
    document_type TEXT NOT NULL,

    published_date DATE NOT NULL,
    event_start_date DATE,
    event_end_date DATE,

    source TEXT NOT NULL,
    speaker TEXT,
    speaker_position TEXT,
    chair TEXT,

    source_url TEXT NOT NULL,
    raw_file_path TEXT,
    cleaned_file_path TEXT,
    content TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_documents_source_url UNIQUE (source_url)
);


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
-- processing_jobs
-- ==================

CREATE TABLE IF NOT EXISTS processing_jobs (
    id SERIAL PRIMARY KEY,

    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    job_type TEXT NOT NULL,
    job_status TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,

    error_msg TEXT,

    CONSTRAINT valid_job_type CHECK (
        job_type IN (
            'generate_chunks', 'extract_keywords', 'summarize', 'classify_tone'
        )
    ),

    CONSTRAINT valid_job_status CHECK (
        job_status IN (
            'pending', 'running', 'completed', 'failed'
        )
    )
);


-- ==================
-- document_chunks
-- ==================

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,

    char_start INTEGER,
    char_end INTEGER,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_document_chunk_index UNIQUE (document_id, chunk_index)
);


-- ==================
-- keyword_occurences
-- ==================

CREATE TABLE IF NOT EXISTS keyword_occurences (
    id SERIAL PRIMARY KEY,

    keyword_id INTEGER NOT NULL REFERENCES keyword_catalog(id) ON DELETE CASCADE,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id INTEGER NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    sentence_index INTEGER,

    char_start INTEGER,
    char_end INTEGER,

    sentence TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);


-- ==================
-- document_semantic
-- ==================

CREATE TABLE IF NOT EXISTS document_semantic (
    id  SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    summary TEXT,
    tone_label TEXT,
    tone_score NUMERIC,
    model_name TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_document_sementic UNIQUE (document_id)
);
