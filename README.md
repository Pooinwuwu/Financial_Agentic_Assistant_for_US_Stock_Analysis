# 📈 Financial Agentic Assistant for US Stock Analysis

**Python 3.12** | **Architecture: Observe-Think-Act** | **Benchmark Accuracy: 100%** | **License: MIT**

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

🛠️ Core Capabilities
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
