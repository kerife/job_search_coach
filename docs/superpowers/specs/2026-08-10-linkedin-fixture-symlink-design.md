# LinkedIn fixture symlink boundary

## Goal

Prevent committed or supplied LinkedIn report fixtures from escaping their
declared inventory through filesystem symlinks.

## Evidence and scope

`validate_linkedin_client_report.load_bundle()` follows symlinks, the CLI reads
the report and bundle paths directly, and
`validate_linkedin_report_fixture_directory()` uses `is_file()` plus reads that
also follow symlinks. A temporary fixture directory with `scenario-a.json`
symlinked to an external valid JSON file passes the validator and static
inventory with no errors. This change is limited to loader, CLI, and static
fixture-directory preflight; regular report/bundle files and existing
duplicate-key/privacy validation remain unchanged.

## Design

Reject a symlink input before reading it with the existing bounded `ValueError`
boundary. The CLI applies the same guard to both report and bundle arguments.
In the static inventory, reject the fixture root itself and any expected report
or bundle whose path is a symlink before `is_file()`/read operations, using a
stable path-only diagnostic. Do not resolve, read, or echo the target. The
static checker should continue validating regular files and
reporting missing/unexpected artifacts in the existing order.

## Acceptance

- Regular report and bundle fixtures still validate unchanged.
- `load_bundle()` rejects a symlink with a bounded error and no target echo.
- CLI validation rejects a symlink bundle without accepting/rendering it.
- Static fixture inventory rejects symlink reports and bundles before reading.
- Existing duplicate-key/privacy, report-pair, schema, and renderer behavior is
  preserved.
