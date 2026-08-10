# Plan: close follow-through schema invariants

1. Add RED tests that validate follow-through fixtures and reject mismatched
   action/event mappings through Draft 2020-12 schema validation.
2. Add minimal `allOf` conditionals to the schema and run the focused contract
   suite.
3. Run static checks and diff checks; preserve the closed artifact boundary.
