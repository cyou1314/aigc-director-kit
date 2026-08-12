# CineThread workflow integration

This repository is the deterministic public core for a larger AIGC workflow.
It does not bundle Codex skills, private assets, Blender files, model accounts,
or paid generation services. A local workflow can produce a public handoff,
then this package validates the handoff and compiles bounded action requests.

## Boundary

```text
local Skill workflow
  -> aigc-director-skill-workflow JSON
  -> validate-workflow
  -> validate-plan + compile-action
  -> prompt-pack JSON + qc-report JSON
  -> optional Blender / FFmpeg / runtime adapter
  -> separately recorded render or QC evidence
```

`validate-workflow` does not run an external Skill, render a scene, call a
model, inspect a video, or prove final visual quality. It only checks the
public contract and, when an action catalog is supplied, performs a dry-run
against known action descriptors.

## Skill-to-contract mapping

| Workflow responsibility | Public handoff | Boundary |
| --- | --- | --- |
| Story or visual direction | `shot_plan` | The plan is a designed or observed contract, not a rendered result. |
| Audio, pacing, or action intent | `action_requests[]` | Only catalog actions can be selected; unknown actions fail. |
| Project coordination | `stages[]` and `handoff` | Stage names are labels, not runtime dependencies. |
| Prompt writing and revision | `aigc-director-prompt-pack` | Global rules are written once; each shot carries only its delta and contract. |
| Blender previs | Optional runtime adapter | Blender is not a core dependency. |
| FFmpeg preprocessing | External evidence step | Original media remains outside this public repository. |
| Video QC | `aigc-director-qc-report` | Pass/fail requires observed evidence from an available artifact. |

The example uses `aigc-manga-video-director`, `audio-to-prompt`, and
`aigc-project-prompt-loop` as illustrative stage labels. They are not bundled
with this Python package and can be replaced by another workflow producer.

## Metadata-only local Skill adapter

Before a project-specific workflow packet exists, a local workflow may publish
an `aigc-director-local-skill-adapter` manifest. It maps only a stable Skill
label, its input and output contract labels, and the evidence semantics of the
stage. It is intentionally reusable and contains no project content.

```powershell
python -m aigc_director_kit validate-local-skill-adapter `
  examples/local_skill_adapter_case.json `
  --json
```

The adapter is not a Skill export and does not execute a Skill. Its strict
metadata-only field set rejects prompt bodies, paths, assets, and credentials.
The separate [`local-skill-adapter.md`](local-skill-adapter.md) guide explains
what may safely appear in a public manifest.

Cross-check the adapter and project workflow together before publication:

```powershell
python -m aigc_director_kit validate-skill-integration `
  examples/local_skill_adapter_case.json `
  examples/skill_workflow_case.json `
  --library examples/action_library.json `
  --json
```

This requires every used workflow stage to match the adapter's id, Skill label,
output contract, and evidence semantics. It verifies required producers and
high-confidence public-safety patterns, but it cannot determine whether all
free-form prose is anonymous. Manual privacy review remains required.

## Run the public handoff

Without an action catalog, the workflow is checked structurally and action
requests receive an explicit not-compiled warning:

```powershell
python -m aigc_director_kit validate-workflow examples/skill_workflow_case.json
```

With the descriptor-only catalog, the action bridge is compiled deterministically:

```powershell
python -m aigc_director_kit validate-workflow `
  examples/skill_workflow_case.json `
  --library examples/action_library.json
```

For machine-readable output, add `--json`. The output is a validation and
dry-run report; a runtime adapter still has to map action ids to real assets.

## Build a runtime adapter handoff

When the next tool needs one packet containing the validated shot plan, prompt
pack, compiled action requests, and evidence boundary, build a runtime
handoff:

```powershell
python -m aigc_director_kit build-runtime-handoff `
  examples/skill_workflow_case.json `
  --library examples/action_library.json `
  --adapter blender-previs `
  --json
```

This command creates a `aigc-director-runtime-handoff` packet in `dry-run`
mode. `runtime.executed` stays `false`, `render_status` stays `not_run`, and
the packet does not launch Blender, resolve motion files, render media, or
claim QC. An adapter may consume the packet and must record its own runtime
and media evidence separately.

## Prompt and QC contracts

The prompt-pack contract keeps reusable character, scene, style, stability,
and avoid rules in `global_rules`. Each shot must retain a primary task,
action causality, camera job, entry state, exit state, duration, and complete
prompt text. When a source shot plan is supplied, ids are cross-checked and a
duration drift is reported as a warning.

The QC contract is deliberately stricter than a prompt check. A report may be
`unverified` or `not_run` when no render is available. A `pass` or `fail`
check must use `observed` evidence and an available artifact. This keeps a
contract audit, a dry-run, and actual video QC as separate evidence layers.

Both layers can also be embedded in the workflow packet as optional
`prompt_pack` and `qc_report` fields. When present, `validate-workflow` checks
them against the embedded shot plan and exposes their status in the summary.

```powershell
python -m aigc_director_kit validate-prompt-pack `
  examples/prompt_pack_case.json `
  --plan examples/one_take_previs_case.json

python -m aigc_director_kit validate-qc-report `
  examples/qc_report_unverified_case.json
```

## Adding a new workflow producer

1. Emit a sanitized `aigc-director-skill-workflow` document.
2. Put the producer name, role, output contract, and evidence status in a
   `stages[]` entry.
3. Embed a versioned `aigc-director-shot-plan` in `shot_plan`.
4. Put natural-language action intent in `action_requests[]` with a shot and
   stage reference.
5. Run `validate-workflow --library ...`, then
   `validate-skill-integration <adapter> <workflow> --library ...` before
   publication or runtime handoff.
6. Manually review the final adapter and workflow for private prose or asset
   identities that automated checks cannot infer.
7. Run `build-runtime-handoff ... --adapter ...` when the next runtime needs a
   single dry-run packet.
8. Add a public example and a regression test when the contract changes.

Keep private source paths, credentials, cookies, private character assets,
unlicensed motion data, and generated media out of the packet. Mark inferred
intent and unverified render/QC claims explicitly instead of presenting them
as observed community or production evidence.
