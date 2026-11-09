Financial Agentic Assistant for US Stock Analysis 📈🤖
Capstone Project: Build & Evaluate an LLM-Powered Application
Target Assets: 10 US Equities (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, JPM, WMT, AMD)
Model & Infrastructure: gemma-4-E4B-it via OpenAI Proxy Protocol | SQLite | bge-m3 Embeddings | Python 3.12 Sandbox

🌟 Project Overview
The Financial Agentic Assistant is an end-to-end, multi-tool agentic LLM application designed to eliminate numerical hallucinations and ground financial insights in verifiable evidence. Instead of relying on a rigid, single-pass retrieve-then-read RAG pipeline, the system uses an autonomous Observe-Think-Act Decision Loop to route user queries to specialized tools:

Text-to-SQL Engine (run_sql): Queries historical annual and quarterly financial metrics (companies, financials, daily_prices) in a SQLite database with strict read-only guardrails.
SEC 10-K Vector RAG (sec_doc_rag): Conducts metadata-filtered semantic search across SEC Form 10-K filings (Item 1A Risk Factors & Item 7 MD&A) with bge-m3 (1024-dim) vector embeddings and explicit citations.
Sandboxed Python Calculation Engine (run_python_calc): Executes sandboxed Python code for statistical financial modeling, moving averages, volatility, Sharpe ratios, and chart plotting.
Agent Orchestrator (run_agent_orchestrator): Coordinates native tool execution, handles multi-hop workflows sequentially, and intercepts general chit-chat without calling tools unnecessarily.
🏗️ System Architecture
                                  +-----------------------+
                                  |     User Question     |
                                  +-----------+-----------+
                                              |
                                              v
                                 +-------------------------+
                                 |   Agent Orchestrator    |
                                 | (Observe-Think-Act Loop)|
                                 +------------+------------+
                                              |
                     +------------------------+------------------------+
                     |                        |                        |
                     v                        v                        v
          +--------------------+    +--------------------+    +--------------------+
          | Text-to-SQL Tool   |    | SEC 10-K RAG Tool  |    | Python Calc Engine |
          |    (`run_sql`)     |    |   (`sec_doc_rag`)  |    | (`run_python_calc`)|
          +---------+----------+    +---------+----------+    +---------+----------+
                    |                         |                         |
                    v                         v                         v
          +--------------------+    +--------------------+    +--------------------+
          | SQLite DB (Read-Only)   | Vector Store (bge-m3)|   | AST Sandbox Exec   |
          | companies          |    | Item 1A (Risks)    |    | pandas / numpy /   |
          | financials         |    | Item 7 (MD&A)      |    | math / sqlite3     |
          | daily_prices       |    | [Symbol, Year Filter]|   | safe_import        |
          +--------------------+    +--------------------+    +--------------------+
🛡️ Defense-in-Depth Guardrails
To ensure safety, stability, and zero hallucinations, host-enforced guardrails operate across all system layers:

SQL Guardrails: Read-only database URI connection (mode=ro), single-statement validation (semicolon check), keyword denylists (DROP, ALTER, DELETE, UPDATE, INSERT), auto-injected LIMIT caps, and exact table name schema prompt enforcement.
Python Sandbox Guardrails: AST (Abstract Syntax Tree) code inspection blocking dangerous modules (os, sys, subprocess, shutil, requests) and dangerous built-ins (eval, exec, open), custom safe_import module whitelist, process stdout/stderr interception, wall-clock execution timeouts, and an iterative self-correction repair loop.
Vector RAG Guardrails: Query construction for metadata pre-filtering (by symbol, year, section), min_score = 0.35 similarity score floor to suppress low-relevance results, and explicit source citation tracking ([Symbol 10-K (Year) Section]).
Agent Loop Control: Maximum step cap (max_steps = 4) to prevent infinite execution loops and zero-temperature sampling for deterministic tool selection.
📁 Repository Structure
.
├── README.md                         # Project Overview, Setup & Benchmark Documentation
├── data/
│   ├── stocks.db                     # SQLite Database (companies, financials, daily_prices, sec_chunks)
│   └── test_set.json                 # 30-Question Labeled Benchmark Evaluation Dataset
├── src/
│   ├── agent/
│   │   └── orchestrator.py           # Core Agent Decision Loop (Observe-Think-Act)
│   └── tools/
│       ├── sql_tool.py               # Text-to-SQL Engine with Read-Only Guardrails
│       ├── vector_tool.py            # SEC 10-K Vector RAG with bge-m3 & Metadata Filters
│       └── calc_tool.py              # Sandboxed Python Execution Engine with AST Inspection
├── scripts/
│   ├── init_db.py                    # SQLite Database Initialization Script
│   ├── seed_data.py                  # Financial Metrics Seeding Script
│   ├── seed_sec_chunks.py            # SEC Form 10-K Embeddings & Vector Seeding Script
│   └── create_test_set.py            # 30-Question Benchmark Dataset Generator
└── tests/
    ├── test_sql_tool.py              # Test Suite for Text-to-SQL Tool
    ├── test_vector_tool.py           # Test Suite for SEC 10-K Vector RAG Tool
    ├── test_calc_tool.py             # Test Suite for Sandboxed Python Calc Tool
    └── test_evaluation_benchmark.py  # Full 30-Question Benchmark Evaluation Script
🚀 Setup & Installation
1. Environment Configuration
Create a .env file in the project root directory:

OPENAI_BASE_URL="https://your-proxy-url/v1"
OPENAI_API_KEY="your-api-key"
2. Database & Data Seeding
Initialize the SQLite database and seed financial metrics and SEC 10-K vector embeddings:

# 1. Initialize SQLite Database Schema
python scripts/init_db.py

# 2. Seed Financial & Daily Price Data
python scripts/seed_data.py

# 3. Seed SEC 10-K Form Chunks and bge-m3 Embeddings
python scripts/seed_sec_chunks.py
📊 Quantitative Benchmark & Evaluation Results
The application was evaluated using a curated 30-Question Benchmark Dataset (data/test_set.json) covering 5 functional categories across the 10 target stocks.

Running the Evaluation Benchmark
# 1. Generate the 30-Question Benchmark Dataset
python scripts/create_test_set.py

# 2. Run the Automated Benchmark Evaluation Protocol
python -m tests.test_evaluation_benchmark
Quantitative Benchmark Results Table
===========================================================================
📊 ตารางสรุปผลการประเมินเชิงปริมาณ (Quantitative Results Table)
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
🎓 Capstone Rubric & Deliverables Alignment
Q1 — GitHub Repository (90 pts): Clean directory structure, environment-based configuration, full 30-question benchmark dataset, reproducible evaluation script, and 100.00% system accuracy.
Q2 — Technical Report (70 pts): 4–8 page document covering system architecture, tool guardrail matrices, quantitative benchmark tables, failure analysis, and limitations.
Q3 — Demo Video / Live Link (40 pts): 3–6 minute narrated screen capture demonstrating multi-tool success cases, guardrail safety handling, and honest failure/edge case analysis.