# Financial Agentic Assistant for US Stock Analysis

> An end-to-end, LLM-powered financial intelligence agent that orchestrates tools for text-to-SQL, SEC 10-K vector retrieval-augmented generation (RAG), and sandboxed Python execution across 10 US equities.

## Table of Contents

- [Overview](#overview)
- [Target Equities](#target-equities)
- [System Architecture](#system-architecture)
- [Core Capabilities](#core-capabilities)
- [Security Guardrails](#security-guardrails)
- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [Evaluation and Benchmark](#evaluation-and-benchmark)
- [License](#license)

## Overview

Financial research often requires combining quantitative metrics, qualitative disclosures from SEC 10-K filings, and statistical analysis. This project uses an autonomous **Observe–Think–Act** decision loop powered by `gemma-4-E4B-it` to select, run, and validate specialized financial tools.

## Target Equities

The application tracks 10 US equities:

| Ticker | Company | Sector |
|:---:|---|---|
| AAPL | Apple Inc. | Technology |
| MSFT | Microsoft Corporation | Technology |
| NVDA | NVIDIA Corporation | Technology |
| AMD | Advanced Micro Devices | Technology |
| GOOGL | Alphabet Inc. | Communication Services |
| AMZN | Amazon.com, Inc. | Consumer Cyclical |
| META | Meta Platforms, Inc. | Communication Services |
| TSLA | Tesla, Inc. | Consumer Cyclical |
| JPM | JPMorgan Chase & Co. | Financial Services |
| WMT | Walmart Inc. | Consumer Defensive |

## System Architecture

```text
                         +-----------------------------+
                         |     User Natural Query      |
                         +--------------+--------------+
                                        |
                                        v
                         +--------------+--------------+
                         |     Agent Decision Loop     |
                         |   (Gemma-4-E4B-it Proxy)    |
                         +--------------+--------------+
                                        |
              +-------------------------+-------------------------+
              |                         |                         |
              v                         v                         v
     +------------------+      +------------------+      +--------------------+
     |   run_sql Tool   |      | sec_doc_rag Tool |      | run_python_calc    |
     | Structured SQLite|      | Vector RAG bge-m3|      | Sandboxed Execution|
     +--------+---------+      +--------+---------+      +---------+----------+
              |                         |                         |
              +-------------------------+-------------------------+
                                        |
                                        v
                         +--------------+--------------+
                         |    Observe & Synthesize     |
                         |  Final Answer + Citations   |
                         +-----------------------------+
```

## Core Capabilities

### Text-to-SQL (`run_sql`)

- Queries historical financial statement data in `financials`, `companies`, and `daily_prices` tables.
- Validates metadata automatically.
- Uses a read-only database connection.

### SEC 10-K Vector RAG (`sec_doc_rag`)

- Retrieves semantically relevant passages using `bge-m3` embeddings.
- Supports metadata filtering by symbol, year, and section, including Item 1A (Risk Factors) and Item 7 (MD&A).
- Enforces citations in the format `[SYMBOL 10-K (YEAR) SECTION]`.

### Sandboxed Python Calculation (`run_python_calc`)

- Generates code for statistical calculations such as mean, volatility, and growth rate.
- Retries after errors using execution tracebacks for self-correction.

## Security Guardrails

| Layer | Component | Guardrails |
|---|---|---|
| Database | `run_sql` | Read-only connection, single-statement enforcement, DDL/DML keyword blocking, and query `LIMIT` injection. |
| Sandbox | `run_python_calc` | AST inspection, module allowlist (`numpy`, `pandas`, `math`, `sqlite3`), blocked OS/network imports, and execution timeouts. |
| Vector store | `sec_doc_rag` | Minimum similarity score (`min_score = 0.35`) and required metadata pre-filtering. |
| Agent loop | `orchestrator` | Maximum of four steps (`max_steps = 4`) and zero-temperature sampling for tool selection. |

## Project Structure

```text
Project_llm/
├── data/
│   ├── stocks.db
│   └── test_set.json
├── src/
│   ├── agent/
│   │   └── orchestrator.py
│   └── tools/
│       ├── sql_tool.py
│       ├── vector_tool.py
│       └── calc_tool.py
├── scripts/
│   ├── seed_data.py
│   ├── seed_sec_chunks.py
│   └── create_test_set.py
├── tests/
│   ├── test_sql_tool.py
│   ├── test_vector_tool.py
│   ├── test_calc_tool.py
│   └── test_evaluation_benchmark.py
└── README.md
```

- `data/stocks.db` — SQLite database containing company, financial, daily price, and SEC chunk data.
- `data/test_set.json` — 30-question benchmark dataset.
- `src/agent/orchestrator.py` — Observe–Think–Act agent loop.
- `src/tools/sql_tool.py` — Text-to-SQL engine with security guardrails.
- `src/tools/vector_tool.py` — SEC 10-K vector RAG with `bge-m3` and metadata filtering.
- `src/tools/calc_tool.py` — Sandboxed Python calculation engine with AST checks.
- `scripts/seed_data.py` — Database initialization.
- `scripts/seed_sec_chunks.py` — SEC 10-K embedding and ingestion.
- `scripts/create_test_set.py` — Benchmark dataset generation.
- `tests/` — Tool and end-to-end benchmark tests.

## Quickstart

### 1. Initialize the database and vector embeddings

```bash
python scripts/seed_data.py
python scripts/seed_sec_chunks.py
```

### 2. Generate and run the benchmark

```bash
python scripts/create_test_set.py
python -m tests.test_evaluation_benchmark
```

## Evaluation and Benchmark

The system is evaluated on a curated 30-question benchmark across five categories:

| Category | Passed / Total | Success Rate |
|---|:---:|---:|
| Text-to-SQL | 8 / 8 | 100% |
| Vector RAG | 8 / 8 | 100% |
| Python calculations | 5 / 5 | 100% |
| Multi-hop | 5 / 5 | 100% |
| Guardrail safety | 4 / 4 | 100% |
| **Overall** | **30 / 30** | **100%** |

## License

This project is licensed under the [MIT License](LICENSE).
