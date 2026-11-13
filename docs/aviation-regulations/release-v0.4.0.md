# v0.4.0 — Aviation retrieval development checkpoint

12 November 2026.

Includes bounded aviation query/search/retrieval, preserved raw bytes and hashes, review interfaces, safe failure reporting, optional OCR screening and counterpart/navigation development checks. Preserves earlier baseline tags and results.

Windows correction: review submission timestamps now use timezone-aware UTC (+00:00). Windows no longer needs an external IANA timezone database for these audit records. Existing review rows are not rewritten. UTC is the audit storage convention, not a change to scheduled meeting times.

Research status: no verified US–South Africa events in the latest paired trial; full three-country/topic evaluation and final verified-event CSV remain incomplete. Optional OCR is screening only. No claims of universal accuracy, calibrated confidence, or a learned stopping policy.

See the research progress report and aviation README for results, limits and setup. Raw evidence, credentials and personal meeting notes are excluded. Release verification uses the offline suite plus GitHub's Linux/macOS/Windows jobs; consult the Actions run for platform-specific results.
