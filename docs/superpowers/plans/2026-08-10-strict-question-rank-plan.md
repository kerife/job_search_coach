# Plan: strict recruiter-practice question rank

1. Add RED tests for boolean/float `question_rank` and schema/custom parity.
2. Implement the smallest type-safe validator comparison; run focused GREEN
   tests and inspect the diff.
3. Review the implementation independently and update the cycle ledger.
4. Run marketplace/static/privacy/release gates, consume the cachebuster once,
   reinstall the canonical plugin, and verify the exact cache plus final suite.
