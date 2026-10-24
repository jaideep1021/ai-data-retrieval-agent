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

For a release, update VERSION, agent.__version__, README and CHANGELOG together.
If dependencies change, resolve in a new environment from requirements.in, freeze
that environment to requirements.txt, and verify installation from scratch.
Retain a complete record of actual tests in docs/verification.md. Review the staged
files and secret exclusions, commit, then tag `vX.Y.Z` and push the commit and tag.
Do not overwrite a released tag. Do not imply cross-platform/live tests passed
unless they actually ran. Choose an explicit code license before broad reuse.
