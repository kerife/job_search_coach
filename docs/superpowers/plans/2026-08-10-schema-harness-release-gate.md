# Plan: include schema harness in release discovery

1. Add a RED integration assertion that imports and exercises the private schema
   harness from `tests/test_full_plugin.py`.
2. Run the full-plugin test to confirm RED, then implement the minimal import /
   mutation assertion and verify GREEN.
3. Run focused/full relevant checks, publish once, install exact version, and
   verify identity.
