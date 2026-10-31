# Development rules

- Live Home Assistant development and testing must use only MCP server `ha-test`,
  assigned by the owner to `192.168.178.147`. Never use the production Home
  Assistant connection for this project, including as a fallback.
- Local builds and tests using synthetic data are allowed.
- Never commit passwords, API tokens, real documents, or private OCR text.
- Update `todo.md` after each completed work package, recording actual test
  results, limitations, and pending work. Do not check off unexecuted live tests.
- Current development Paperless address: `http://192.168.178.10:8810`.
  Credentials belong in the integration configuration, not source or fixtures.
- Run the checks in `.github/workflows/tests.yml` before pushing changes.
