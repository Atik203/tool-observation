# Security policy

## Supported versions

| Version | Supported |
|---|---|
| `0.1.x` (scaffold) | Yes — security fixes only |
| `< 0.1.0` | No |

The repository is pre-confirmatory. There is no hosted service and no production deployment.

## Reporting a vulnerability

Use **GitHub Security Advisories** for private reporting:

<https://github.com/Atik203/tool-observation/security/advisories/new>

Do not open a public issue for a vulnerability. Do not attach exploit details, credentials, or
personal data to a public issue.

Include, where possible:

- affected file, commit, or version;
- reproduction steps or a minimal proof of concept;
- impact assessment (secret exposure, PII exposure, code execution, dependency risk);
- whether the issue affects a release artifact or only the development tree.

## What to report

- **Secrets** committed or exposed: API keys, GitHub tokens, Hugging Face tokens, cloud or
  GPU credentials, SSH keys, `.env` contents.
- **PII or data leaks**: names, emails, addresses, phone numbers, payment identifiers, or raw
  τ-bench trajectories in a tracked file or release.
- **Dependency vulnerabilities** that affect the package or the release environment.
- **Code execution or path traversal** in pipeline scripts, config loading, or the renderer.
- **Release integrity**: a modified frozen manifest, mismatched hash, or unreviewed ToolResult-800
  artifact.

## Secret handling

- Never put secrets in the repository, issues, PRs, logs, notebooks, configs, or screenshots.
- Use environment variables or a local, gitignored `.env`; never commit `.env`.
- Rotate any credential that was pasted into chat, a commit, or a log. A deleted file in git
  history is still exposed until the credential is rotated.
- If a secret is committed, treat it as compromised, rotate first, then clean history.

## Data handling

τ-bench historical trajectories may contain **PII** (names, emails, addresses, phone numbers,
payment identifiers). Treat all raw trajectories as PII-bearing even before scrubbing.

- Never commit `data/raw/`, `data/upstream/`, `data/interim/`, `data/frozen/`, or `data/runs/`.
- Never commit raw trajectories, unscrubbed observations, or run ledgers containing PII.
- The public ToolResult-800 release must pass the scrub and PII audit in `release/README.md`.
- If you believe PII has entered a release, report it privately and do not download or
  redistribute the artifact.

## Response expectations

- Acknowledgement within **5 business days**.
- Initial assessment within **10 business days**.
- Fix or mitigation target within **30 days** for critical secret/PII exposures; best effort for
  lower-severity issues.
- We will credit reporters unless they prefer to remain anonymous.

These are good-faith targets for a small research team, not a contractual SLA.

## Out of scope

- Vulnerabilities in upstream τ-bench, model weights, vLLM, or third-party packages that are
  already reported upstream (report them upstream; tell us if they affect this project).
- Denial-of-service against local scripts with no security boundary.
- Findings that require committing secrets or PII to demonstrate.
