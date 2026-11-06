# Week 3 release review and Git guide

Proposed release: **v0.3.0 — Week 3 research**. This extends the existing project;
it does not replace or move v0.1.0 or v0.2.0. VERSION is prepared locally. No commit,
tag or push has been made during this preparation. Internal experiment version
identifiers and frozen snapshots deliberately retain their original values.

## What is included

The exact allowlist is [release-v0.3.0-files.txt](release-v0.3.0-files.txt).
It includes business retrieval and evaluation code, pinned additional dependencies,
CI dependency updates, tests, blinded public sample inputs and separate benchmark
references, sanitized experiment results, the rejection audit, literature review,
proposed experiment specification, and the comprehensive report in Markdown and Word.
The decision experiment is explicitly a proposal; no simulator is included.

The benchmark answer file is public for reproducibility but must not be given to
the retrieval agent. Raw responses are not included. Source snapshot hashes and
sanitized metrics are available, but reproducing the private evidence audit needs
the original local runs.

## What is excluded

All of runs/, including Weekly_Correspondence_and_Accomplishments.docx, older
correspondence logs, private meeting guides, raw evidence and local environments;
.env and credentials; screenshots; local backups; AGENTS.md. No private email
archive is included in the public report. The public report is docs/week3-report.docx.

## Review and publish after approving the files

Run these from the canonical project folder. Inspect any existing staged files
before proceeding; do not blindly include unrelated changes.

```sh
cd /Users/jaideepmanupati/Downloads/Programming/ai-data-retrieval-agent
git status --short
git diff --cached --name-only
git diff --stat
cat docs/release-v0.3.0-files.txt
git check-ignore .env runs/Weekly_Correspondence_and_Accomplishments.docx
git fetch origin --tags
git tag --list
```

Create a release branch, then stage only the reviewed allowlist:

```sh
git switch -c release/v0.3.0
git add --pathspec-from-file=docs/release-v0.3.0-files.txt
git diff --cached --check
git diff --cached --name-only
git diff --cached --stat
git diff --cached
```

Press q to leave the diff viewer. Open the public Word report separately because
Git does not show a readable Word diff. Confirm no private files are staged.
Use your configured Python environment to run:

```sh
python -m pip install -r requirements-business.txt
python -m unittest discover -s tests
python -m pip check
```

After reviewing the files and passing checks:

```sh
git commit -m "Release v0.3.0: Week 3 DOT experiments and research report"
git switch main
git merge --ff-only origin/main
git merge --ff-only release/v0.3.0
git tag -a v0.3.0 -m "v0.3.0: Week 3 research"
git show --no-patch v0.3.0
git push --atomic origin main refs/tags/v0.3.0
git ls-remote --heads --tags origin
git status
```

If a branch/tag already exists or a fast-forward merge fails, stop and inspect
instead of forcing, deleting tags or rewriting history. The final commands publish
the reviewed commit and tag; they have not been executed during preparation.
