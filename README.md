# Project_llm

My Goal :
Project — Capstone: Build & Evaluate an LLM-Powered Application
Covers: Lectures 1–15 — prompting, structured output, backend & streaming, vector storage & RAG, evaluation, query construction, agents & tool calling, code execution, skills & MCP.

Goal
This is the capstone for the course. You will design, build, evaluate, and demo your own LLM-powered application end-to-end, pulling together the techniques from the whole course. The point is not to use every technique — it is to pick the right ones for a real problem you care about, wire them together into something that works, and then tell the truth about how well it works with an honest evaluation.

A good project is a small but complete application: it takes real input, calls the model against the class proxy (OPENAI() with model="gemma-4-E4B-it"), does something genuinely useful with the output, and has at least one place where you measured quality rather than guessed at it.

Scope — what counts
Your app must, at minimum:

Call the LLM through the class proxy (from openai import OpenAI).
Demonstrate at least three of the course's capability families — and they must include the evaluation family (#3) and at least one agentic family:
structured output with schema validation,
retrieval / RAG (embed → index → retrieve → cite),
retrieval evaluation — a metric on a labelled test set,
an agent loop with tools — function calling + a stop condition (agentic),
an advanced capability — SQL, web search, sandboxed code execution, or MCP (agentic),
a served interface — a FastAPI/REST backend and/or an SSE-streaming UI.
Include a real evaluation: a small labelled or curated test set, at least one quantitative metric (e.g. accuracy, recall@k, MRR, faithfulness, an LLM-as-judge score), and a baseline you compare against.
The repo rubric grades this coverage first: a project that shows fewer than three families (or skips evaluation / all agentic work) is capped. This is deliberate — the capstone is where the course's "build an end-to-end X" outcomes are actually assessed, so it should exercise a real spread of them, not just one.

Idea starters (pick one or invent your own)
Grounded Q&A / "chat with your docs": RAG over lecture notes, a textbook, a codebase, or a set of PDFs, with citations and a faithfulness eval.
Structured extractor: turn messy text (receipts, emails, job posts) into validated JSON, evaluated against a hand-labelled gold set.
Agentic assistant: an agent that picks among tools (SQL over a small DB, web search, a calculator/code sandbox) to answer multi-step questions.
NL → query interface: natural-language → SQL or → a structured filter over a dataset, with an exact-match / execution-match eval.
MCP-powered tool: expose a capability as an MCP server and drive it from an agent host, or connect your app to an existing MCP server.
Using the reference app — and how your project must differ
The course ships a small public reference app — a mini chat + RAG application built stage by stage as git tags: kmitl-llm-app-demo. It is the worked example behind Lectures 3–10 (streaming chat, a vector store with a min_score floor and citations, an eval harness, an agent loop), and its corpus is this course's own stack. You may read, run, fork, and cite the reference app and use AI tools freely. Submitting it (or a re-skin) as your own does not pass — your project must answer questions the reference can't, on data it's never seen, with an evaluation you built and can defend.

Concretely, to pass the project you must:

Use a corpus the reference app cannot answer — your own domain, not this course's stack. Commit the raw data (or a fetch script) to your repo.
Build your own evaluation set — roughly 30 examples — and beat a baseline you name (e.g. no-retrieval, BM25-only, top-1). The numbers must be reproducible from your repo.
Show one measured improvement over a naive default — justify your own min_score, chunk size, or retrieval choice with a before/after number, not a guess.
Defend it live in the demo — run your app on a new input we give you and explain one design choice and one evaluation number.
These requirements don't change the point allocations below — they are how the existing rubric (coverage, a real eval with a baseline, the in-person defence) is read when a public reference exists.

What to do — milestones
Proposal (week 1 of the project). One paragraph: the problem, who it's for, which course techniques you'll use, and how you'll evaluate it. Sanity- check the scope with the instructor — small and finished beats big and broken.
Build. Implement the app. Keep a clean repo: a README.md that says what it does and how to run it, sensible structure, no secrets committed (read the API key/base URL from the environment, exactly like the sandbox). Commit as you go — the history should show real, incremental work.
Evaluate. Assemble your test set, run your metric(s) against a baseline, and record the numbers. The evaluation script/notebook lives in the repo and is reproducible.
Demo. Record a short (3–6 min) screen-capture walking through the app running for real, or deploy it and share a live link. Show a success case and at least one honest failure case.
Deliverables / how it's graded (200 pts)
Q1 — GitHub repository (URL, 90 pts). A public github.com repo with your code, a clear README.md, your evaluation script/data, and a commit history. Graded on: it runs from the README (≈25), code quality & structure following the course's layering ideas (≈25), correct & safe use of the LLM/proxy and tools — env-based config, validated structured output, allow-listed tool calls (≈25), and README/repo clarity (≈15).
Q2 — Project report (PDF, 70 pts). 4–8 pages covering: the problem and who it's for; your design (architecture diagram + which techniques and why); your evaluation (test set, metric, baseline, results table); results with honest analysis including failure cases; and limitations / what you'd do next. An honest, well-analysed eval scores higher than an inflated one.
Q3 — Demo video or live link (URL, 40 pts). A 3–6 min screen recording (unlisted YouTube/Drive link) or a deployed, working app URL. Show it running on real input, one success and one failure case, narrated.
Q1 + Q2 are graded by rubric and discussed in an in-person demo session, where we'll ask you to run the app and explain a design choice. Be ready to show your code and defend an evaluation number.

Tips
Scope ruthlessly. A finished structured-extractor with a 30-example gold set beats a half-built "autonomous agent". You can always add more.
Build the eval early, not the night before. It will change how you build. Even 20 hand-labelled examples turn "I think it's good" into a number.
Set temperature=0 for anything you evaluate or that must be repeatable; reserve higher temperatures for genuinely creative steps.
Validate everything that crosses a boundary — parse/repair JSON with a schema, allow-list and check tool arguments before running them, and treat every tool result as untrusted (Lectures 2, 10, 15).
Cite your sources in any RAG output, and report a baseline so your metric means something (Lectures 6–7).
Don't commit secrets. Read OPENAI_API_KEY / OPENAI_BASE_URL from the environment, just like the sandbox does.
Tell the truth in the report. A clearly-described failure case shows more understanding than a suspiciously perfect results table.