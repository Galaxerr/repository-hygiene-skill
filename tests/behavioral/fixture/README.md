# Ledger maintenance example

Run `python3 -B -m ledger` for the supported CLI and `python3 -B -m unittest -v` for the local contract tests. The CLI loads the profile's enabled modules at runtime. The `extended` profile is supported alongside the default `standard` profile. Modules register renderers when imported.

The supported library API is `ledger.service.public_export`. Client programs run outside this checkout. Names prefixed with an underscore are private implementation details.

## Operator runbook

- Maintained customers can upgrade snapshots using the v1 reader. Current snapshots use v2. Keep both readers during supported upgrades.
- Restore a backup through `ledger.service.restore_snapshot` during incident recovery. Restoring requires both an operator role and scope over the target ledger. Those checks have independent inputs.
- A transient store write is retried once. Permanent failures must surface to the caller.
- CSV and text imports apply the same single-row validation contract. Both reject an empty label after trimming.
