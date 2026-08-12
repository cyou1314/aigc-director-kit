# Metadata-only local Skill adapter

`aigc-director-local-skill-adapter` is a public manifest for describing how a
private local Skill stack connects to CineThread. It records only stage labels,
input and output contract names, and the meaning of each evidence state.

It is deliberately not a Skill export, a prompt pack, or a project handoff.
The manifest must stay safe to publish.

## What this solves

Local production Skills can be much more capable than a public repository:
they can reason about references, direct performance, route image or video
work, and inspect real artifacts. Publishing that implementation wholesale
would expose private methods and make the public core harder to reproduce.

The adapter manifest gives each side a small, stable boundary:

```text
private local Skills
  -> metadata-only adapter manifest
  -> sanitized skill-workflow packet
  -> CineThread deterministic validation and dry-run handoff
  -> optional runtime / real artifact
  -> local evidence-based QC
```

The manifest is reusable across projects. A `aigc-director-skill-workflow`
packet is project-specific and may carry a sanitized shot plan, action
requests, prompt pack, and QC report.

## Validate the public interface

```powershell
python -m aigc_director_kit validate-local-skill-adapter `
  examples/local_skill_adapter_case.json `
  --json
```

The example maps local stage labels to existing CineThread contracts without
shipping any Skill instructions. It is also included in `verify-examples`.

## Required public fields

| Field | Meaning | Safe to publish |
| --- | --- | --- |
| `skill_label` | Stable label, not an installation path or source archive | Yes |
| `role` | Short description of the stage responsibility | Yes |
| `input_contracts` | Names of incoming interface contracts | Yes |
| `output_contract` | Name of the outgoing CineThread or workflow contract | Yes |
| `evidence` | `designed`, `inferred`, or `observed` evidence semantics | Yes |

The manifest fixes `visibility` to `public-metadata-only` and
`source_access` to `local-only`. Unknown fields are rejected, and obvious
credentials or local paths in string values are rejected as a guard against
accidental publication.

That guard is structural, not a guarantee that prose is harmless. Review every
manifest before publishing.

## Keep these out

- Skill source, installation paths, archives, or tool configuration;
- prompt bodies, client briefs, private notes, or reference descriptions;
- character and scene assets, source media, rendered output, or project IDs;
- credentials, cookies, API keys, account identifiers, and machine paths;
- claims that a render or QC pass happened when no artifact was inspected.

Use [`skill-workflow-integration.md`](skill-workflow-integration.md) for the
next step: emitting a sanitized, per-project workflow packet. The adapter
manifest itself never executes a Skill, launches a runtime, renders media, or
proves output quality.
