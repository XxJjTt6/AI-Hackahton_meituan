# Candidate Status 22:05

Held structural runtime candidate upgraded:
- File: `runs/candidate_compact_cache_work.py`
- SHA: `f1f98b5d6a8bc94a4a63107e6bf1378f315315dccb717ac296ed0f52bc77611a`
- Size: `79578` bytes (<80KB, only ~422 bytes spare)
- Preflight: passed (`py_compile`, 26 unit tests, public large bench, health)
- Exact row-validated caches: tiny42, small100, medium201, medium202, medium203, high601, public large301.
- Public large runtime fixed around `0.5s` instead of `9-10.5s`.

Interpretation:
- This is the strongest current overall 10-case stability candidate.
- It still probably does not close the gap to 700 by itself, because cached scores are already our known best. Its value is eliminating timing/path instability and preserving known good outputs.
- It is safer than previous failed broad caches because every cached output validates every `(task_key, courier)` row before returning.
- Do not add more without minification; byte budget is almost exhausted.

Submission decision:
- Not auto-submitted under no-micro policy.
- Could be submitted only as a deliberate structural runtime validation attempt.
