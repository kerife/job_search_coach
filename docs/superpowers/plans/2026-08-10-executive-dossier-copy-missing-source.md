# Plan: missing copy-source feedback

1. Add a RED regression asserting the handler reports failure when the source
   node is absent.
2. Set the existing status node to the fixed failure message before returning.
3. Run focused dossier tests and publish/install with the normal release gates.
