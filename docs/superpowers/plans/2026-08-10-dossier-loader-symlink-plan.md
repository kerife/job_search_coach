# Implementation plan: dossier loader symlink boundary

1. Add RED loader and CLI tests using a temporary regular target plus symlink.
2. Run the focused tests and confirm the current loader follows the symlink.
3. Add the minimal `is_symlink()` guard before reading the path.
4. Run focused dossier/privacy/plugin/root/static checks and review the diff.
5. Refresh provenance, consume the cachebuster once, publish, reinstall the
   exact version, and rerun the final matrix.
