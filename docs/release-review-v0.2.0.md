# v0.2.0 local release review

**Date:** 2026-10-28
**Package VERSION:** 0.2.0
**Preserved baseline:** agent.py reports 0.1.0; existing v0.1.0 tag unchanged

## Package contents

Include the preserved baseline, single/multi-source automatic paths, provider
adapters, evaluation/data-preparation/report tools, pinned dependencies, tests,
configuration template, research documentation, sanitized evaluation records,
and the reviewed public 30-market airline sample with attribution/provenance.
Contributor guidance is in CONTRIBUTING.md; machine-specific agent instructions
remain local.

Exclude .env, keys, raw runs and evidence, original local result files, environments,
backups, screenshots and machine-specific .vscode settings. These files remain
in place locally; they were not deleted or moved. The public business sample is
reviewed aggregate government data, not a private customer dataset.

## Actual checks

- Fresh virtual environment created under ignored `runs/release-review-20261028/`.
- Installed the existing pinned requirements from scratch into that environment.
  Dependencies were not upgraded and the pins were not changed.
- Copied the candidate source files into a clean checkout directory, excluding
  ignored keys, environments, raw runs, evidence and editor settings.
- **67 tests passed** against that clean source copy in the fresh environment,
  including the real Chromium test with local HTML. Existing installed Chromium
  was reused; this does not claim a fresh browser download.
- `pip check`: no broken requirements. CLI help for multi-source, evaluation and
  business preparation worked. Baseline version output remained 0.1.0.
- Reviewed the completed 60-trial evaluation and 30-record business sample; no new
  paid API benchmark was run during release preparation. Existing live findings
  remain authoritative, with their documented limitations and failures.
- Final audits verified reference links, public-result summary consistency, sample
  hashes, configured-key absence, ignored output paths, and source preservation.
  The clean-copy install/test logs and candidate file inventory remain local.

This is a macOS/Python 3.13 check. Windows/Linux and remote GitHub Actions were not
executed here. The repository contains a CI workflow but no new passing remote CI
run is claimed. Local raw-evidence hashes do not authenticate source correctness.

## Version and documentation decisions

The package version is 0.2.0. The
original agent stays 0.1.0 and the automatic files retain their experimental
version strings, preserving interpretation of historical run manifests. README
now separates Week 1 checkout instructions from Week 2 reproduction, and the
roadmap distinguishes implemented work from proposed business-domain adaptation.

The project code still has no chosen open-source license. No license was invented
on the user's behalf. Dataset source-license metadata and dependency terms remain
separate from permission to reuse the project's code.

## Release boundaries

The existing v0.1.0 tag and original baseline are preserved. No business-domain
retrieval accuracy, prediction capability or new remote CI result is claimed.
Git publication is a separate action; the checks above describe local validation.
