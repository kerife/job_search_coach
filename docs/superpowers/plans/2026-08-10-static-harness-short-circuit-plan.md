# Implementation plan: static harness short-circuit

1. Add a focused RED test that makes the second harness fail if invoked after
   a private-schema failure.
2. Run it and observe the current implementation invokes the second harness.
3. Return immediately after printing the first bounded harness errors.
4. Run the focused static/root tests, plugin/static/privacy gates, and diff
   checks.
5. Include this repair with the nullable-pattern release only if all gates are
   green; refresh provenance once and consume the cachebuster once.
