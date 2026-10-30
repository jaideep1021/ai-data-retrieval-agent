# Developing the next baseline

Start from `main` in a feature branch. Use Python 3.13 and the pinned requirements.
Never add `.env`, keys, local evidence, results or user datasets to commits. Keep
synthetic fixtures small and label their purpose. Do not use `git add -f` to bypass
these exclusions. Review `git status --short`, `git diff` and `git diff --cached`
before committing; `.gitignore` does not remove files already tracked.

For a change, explain the research question, behavior change and limitations.
Run `python -m unittest discover -s tests -v`, `python -m pip check`, and the
optional local-browser test for retrieval changes. Live runs cost quota: keep them
small and record model, date, input and observed results; never publish raw keys or
provider errors. Add failure tests for meaningful new behavior.

The package VERSION identifies the combined release. Do not change agent.__version__:
agent.py is the preserved 0.1.0 baseline. Autonomous development labels identify
the code used in recorded experiments and must not be retroactively rewritten.
Update VERSION, README, CHANGELOG and the release review together. Record the
approved commit and create a new annotated version tag.
Never overwrite v0.1.0 or republish individual deliverable branches.

If dependencies change, resolve in a new environment from requirements.in, freeze
that environment to requirements.txt, and verify installation from scratch.
Record actual checks in docs/release-review-v0.2.0.md. Inspect the full proposed
file set, including untracked files, before staging. Preserve .env, raw runs,
evidence, original data, local backups and machine-specific editor settings.
Reviewed public examples/business data may be included with its source attribution;
this exception does not permit committing private business datasets.

After explicit approval, review staged files and secret exclusions, commit the
combined release, and push the approved branch/commit and new tag. Do not imply
cross-platform, CI or live tests passed unless they actually ran. No project code
license has been selected; public visibility does not itself grant broad reuse.
