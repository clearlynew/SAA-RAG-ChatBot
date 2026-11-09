# SAA RAG Assistant: Build Plan & Reference

Reference doc.

## 1. Goal

A deployed, serverless RAG assistant for AWS SAA exam prep, built to show cloud skills on my resume. It replaces Legali. Target: live link, README, and eval numbers before I send January internship applications.

## 2. Scope

**In scope**

- Ingest AWS whitepapers only (no notes, course material, or practice questions)
- Hybrid retrieval: vector search + keyword overlap, merged with RRF
- Bedrock rerank, then answer generation with sources
- Static frontend + API
- Everything provisioned with Terraform
- Eval, load test, cost numbers

**Non-goals (do not add)**

- Multi-model fallback
- OpenSearch
- Bedrock Knowledge Bases (I hand-roll the Lambdas on purpose)
- User accounts / auth
- Fancy UI

## 3. Stack (fixed)

- **Region:** us-east-1
- **Embeddings + generation + rerank/judge:** Bedrock (Titan embed + a Bedrock text model)
- **Vectors:** S3 Vectors
- **Keyword index, eval log, cache:** DynamoDB
- **Ingest:** S3 upload -> SQS -> Lambda
- **Query path:** API Gateway -> Lambda
- **Frontend:** static site on S3 + CloudFront
- **IaC:** Terraform
- **Language:** Python (Lambdas)

## 4. Architecture

**Ingest:** raw docs in S3 -> SQS queue -> ingest Lambda (structure-aware chunking -> Titan embeddings -> write vectors to S3 Vectors + keyword terms to DynamoDB).

**Query:** frontend -> API Gateway -> query Lambda -> (1) embed question, (2) vector top-k, (3) keyword top-k, (4) merge with RRF, (5) Bedrock rerank, (6) generate answer with cited chunks, (7) cache + log to DynamoDB.

## 5. Repo structure

```
saa-rag/
  README.md          # architecture diagram, decisions, eval results, cost, live link
  PLAN.md            # this doc
  terraform/         # all infra
  lambdas/
    ingest/
    query/
  eval/              # questions.json, run_eval.py, results.md
  frontend/          # static page
  data/              # source docs (gitignored if large)
```

## 6. Phases

**Phase 0: Setup**

- Repo, Terraform backend, AWS profile, Bedrock model access enabled in us-east-1
- Done when: `terraform plan` runs clean and a test Bedrock call works

**Phase 1: Storage + ingest**

- S3 buckets, S3 Vectors index, DynamoDB tables, SQS, ingest Lambda
- Done when: uploading one doc results in vectors + keyword rows I can see

**Phase 2: Retrieval**

- Vector search, keyword search, RRF merge, Bedrock rerank
- Done when: a local script returns sensible top-5 chunks for 5 test questions

**Phase 3: Generation + API**

- Answer generation with citations, API Gateway, caching
- Done when: `curl` to the API returns a cited answer

**Phase 4: Frontend + deploy**

- Static page, CloudFront, end-to-end on the live URL
- Done when: live link works from my phone

**Phase 5: Eval + load test + cost**

- 30 to 50 questions with labeled correct source chunks
- Compare: vector-only vs hybrid vs hybrid + rerank, precision/recall@5
- Load test, then cost per 1,000 queries from the bill
- Done when: results table is in the README

**Phase 6: README + resume**

- Architecture diagram, design decisions in my own words, results, live link
- Add to resume, remove Legali
  
## 7. Decision log

Add a line each time a real choice is made (what, why, what I rejected).

- Hand-rolled Lambdas over Bedrock Knowledge Bases: to understand and explain retrieval end to end
- Lightweight hybrid (term overlap + RRF) over OpenSearch: lower cost and complexity
- Structure-aware chunking as default; semantic chunking only as an optional eval experiment
- (add more here)


## 8. Phase 0 detail: setup checklist

- [ ] Create repo, add `PLAN.md`, `.gitignore` (terraform state, `.env`, `data/` if large)
- [ ] Terraform remote state: S3 bucket + DynamoDB lock table (create these by hand once, everything else via Terraform)
- [ ] AWS budget alarm (e.g. $10 and $25) with email notification
- [ ] Enable Bedrock model access in us-east-1 for the embedding model, the generation model, and a rerank model **(check availability)**
- [ ] Smoke test: one `invoke_model` call for embeddings and one for generation from a local script
- [ ] Pick and record in the decision log: embedding model + dimension (e.g. Titan Text Embeddings V2, 1024 dims), generation model, rerank approach
- [ ] Fallback if no rerank model is available in us-east-1: LLM-as-judge scoring of the top 10 chunks (score 0 to 10, keep top 5)

