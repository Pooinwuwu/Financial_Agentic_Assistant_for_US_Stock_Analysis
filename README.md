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
Core Capabilities
Text-to-SQL (run_sql)
- Queries historical financial statement data in financials, companies, and daily_prices tables.
- Validates metadata automatically.
- Uses a read-only database connection.
SEC 10-K Vector RAG (sec_doc_rag)
- Retrieves semantically relevant passages using bge-m3 embeddings.
- Supports metadata filtering by symbol, year, and section, including Item 1A (Risk Factors) and Item 7 (MD&A).
- Enforces citations in the format [SYMBOL 10-K (YEAR) SECTION].
Sandboxed Python Calculation (run_python_calc)
- Generates code for statistical calculations such as mean, volatility, and growth rate.
- Retries after errors using execution tracebacks for self-correction.
