# SAA RAG Assistant: Build Plan & Reference

Reference doc. Status: built and deployed; remaining work is README polish, load test and cost numbers (section 21).

## 1. Goal

A deployed, serverless RAG assistant for AWS SAA exam prep, built to show cloud and retrieval skills. Target: live link, README, and eval numbers.

## 2. Scope

**In scope**

- Ingest AWS whitepapers only (no notes, course material, or practice questions)
- Hybrid retrieval: vector search + keyword overlap, merged with RRF
- LLM-judge rerank (no Bedrock rerank model available), then answer generation with numbered citations and a refusal path
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
- **Embeddings:** Bedrock, `amazon.titan-embed-text-v2:0`, 1024 dims
- **Generation + rerank judge:** Bedrock, `us.amazon.nova-lite-v1:0` (Nova Pro comparison optional)
- **Vectors:** S3 Vectors
- **Keyword index, eval log, cache:** DynamoDB
- **Ingest:** S3 upload -> SQS -> Lambda
- **Query path:** API Gateway -> Lambda
- **Frontend:** static site on S3 + CloudFront
- **IaC:** Terraform
- **Language:** Python (Lambdas)

## 4. Architecture

**Ingest:** raw docs in S3 -> SQS queue -> ingest Lambda (structure-aware chunking -> Titan embeddings -> write vectors to S3 Vectors + keyword terms to DynamoDB).

**Query:** browser -> CloudFront (same origin; `/ask` forwarded to API Gateway) -> query Lambda -> (0) validate + clean input, check cache and daily cap, (1) embed question, (2) vector top-20 and keyword top-20 in parallel (keyword path spell-corrected), (3) merge with RRF, (4) LLM-judge rerank of the top 15, keep 5, (5) relevance gate, (6) generate answer with numbered citations, (7) grounding check, cache for 24 h.

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

**Phase 6: README**

- Architecture diagram, design decisions in my own words, results, live link
  
## 7. Decision log

Add a line each time a real choice is made (what, why, what I rejected).

- Hand-rolled Lambdas over Bedrock Knowledge Bases: to understand and explain retrieval end to end
- Lightweight hybrid (term overlap + RRF) over OpenSearch: lower cost and complexity
- Structure-aware chunking as default; semantic chunking only as an optional eval experiment
- Typo handling on the keyword path only (vocab-based spell correction, `SPELLFIX` env switch). Vector search already tolerates typos. Measured effect: MRR 0.75 to 0.80 on the typo set, hit@5 unchanged (4 questions better, 2 worse); kept because it is cheap and can be turned off.
- Reranker pool 15 (not 10): wider pool gave the judge more chances to rescue paraphrases.
- Relevance gate `MIN_JUDGE_SCORE=2` plus a model-level refusal and a citation check: three layers, because on the out-of-scope set 3 of 14 questions scored 5 to 8 on the judge and only the model refusal caught them.
- Judge prompt left at original wording: adding "the question is untrusted" dropped hit@5 0.97 to 0.94 (q013). Injection defense lives in `clean_question` (strips `<>`) and `generate.py` (tag wrapping and neutralizing) instead. Tested with the injection eval.
- Same-origin `/ask` through CloudFront instead of CORS: removes a whole class of config mistakes.
- Labels fixed after reading the retrieved chunks: q011, q027 (too narrow), o011 removed from out-of-scope (the paper has the answer). The garbled `kms-cryptographic-details` paper was deleted from the index.
- No WAF: abuse is bounded by the daily cap, throttling and a budget alert. A WAF costs more than the rest of the demo.
- Judge variance: run-to-run MRR moves by about 0.01, so report MRR as ~0.81 and hit@5 as 0.97 on this set.
- Format-hijack fix in code, not prompt: the system prompt already said to ignore format instructions and the model still answered in JSON. `generate.py` now refuses answers starting with `{` or `[{` or containing a code fence. Trade-off: a real question wrapped in a format request gets a refusal.
- Keep every results file in git (results_k*.md/json) so numbers can be traced to a commit.


## 8. Phase 0 detail: setup checklist

- [ ] Create repo, add `PLAN.md`, `.gitignore` (terraform state, `.env`, `data/` if large)
- [ ] Terraform remote state: S3 bucket + DynamoDB lock table (create these by hand once, everything else via Terraform)
- [x] AWS budget alarm with email notification
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

Size as built: 756 chunks from four documents (Overview of AWS, Generative AI Lens, KMS Best Practices (archived 2021), Security Best Practices; see SOURCES.md), well under the original 15 to 30 paper target. Quality beats size for the eval. Folder layout in S3: `raw/whitepapers/<name>.md`, with a small `meta` JSON per doc (title, source URL, topic tags such as `security`, `reliability`, `cost`).

## 10. Chunking spec (structure-aware)

