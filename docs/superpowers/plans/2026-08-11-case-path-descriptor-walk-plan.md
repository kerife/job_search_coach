# Case Path Descriptor Walk Plan

1. Add RED tests for an intermediate parent symlink and nested symlink, plus
   relative/regular path compatibility.
2. Implement anchored parent descriptor walking with trusted macOS alias
   exceptions and leaf `O_NOFOLLOW` openat.
3. Close descriptors on all paths and preserve existing byte/error contracts.
4. Run focused case, structure/privacy, static, plugin, and release suites.
5. Bump once, install, refresh provenance/attestation, compare source/cache, and
   run installed smoke.
