# Capstone Roadmap: Financial Agentic Assistant for US Stock Analysis

## 1. Project Vision & Scope Alignment

Modern equity research and financial analysis require a synthesis of quantitative financial statement metrics, qualitative regulatory filings, and real-time market data. Standard large language model deployments frequently suffer from numerical hallucinations when performing multi-period financial calculations, while traditional fixed Retrieval-Augmented Generation pipelines fail when required to compute aggregate statistical figures across multiple database rows. As outlined in the course capstone specifications, an effective LLM application must solve a genuine problem on an independent domain using a small but fully functional architecture with rigorous quantitative evaluation. This capstone project builds an end-to-end Financial Agentic Assistant focused on a curated portfolio of ten premier United States equities: Apple (AAPL), Microsoft (MSFT), NVIDIA (NVDA), Advanced Micro Devices (AMD), Alphabet (GOOGL), Amazon (AMZN), Walmart (WMT), Meta Platforms (META), Tesla (TSLA), and JPMorgan Chase (JPM).

By transitioning from a rigid retrieve-then-read pipeline to an autonomous agentic decision loop, the system dynamically routes user requests to specialized tools. Quantitative queries over historical financial statements execute via structured Text-to-SQL; qualitative inquiries regarding operational risks and management discussion navigate a vector-indexed database of Securities and Exchange Commission Form 10-K filings; complex statistical modeling and technical chart plotting execute inside an isolated Python calculation sandbox; and breaking news updates fetch via live web search.

The architectural evolution from traditional fixed RAG to the proposed Financial Agentic Assistant highlights fundamental improvements in accuracy, tool orchestration, and quantitative safety:

| Architecture Dimension | Traditional Fixed RAG Pipeline | Proposed Financial Agentic Assistant |
| :--- | :--- | :--- |
| Core Execution Model | Fixed single-pass retrieve-then-read sequence on every input turn | Dynamic Observe-Think-Act loop with native tool calling and adaptive termination |
| Quantitative Data Handling | Attempts to count or aggregate over top-k retrieved text passages | Generates guarded Text-to-SQL over SQLite database for exact mathematical aggregation |
| Complex Calculation Safety | Estimates mathematical formulas directly within model generation weights | Delegates statistical modeling and graphing to an isolated Python code sandbox |
| Qualitative Context Search | Uniform vector lookup without structural metadata pre-filtering | Metadata-filtered vector search over 10-K Item 1A (Risk Factors) and Item 7 (MD&A) |
| Latency & Resource Efficiency | Executes vector search indiscriminately on every query, including chit-chat | Evaluates query intent first, calling search tools only when additional facts are required |

---

## 2. System Architecture & Capability Family Mapping

The capstone application architecture integrates four core capability families from the course curriculum, establishing a robust separation of concerns across frontend streaming, backend API routing, database persistence, and model execution. Following the course backend design principles, the application enforces a strict router-service-repository layering pattern. The router layer processes incoming HTTP requests and validates data payloads at the edge using Pydantic schemas; the service layer manages business logic, prompt assembly, and the agentic loop; and the repository layer governs database connections and vector store operations. All interaction with the underlying language model occurs through the designated class proxy using the Gemma-4-E4B-it model.

The end-to-end system design maps directly to four explicit capability families required for capstone evaluation and rubric compliance:

1. **Agentic Decision Loop & Tool Calling Family**: The core conversational loop operates on an Observe-Think-Act cycle using native model tool calling. The host application supplies tool definitions formatted as JSON Schema objects. When the language model emits a structured tool request, the host code interceptors validate arguments, execute the requested routine, and append the tool result back into the message array as a dedicated tool role message. To guarantee reliable execution, the loop enforces zero-temperature sampling for deterministic control flow, tracks call history to prevent infinite repetition, and applies a strict step limit as an upper execution bound.
2. **Advanced Multi-Modal Tooling Family**: The agent commands four specialized tools capable of resolving structured, unstructured, computational, and live web requirements. Quantitative database queries execute through an isolated Text-to-SQL engine; unstructured document inquiries route to a vector-indexed search store; advanced statistical calculations execute within a sandboxed Python execution engine; and real-time market updates resolve via web search.
3. **Retrieval-Augmented Generation & Query Construction Family**: Qualitative research draws from 10-K filings chunked into windowed passages of approximately three hundred tokens with fifteen percent overlap. Each chunk retains structural metadata tags including stock symbol, fiscal year, and document section. Vector embeddings generated by the multilingual bge-m3 model populate a Postgres pgvector store. Incoming natural language queries undergo query construction, extracting exact metadata filter predicates prior to executing cosine distance ranking, enforced by a minimum similarity score floor to suppress low-relevance passages.
4. **Served API & Streaming UI Family**: The application exposes a production-ready FastAPI backend serving an asynchronous event loop. Chat completions stream token by token to a reactive frontend interface utilizing Server-Sent Events with a text/event-stream content type and a custom done sentinel frame. Server proxy buffering is explicitly disabled via headers to ensure instant token delivery.