## 9. Data sources and corpus

**AWS whitepapers only.** I chose this for safety (copyright and licensing), so nothing else goes into the index. The corpus is official AWS whitepapers that I download myself.

- Core: AWS Well-Architected Framework and its pillar whitepapers (Security, Reliability, Performance Efficiency, Cost Optimization, Operational Excellence, Sustainability)
- Topic papers that match SAA domains: disaster recovery, VPC connectivity options, security best practices, storage and database options, deployment options (verify exact titles on the AWS whitepapers page)
- Save each one as text or markdown, keeping its headings, so the structure-aware chunker has something to work with

**Not in the corpus:** my own notes, the Maarek course material, Tutorials Dojo content, practice-question explanations, exam dumps, blog posts. Check each whitepaper's usage terms on the AWS site, use it for this personal project only, and keep the raw files out of the public repo (`data/` in `.gitignore`; the README tells people how to download them).

Size: aim for 15 to 30 whitepapers, about 1,000 to 3,000 chunks. Quality beats size for the eval. Folder layout in S3: `raw/whitepapers/<name>.md`, with a small `meta` JSON per doc (title, source URL, topic tags such as `security`, `reliability`, `cost`).

## 10. Chunking spec (structure-aware)

- Split on markdown headings first (H1/H2/H3). Each chunk keeps its heading path, e.g. `S3 > Storage classes > Glacier`.
- Target 200 to 400 tokens per chunk, hard max 500. If a section is longer, split on paragraph boundaries with \~50 token overlap.
- Never split inside a code block or a table.
- Prepend the heading path to the chunk text before embedding (helps retrieval).
- Chunk ID format: `<doc_id>#<section_index>#<chunk_index>`
- Store per chunk: `chunk_id, doc_id, source, heading_path, text, token_count, topic_tags`
- Optional eval experiment only: semantic chunking compared against this default.

## 11. Data model

**S3 Vectors**

- One vector bucket, one index. Dimension = embedding dimension, distance metric = cosine **(check)**
- Vector key = `chunk_id`. Metadata: `doc_id, source, heading_path, topic_tags`
- Batch writes in groups (check current per-call limit)

**DynamoDB tables (on-demand billing)**

| Table | Keys | Main attributes | Purpose |
| --- | --- | --- | --- |
| `chunks` | PK `chunk_id` | text, doc\_id, heading\_path, source, token\_count | Fetch chunk text after retrieval |
| `terms` | PK `term`, SK `chunk_id` | tf (term frequency) | Keyword index (inverted) |
| `docstats` | PK `chunk_id` | length | Length normalization for keyword scoring |
| `cache` | PK `query_hash` | answer, sources, ttl | Cache repeated questions (TTL 24h) |
| `evallog` | PK `run_id`, SK `question_id` | retrieved ids, scores, latency | Eval results per config |

Keyword scoring: lowercase, strip stopwords, simple stemming; score = BM25-lite over matching terms. Keep it simple and explainable.

## 12. Retrieval spec

1. Embed the question (same model as ingest).
2. Vector search: top 20 from S3 Vectors.
3. Keyword search: top 20 from `terms` table.
4. Merge with Reciprocal Rank Fusion: `score(d) = sum(1 / (60 + rank_i(d)))` over the two lists. Keep top 10.
5. Rerank the 10 candidates with the Bedrock rerank model (or LLM-judge fallback). Keep top 5.
6. Generate the answer from the top 5 chunks.

Config lives in one place (env vars or a config file): `K_VECTOR=20, K_KEYWORD=20, RRF_K=60, K_RERANK_IN=10, K_FINAL=5`. The eval flips these (and on/off switches) to compare modes: `vector_only`, `hybrid`, `hybrid_rerank`.

## 13. API contract

`POST /ask`

- Request: `{"question": "string (max 500 chars)"}`
- Response 200: `{"answer": "...", "sources": [...], "latency_ms": 0, "cached": false}`
- Errors: 400 invalid input, 429 throttled, 500 internal (never leak stack traces)

Also: CORS locked to the CloudFront domain, API Gateway throttling (e.g. 5 req/s, burst 10) to protect the bill, request validation at the gateway.

