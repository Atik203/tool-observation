# Data license — ToolResult-800

## Summary

| Component | License |
|---|---|
| ToolResult-800 additions: perturbations, prose renderings, manifests, labels, recovery traces, and derived tabular data | **CC BY 4.0** |
| Upstream τ-bench code and data | **MIT** (as distributed by the τ-bench authors) |
| Third-party model weights and outputs | Under each model's own license |
| Project source code | **MIT** (`LICENSE`) |
| Project documentation | **CC BY 4.0** (`LICENSE-DOCS`) |

ToolResult-800 is a derived dataset built on the public τ-bench historical trajectories. It is not a
re-license of τ-bench. Upstream notices and license terms are preserved.

## Upstream τ-bench

- Source: the public τ-bench repository and its `historical_trajectories/` files.
- Upstream license: MIT. The upstream copyright notice and permission notice are retained in
  the release package.
- Citation: the τ-bench paper and repository must be cited by any use of ToolResult-800.
- The project pins a specific upstream commit; see `configs/harvest.yaml` and
  `data/manifests/`.

## What CC BY 4.0 covers

The following additions are released under CC BY 4.0:

- the frozen 800-prefix selection and its manifests;
- perturbation records (JSON path, true value, false value, criticality label, expected action
  change);
- deterministic prose renderings and the renderer version;
- severity and outcome labels produced by this project;
- recovery traces and derived decision signatures;
- aggregate tables, figures, and documentation.

Attribution should name **ToolResult-800 / tool-observation**, the authors, the CC BY 4.0 license, and
the upstream τ-bench source, and should indicate whether changes were made.

## What is not released

- Raw τ-bench trajectories. Users obtain them from upstream under the upstream license.
- Unscrubbed observations or any file containing PII.
- Model weights, adapters, caches, or GPU credentials.
- Third-party content that the project has no right to re-license.

## PII

τ-bench trajectories can contain names, emails, addresses, phone numbers, and payment
identifiers. The release pipeline excludes profile tools and replaces direct identifiers with
stable synthetic tokens. No raw PII is released. If you believe PII is present in a ToolResult-800
artifact, report it privately per `SECURITY.md`; do not redistribute the artifact.

## Redistribution and notices

If you redistribute ToolResult-800 or a derived work:

1. Include this file, `LICENSE-DOCS`, the MIT `LICENSE`, and the upstream τ-bench notice.
2. Preserve the attribution and the modification indication.
3. Do not imply endorsement by the authors or by the τ-bench authors.
4. Do not add legal or technical restrictions that prevent others from exercising the CC BY 4.0
   rights in the derived portions.

## No warranty

The data is provided "as is", without warranty of any kind. The authors are not liable for any
claim, damages, or other liability arising from its use. See the full CC BY 4.0 text:
<https://creativecommons.org/licenses/by/4.0/legalcode>.
