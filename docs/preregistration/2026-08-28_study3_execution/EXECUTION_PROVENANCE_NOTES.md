# Study 3 — execution / provenance notes

## N1 (2026-08-29) — accidental staging of the quarantined build into a local commit

During the Amendment-2 tooling commit, a directory-level `git add` staged the quarantined
prevalidation build (`baseline/`, tree `3ea64b31…`, containing task P32's materialized
host output) into a local commit. Caught immediately on reviewing the commit stat, before
any push: the quarantined paths were removed from the index (`git rm --cached`) and the
commit was amended; the amended commit (`9bac069`) was verified to contain zero
`baseline/` paths. The superseded local object is dangling, unreferenced, was never
pushed, and is NOT a research artifact — it is left to normal git garbage collection.
`.gitignore` entries for the quarantined build and the sealed materialization directory
were added in `e1db149` to prevent recurrence. Verification that the current branch
history, index, and all push-visible refs contain no quarantined content is recorded
below (N3).

## N2 (2026-08-29) — controlled backup of the sealed FROZEN_CASE_MANIFEST

- Original `sealed_materialization/FROZEN_CASE_MANIFEST.json` untouched.
- One controlled copy stored on the same host in a user-home hidden directory on local
  disk, outside the repository and outside normal sync targets; permissions read-only.
- Copy verified byte-identical to the frozen manifest:
  sha256 `2422431ac301aa4e439fe4ff2bdc7e23d6dfd2ffdf836cd8bdbda3ed25df2a36`.
- No raw content is reproduced in any research log; this note records storage category
  and hash only.
- Recovery rule (binding): only a copy hashing exactly to `2422431a…` may ever be
  accepted as the manifest; "regenerating an equivalent manifest" is prohibited
  (Amendment 2, clauses 10–11).

## N3 (2026-08-29) — ref-cleanliness verification for the quarantined content

Recorded at the time of the formal baseline rebuild: `git ls-files` (index) and the full
name-history of every push-visible ref contain no path under the quarantined build or the
sealed materialization directory. The quarantined build itself was moved on disk to
`quarantined_prevalidation_build/` (relative-path tree hash `3ea64b31…` unchanged by the
parent-directory rename) so the formal rebuild could occupy `baseline/`; both directories
remain gitignored and uncommitted.