## 14. Terraform layout

```
terraform/
  main.tf  variables.tf  outputs.tf  providers.tf
  modules/
    storage/   # S3 buckets, S3 Vectors, DynamoDB tables
    ingest/    # SQS (+ DLQ), S3 event notification, ingest Lambda, IAM
    api/       # query Lambda, API Gateway, IAM, throttling
    frontend/  # S3 site bucket, CloudFront (OAC), outputs
```

- Each Lambda gets its own least-privilege IAM role (only the tables, buckets, and Bedrock models it needs)
- SQS gets a dead-letter queue (max receive count 3)
- Lambda timeouts: ingest 60s, query 30s; memory 512 MB to start, tune later
- Tag every resource: `project=saa-rag`
- Outputs: API URL, CloudFront URL, bucket names

## 15. Phase task breakdown

**Phase 1: Storage + ingest**

1. Terraform `storage` module, apply
2. Write the chunker as a plain Python module with unit tests (run locally first)
3. Write the ingest Lambda: read S3 object, chunk, embed, write vectors, write DynamoDB rows
4. Terraform `ingest` module: S3 upload event -> SQS -> Lambda, plus DLQ
5. Upload one doc, check CloudWatch logs and the data in S3 Vectors and DynamoDB
6. Upload the full corpus; watch for Bedrock throttling and add retries with backoff

**Phase 2: Retrieval**

1. Local script `retrieve.py` that runs steps 1 to 6 of the retrieval spec against the deployed data
2. Write 5 test questions and eyeball results
3. Start `eval/questions.json` now (see section 22)

**Phase 3: Generation + API**

1. Move retrieval + generation into the query Lambda
2. Add caching and logging
3. Terraform `api` module; test with `curl`
4. Add input validation and error handling

**Phase 4: Frontend + deploy**

1. Single HTML page: input box, answer area, numbered sources list
2. Terraform `frontend` module (S3 + CloudFront with OAC); upload the page
3. Test the live URL on desktop and phone

**Phase 5: Eval + load test + cost** (see sections 22 to 24)

**Phase 6: README + resume** (see section 26)

## 16. Eval methodology

- 30 to 50 questions, written by me from whitepaper content only, covering the main SAA domains (security, resilient architectures, performance, cost)
- Format per question: `{id, question, relevant_chunk_ids: [...], topic}` (label the chunks that truly answer it; allow 1 to 3)
- Metrics: **precision@5** and **recall@5** for retrieval; plus an answer quality score (1 to 5 rubric: correct, grounded in sources, concise) judged by an LLM and spot-checked by me on 10 questions
- Configs to compare: `vector_only`, `hybrid`, `hybrid_rerank` (optional extra: semantic chunking)
- Output: `eval/results.md` with a table, a short analysis of where each config fails, and 3 example failures
- Keep the question set fixed after the first run so comparisons are fair

## 17. Load test

- Tool: `k6` or `hey` against the API (keep it small to protect the bill)
- Scenarios: 1, 5, 10 concurrent users for 60 seconds, with a mix of cached and uncached questions
- Record: p50/p95 latency, error rate, cold-start impact, throttling hits
- Put the numbers in the README

## 18. Cost tracking

- Tag everything, check Cost Explorer after the eval and load test
- Compute: total cost / number of queries = cost per 1,000 queries (split: Bedrock vs Lambda vs DynamoDB vs other)
- Note the main cost driver and one optimization you would make

## 19. Testing

- Unit tests: chunker, RRF merge, keyword scoring, prompt builder
- One integration test script that hits the live API with 3 questions
- Tests do not need to be fancy, but they should exist and run with one command

## 20. README outline

1. One-paragraph summary + live link + screenshot
2. Architecture diagram (ingest path and query path)
3. Design decisions: why hand-rolled Lambdas, why S3 Vectors, why hybrid + RRF, why SQS buffering, why structure-aware chunking
4. Eval results table and what I learned
5. Load test and cost numbers
6. How to deploy (`terraform apply`, how to ingest)
7. Limitations and what I would do next

## 21. Progress tracker

Update this as I go.

- [ ] Phase 0: Setup
- [ ] Phase 1: Storage + ingest
- [ ] Phase 2: Retrieval
- [ ] Phase 3: Generation + API
- [ ] Phase 4: Frontend + deploy
- [ ] Phase 5: Eval + load test + cost
- [ ] Phase 6: README + resume updated 
