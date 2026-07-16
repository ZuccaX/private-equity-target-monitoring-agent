# Milestone 2 Retrieval Evaluation

- Fixture cases: `3` (expected hit, injection-isolation hit, type-filtered empty)
- Provider: `sentence_transformer`
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- Dimension: `384`
- Recall@K: `1.000`
- MRR: `1.000`
- Cross-company/forbidden leakage: `0`
- Empty cases: `1`
- Model loading: offline/local-files-only

The same deterministic fixture is intended for host and disposable Docker
checks. A separate missing-cache probe verifies the explicit
`model_unavailable -> hashing` fallback without mixing cohorts.

The fixture resolves companies by stable domain, requires company-scoped RAG,
checks forbidden cross-company document IDs, validates the empty case and
confirms prompt-injection isolation. These are deterministic demo-corpus
regression metrics, not a claim of general production retrieval quality.
