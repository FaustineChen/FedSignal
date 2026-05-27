# Semantic Query Processing Pipeline for Policy Documents

An asynchronous backend system for ingesting, processing, and querying central bank communications.
The project explores how to execute semantic queries over a document corpus efficiently by combining structured filters, keyword indexing, cached semantic operators, and selective LLM calls.

## Overview

Central bank communications contain important policy signals, but analyzing them manually across years of statements, speeches, and transcripts is time-consuming.

This project builds a backend pipeline that can:

- Ingest official policy documents
- Process documents asynchronously through a job queue
- Extract keywords, phrases, metadata, and policy-relevant signals
- Support structured and semantic queries over the document corpus
- Cache expensive semantic operations to avoid repeated LLM calls
- Translate natural language questions into executable query plans

The initial use case focuses on Federal Reserve communications, such as FOMC statements, speeches, and press conference transcripts.

## Motivation

A naive semantic analysis system might call an LLM on every document, paragraph, or row. This does not scale well.

This project investigates a more systems-oriented approach:

1. Apply structured filters first
2. Narrow the candidate set using metadata and keyword search
3. Execute semantic operators only on relevant chunks
4. Cache semantic results for reuse
5. Track query execution steps and processing costs

The goal is not to build a financial prediction model, but to prototype an efficient semantic query processing pipeline.