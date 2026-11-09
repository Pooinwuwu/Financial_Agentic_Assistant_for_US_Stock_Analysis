# 📈 Financial Agentic Assistant for US Stock Analysis

![Python 3.12]([suspicious link removed])
![Architecture]([suspicious link removed])
![Benchmark]([suspicious link removed])
![License]([suspicious link removed])

> An end-to-end LLM-powered financial intelligence agent capable of dynamic tool orchestration across **Text-to-SQL**, **SEC 10-K Vector RAG**, and **Sandboxed Python Execution** for 10 US equities.

---

## 📑 Table of Contents
- [Overview](#-overview)
- [Target Equities](#-target-equities)
- [System Architecture](#-system-architecture)
- [Core Capabilities](#-core-capabilities)
- [Security Guardrails](#-security-guardrails)
- [Project Directory Structure](#-project-directory-structure)
- [Quickstart Guide](#-quickstart-guide)
- [Quantitative Evaluation & Benchmark](#-quantitative-evaluation--benchmark)
- [License](#-license)

---

## 🌟 Overview

Modern financial research requires synthesizing quantitative metrics, qualitative disclosures (SEC 10-K risk factors and management discussions), and complex statistical computations. 

This system deploys an autonomous **Observe-Think-Act Decision Loop** powered by `gemma-4-E4B-it` that dynamically selects, executes, and validates specialized financial tools.

---

## 🏢 Target Equities

The application tracks a portfolio of 10 premier United States equities:

| Ticker | Company Name | Sector |
| :---: | :--- | :--- |
| **AAPL** | Apple Inc. | Technology |
| **MSFT** | Microsoft Corporation | Technology |
| **NVDA** | NVIDIA Corporation | Technology |
| **AMD** | Advanced Micro Devices | Technology |
| **GOOGL**| Alphabet Inc. | Communication Services |
| **AMZN** | [suspicious link removed] Inc. | Consumer Cyclical |
| **META** | Meta Platforms Inc. | Communication Services |
| **TSLA** | Tesla, Inc. | Consumer Cyclical |
| **JPM**  | JPMorgan Chase & Co. | Financial Services |
| **WMT**  | Walmart Inc. | Consumer Defensive |

---

## 🏗️ System Architecture

```text
                      +-----------------------------+
                      |     User Natural Query      |
                      +--------------+--------------+
                                     |
                                     v
                      +--------------+--------------+
                      |  Agent Decision Loop        |
                      |  (Gemma-4-E4B-it Proxy)     |
                      +--------------+--------------+
                                     |
           +-------------------------+-------------------------+
           |                         |                         |
           v                         v                         v
+----------+----------+   +----------+----------+   +----------+----------+
|    run_sql Tool     |   |   sec_doc_rag Tool  |   |  run_python_calc     |
| (Structured SQLite) |   | (Vector RAG bge-m3) |   | (Sandboxed Execution)|
+----------+----------+   +----------+----------+   +----------+----------+
           |                         |                         |
           +-------------------------+-------------------------+
                                     |
                                     v
                      +--------------+--------------+
                      |    Observe & Synthesize     |
                      |   Final Answer + Citations  |
                      +-----------------------------+

```

## 🛠️ Core Capabilities
1. 📊 Text-to-SQL Execution (run_sql)
Query historical financial statement data (financials, companies, daily_prices).
Automatic metadata validation and Read-Only connection protection.
2. 🔍 SEC 10-K Vector RAG (sec_doc_rag)
Dense semantic retrieval using bge-m3 embeddings.
Metadata pre-filtering by symbol, year, and section (Item 1A Risk Factors & Item 7 MD&A).
Automatic citation enforcement: [SYMBOL 10-K (YEAR) SECTION].
3. 🧮 Sandboxed Python Calculation (run_python_calc)
Dynamic code generation for statistical calculations (Mean, Volatility, Growth Rate).
Self-correction retry loop fed by execution tracebacks.
🛡️ Security Guardrails
Layer
Component
Guardrail Enforced
Database
run_sql
Read-only connection mode, single-statement enforcement, DDL/DML keyword blocking, query LIMIT injection.
Sandbox
run_python_calc
AST syntax inspection, whitelist allowed modules (numpy, pandas, math, sqlite3), banned OS/network imports, execution timeout caps.
Vector Store
sec_doc_rag
Minimum similarity score floor (min_score = 0.35), mandatory metadata pre-filtering.
Agent Loop
orchestrator
Maximum step cap (max_steps = 4), zero-temperature sampling for tool selection.
📁 Project Directory Structure
Project_llm/
├── data/
│   ├── stocks.db              # SQLite database (companies, financials, daily_prices, sec_chunks)
│   └── test_set.json          # 30-Question Benchmark Dataset
├── src/
│   ├── agent/
│   │   └── orchestrator.py    # Observe-Think-Act Agent Decision Loop
│   └── tools/
│       ├── sql_tool.py        # Text-to-SQL Engine with Security Guardrails
│       ├── vector_tool.py     # SEC 10-K Vector RAG with bge-m3 & Metadata Filtering
│       └── calc_tool.py       # Sandboxed Python Calculation Engine with AST Checking
├── scripts/
│   ├── seed_data.py           # Database Initialization Script
│   ├── seed_sec_chunks.py    # SEC 10-K Document Embedding & Ingestion
│   └── create_test_set.py     # Benchmark Dataset Generator (30 Questions)
├── tests/
│   ├── test_sql_tool.py       # SQL Tool Unit Test
│   ├── test_vector_tool.py    # Vector RAG Tool Unit Test
│   ├── test_calc_tool.py      # Python Calc Sandbox Unit Test
│   └── test_evaluation_benchmark.py  # Full 30-Question End-to-End Evaluation Runner
└── README.md                  # Project Documentation
🚀 Quickstart Guide
1. Initialize Database & Vector Embeddings
python scripts/seed_data.py
python scripts/seed_sec_chunks.py
2. Run Benchmark Evaluation
python scripts/create_test_set.py
python -m tests.test_evaluation_benchmark
📊 Quantitative Evaluation & Benchmark
System performance is evaluated against a curated 30-question benchmark dataset across 5 functional categories:
===========================================================================
📊 Quantitative Results Table (End-to-End Agent Benchmark)
===========================================================================
Functional Category                 | Passed / Total  | Success Rate (%)
---------------------------------------------------------------------------
text_to_sql                         | 8/8             | 100.00%
vector_rag                          | 8/8             | 100.00%
python_calc                         | 5/5             | 100.00%
multi_hop                           | 5/5             | 100.00%
guardrail_safety                    | 4/4             | 100.00%
---------------------------------------------------------------------------
OVERALL SYSTEM ACCURACY             | 30/30           | 100.00%
===========================================================================
📜 License
This project is licensed under the MIT License.