---

## 3. Financial Tools & Defense-in-Depth Guardrails Specification

Autonomous agents capable of executing database queries, running code, and ingesting web text introduce significant security and stability risks if left unmonitored. Following the security guardrail frameworks established in the course, every tool in this application operates within a defensive boundary where user inputs and model outputs are treated as untrusted data. System security relies on host-enforced constraints rather than model self-regulation.

The agent interacts with four defined tools, each engineered with specific system signatures and operational constraints:

* **Text-to-SQL Execution Tool (`run_sql`)**: Converts natural language requests into structured SQL queries against a SQLite database containing historical annual and quarterly financial metrics (revenue, net income, operating income, gross margin, net margin, EPS, P/E ratio, ROE, and free cash flow) for the ten target stocks.
* **SEC 10-K Document Search Tool (`sec_doc_rag`)**: Conducts metadata-filtered semantic retrieval across SEC Form 10-K filings, specifically targeting Item 1A (Risk Factors) and Item 7 (Management's Discussion and Analysis). Every retrieved passage carries explicit source citations.
* **Sandboxed Python Calculation Tool (`run_python_calc`)**: Generates and executes Python scripts against daily stock price tables to compute statistical financial models, moving averages, Sharpe ratios, volatility metrics, and trend charts.
* **Market News Search Tool (`search_web_news`)**: Searches live financial news and SEC announcements for recent developments occurring after the model's knowledge cutoff date.

To prevent malicious execution, runaway loops, and prompt injection attacks, the host environment enforces a multi-layered guardrail matrix across all four tools:

| System Layer | Target Risk Factor | Enforced Technical Guardrail |
| :--- | :--- | :--- |
| Database (`run_sql`) | Data destruction, multi-statement injection, and unindexed full scans | Read-only connection mode, single-statement enforcement via semicolon rejection, keyword denylists blocking data manipulation commands, mandatory query LIMIT injection, and parameterized value binding |
| Execution Sandbox (`run_python_calc`) | System file deletion, unauthorized network egress, and infinite execution loops | Isolated process execution with safe builtin allowlists, wall-clock execution timeout caps, strict memory allocation limits, and disabled outbound network access |
| Web Ingestion (`search_web_news`) | Indirect prompt injection hiding in fetched web prose | Structural data fencing wrapping fetched text in untrusted tags, instruction stripping, domain allowlisting, and host-side URL audit logging |
| Agent Control Loop | Infinite execution loops and budget exhaustion | Fixed maximum step limit cap, zero-temperature sampling for tool selection, repeated call detection, and fail-safe fallback responses |

---

## 4. Quantitative Evaluation Protocol & Benchmark Strategy

In accordance with course project rubrics, system performance must be proven through objective measurement on a labeled test set rather than subjective sampling. The evaluation dataset comprises thirty curated, domain-specific examples covering the ten target US stocks. The dataset contains balanced representations of single-tool quantitative lookups, document retrieval, statistical computation, complex multi-hop workflows, and negative guardrail test cases.

The thirty-question test dataset is structured across five distinct functional categories to evaluate comprehensive agent performance:

1. **Text-to-SQL Quantitative Inquiries (8 Questions)**: Evaluates exact SQL execution match and numerical accuracy for queries requiring database joins, filtering, and aggregation over financial statement ratios.
2. **Document RAG Qualitative Inquiries (8 Questions)**: Assesses passage retrieval recall, metadata filter accuracy, answer faithfulness, and source citation precision across 10-K Risk Factors and MD&A sections.
3. **Sandboxed Python Calculations (5 Questions)**: Measures code generation correctness, execution success rate, and statistical accuracy for time-series computations such as moving averages, volatility, and drawdowns.
4. **Multi-Hop / Multi-Tool Workflows (5 Questions)**: Evaluates complex task completion requiring sequential tool orchestration, such as retrieving financial margins via SQL and explaining performance differences using 10-K Risk Factor RAG.
5. **No-Tool & Guardrail Safety Scenarios (4 Questions)**: Evaluates tool selection precision by verifying that general conversation does not trigger tool invocation, and confirms host defense mechanisms against malicious SQL injection or out-of-scope predictions.

System performance will be evaluated against two baseline configurations: a Vanilla Gemma model operating without external tools, and a Single-Pass Classic RAG pipeline without SQL or Python code execution. Evaluation metrics measure retrieval effectiveness and generation quality independently:

* **Retrieval Metrics**: Recall@k and Mean Reciprocal Rank (MRR) evaluate document passage retrieval accuracy.
* **Execution Metrics**: SQL Execution Match Rate and Python Sandbox Success Rate measure programmatic accuracy against ground-truth outputs.
* **Generation & Faithfulness Metrics**: LLM-as-judge scoring, calibrated against human labels, evaluates answer groundedness and citation validity on a five-point scale.
* **Ablation Demonstration**: To fulfill the capstone requirement of demonstrating a measured improvement over a naive default, system performance will be compared before and after optimizing retrieval parameters, specifically evaluating the impact of chunk size selection and similarity score thresholds.

---

## 5. Five-Week Execution Roadmap & Implementation Schedule

To ensure project completion within the academic timeline, development follows a structured five-week milestone roadmap. The schedule prioritizes early dataset creation, robust tool boundary isolation, and reproducible evaluation harness construction before finalizing the user interface.

The weekly execution schedule details technical objectives, core deliverables, and validation criteria for each development phase:

### Week 1: Environment Setup, Database Schema & Data Ingestion
* **Technical Focus**: Establish repository structure, configure environment variable management for API keys, build the SQLite financial database, and write ingestion scripts.
* **Key Deliverables**: Public GitHub repository with clean directory layout, SQLite database populated with 3–5 years of financial metrics for the 10 target stocks via yfinance, and initial project proposal document.
* **Validation Check**: Verify that SQLite tables contain clean numerical types and execute sample SQL join queries successfully.

### Week 2: SEC 10-K Filings Vector Indexing & RAG Pipeline
* **Technical Focus**: Extract, chunk, and embed SEC Form 10-K filings (Item 1A and Item 7) for all 10 companies.
* **Key Deliverables**: Ingestion pipeline utilizing pypdf/pdfplumber, text chunking module with windowed overlap and metadata attachment, and a Postgres pgvector store populated with bge-m3 embeddings.
* **Validation Check**: Test similarity search with query construction filters to confirm that metadata filtering correctly restricts retrieved passages by company symbol and fiscal year.

### Week 3: Agentic Tools Implementation & Defense Guardrails
* **Technical Focus**: Construct the core Observe-Think-Act agent loop with native tool definitions and implement security interceptors.
* **Key Deliverables**: Functional tool suite containing `run_sql` with SELECT-only guardrails, `sec_doc_rag` with citation tracking, `run_python_calc` with execution sandboxing, and `search_web_news` with prompt injection fencing.
* **Validation Check**: Execute test queries against individual tools to confirm argument parsing, execution handling, and error recovery loops.

### Week 4: Test Dataset Assembly & Automated Evaluation Harness
* **Technical Focus**: Finalize the 30-question labeled evaluation dataset and construct automated benchmark scripts.
* **Key Deliverables**: Labeled test dataset file (`test_set.json`), reproducible evaluation runner script, baseline comparison execution against Vanilla Gemma and Classic RAG, and an ablation study comparing retrieval thresholds.
* **Validation Check**: Reproduce evaluation metrics from repository scripts, generating comparative tables for Recall@k, MRR, SQL Execution Match, and LLM-as-judge faithfulness scores.

### Week 5: Served API, Streaming UI & Final Project Submissions
* **Technical Focus**: Wrap the agentic pipeline in a FastAPI REST backend, implement SSE token streaming, build the web interface, and create final presentation materials.
* **Key Deliverables**: FastAPI application with Pydantic payload validation, reactive web interface supporting token streaming via SSE, comprehensive project report PDF (4–8 pages), and a 3–6 minute narrated demo video.
* **Validation Check**: Confirm end-to-end user interaction from the web UI, verifying that token streaming operates cleanly and error states display appropriate HTTP status codes.

---

## 6. Course Deliverables & Rubric Alignment Matrix

Project submissions are evaluated across three primary deliverables totaling two hundred points. Compliance with course standards requires meeting specific technical, architectural, and analytical criteria across all three components.

The alignment matrix details how project artifacts satisfy specific rubric criteria and point allocations:

| Deliverable Artifact | Point Allocation | Core Rubric Requirements & Strategic Alignment |
| :--- | :---: | :--- |
| **Q1: GitHub Repository** | 90 Points | Public GitHub repository containing runnable code, structured README with execution instructions, layered backend code (Router-Service-Repository), environment-based API key management without committed secrets, robust Pydantic data validation, guarded tool definitions, and committed evaluation datasets. |
| **Q2: Project Report PDF** | 70 Points | 4–8 page analytical report covering problem definition, architectural diagram detailing tool interaction and API flow, thorough evaluation protocol with comparative results tables against baseline models, ablation study justification, honest failure case analysis, and technical limitations. |
| **Q3: Demo Video or Live Link** | 40 Points | 3–6 minute narrated screen capture or deployed application URL demonstrating live execution on unseen financial inputs, highlighting one clear success case and one honest failure case, accompanied by preparation for an in-person live defense. |