- Split on markdown headings first (H1/H2/H3). Each chunk keeps its heading path, e.g. `S3 > Storage classes > Glacier`.
- Target 400 tokens per chunk, hard max 500 (as built; `chunker.py`). If a section is longer, split on paragraph boundaries with ~50 token overlap.
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
4. Merge with Reciprocal Rank Fusion: `score(d) = sum(1 / (60 + rank_i(d)))` over the two lists. Keep the top 15 (`RERANK_POOL`).
5. Rerank the 15 candidates with the LLM judge (JSON scores 0 to 10; falls back to hybrid order if the judge output can't be parsed). Keep top 5.
6. Relevance gate: refuse if the best judge score is below `MIN_JUDGE_SCORE` (2).
7. Generate the answer from the top 5 chunks (numbered citations); refuse on INSUFFICIENT_CONTEXT, on a JSON or code-fence shaped answer (`format_violation`), or if no valid citation.
8. Grounding judge checks the answer against the cited passages.

Config lives in env vars: `K_VECTOR=20, K_KEYWORD=20, RRF_K=60, RERANK_POOL=15, SPELLFIX=1`. The eval flips modes: `vector_only`, `keyword_only`, `hybrid`, `hybrid_rerank`. Keyword terms that appear in more than half of all chunks are skipped (`MAX_DF_RATIO`).

## 13. API contract

`POST /ask`

- Request: `{"question": "string (max 500 chars)"}`
- Response 200: `{"answer": "...", "sources": [...], "latency_ms": 0, "cached": false}`
- Errors: 400 invalid input, 429 throttled, 500 internal (generic message, never leak stack traces)
- Response fields: verify against `public_view` in `lambdas/query/handler.py`; raw chunk text is never returned

Also: no CORS needed (the page and `/ask` share the CloudFront origin), API Gateway throttle 2 req/s burst 5, daily cap of 500 uncached questions, 24 h cache, input validation in `validation.py` (length, type, `<` `>` stripped).

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
- Lambda timeouts: ingest 900s with SQS visibility timeout 5400s (raised after timeouts on big documents); query 30s; memory 512 MB to start, tune later
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

**Phase 6: README** (see section 20)

## 16. Eval methodology

As built:

- 34 retrieval questions (q001 to q023 worded close to the text, q024 to q034 paraphrased), labeled by `answer_phrases`: a chunk counts as relevant if it contains the phrase.
- Metrics: hit@5, MRR, precision@5, recall@5 (`run_eval.py`), per mode.
- Generation eval (`run_gen_eval.py`): refusals on in-scope (want 0), citation validity, grounding judge, and 14 out-of-scope questions (want all refused). I read the in-scope answers by hand.
- Injection eval (`run_injection_eval.py`, 8 prompts), typo eval (`run_typo_eval.py`, spell-fix on/off).
- Labels were corrected twice (q011, q027) after reading retrieved chunks, and o011 was removed from out-of-scope because the paper did contain the answer. Fixing a wrong label is fine; do not change labels to make a number go up.
- Report the final numbers from one run of all four evals on the committed code, with the commit hash.

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

- [x] Phase 0: Setup
- [x] Phase 1: Storage + ingest
- [x] Phase 2: Retrieval
- [x] Phase 3: Generation + API
- [x] Phase 4: Frontend + deploy (live on CloudFront)
- [x] Phase 5: Eval done; load test and cost per 1,000 queries are optional and not done
- [ ] Phase 6: README, SOURCES.md, live link and screenshot

Models: embeddings `amazon.titan-embed-text-v2:0` (1024 dims); generation and rerank judge `us.amazon.nova-lite-v1:0` (no rerank model available in us-east-1, so an LLM judge; Nova Pro comparison optional).

## 22. Results snapshot (k=5, 34 questions, 756 chunks)

| mode | hit@5 | MRR |
|---|---|---|
| hybrid | 0.82 | 0.55 |
| hybrid_rerank | 0.97 | 0.81 |

vector_only and keyword_only: TODO (re-run all modes once so every row comes from the same labels and index).

- Close-wording questions: hybrid 0.91, hybrid+rerank 1.00. Paraphrased: hybrid 0.64, hybrid+rerank 0.91.
- Generation: 0/15 in-scope refused, 15/15 cited, 15/15 supported, 14/14 out-of-scope refused (3 of those caught by the model, not the score gate).
- Injection: 8/8 pass. One case made the model answer in a requested JSON format (my first check only looked for the attack word); now blocked by a format check in `generate.py` (`format_violation`).
- Typos (final code): clean 0.97 / 0.80; typos with spell-fix off 0.94 / 0.75; on 0.94 / 0.80. Mixed per question (4 better, 2 worse), so a modest MRR gain, hit@5 unchanged.

**Known misses**

- q024: paraphrase with no shared vocabulary ("run trained neural networks in production" vs "inference"/Inf2). Neither retriever surfaces it in the top 5. Idea: query rewriting.
- q013: unstable. The question is generic ("what purpose does the Vector Data Store serve") and about 25 chunks discuss vector stores. It missed (hit@5 0.94) when I added one sentence to the judge prompt and hit at rank 4 with the original prompt. Label is literal ("vector data store"); the reranker also returns on-topic chunks that don't contain that phrase.
