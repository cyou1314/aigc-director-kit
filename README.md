# CineThread

> Deterministic creative handoffs for AI animation, storyboards, and previs.

`CineThread` is the public product name. The Python package, CLI command, and
versioned JSON contract identifiers remain `aigc-director-kit` in the 0.x
series for compatibility.

## Verify a checkout in one command

After cloning or extracting this repository, run the verification from the
repository folder:

```powershell
# Windows terminal (when the Python launcher is installed)
py -3 -m aigc_director_kit verify-examples --json --output cinethread-verify.json

# macOS or Linux
python3 -m aigc_director_kit verify-examples --json --output cinethread-verify.json
```

It checks every public plan, adapter/workflow integration, prompt-pack,
QC-boundary, action, and runtime-handoff example, and returns a privacy-safe
report with relative paths only. It does not render or generate media. For a real bug report, review the
output first and use the [60-second trial guide](docs/try-it.md) or the
[Verified run feedback](https://github.com/cyou1314/cinethread/issues/new/choose) form.
Windows users who do not know which Python command to use can instead double-click
[`run_examples.bat`](run_examples.bat); it detects common Python installations.

## Skill workflow handoff

Local AIGC Skills can publish a metadata-only adapter, then hand a sanitized
workflow packet to this repository:

```text
local Skills -> metadata-only adapter -> skill-workflow JSON -> validate-workflow -> optional runtime adapter
```

The public contract is documented in [`docs/skill-workflow-integration.md`](docs/skill-workflow-integration.md),
with a runnable example at [`examples/skill_workflow_case.json`](examples/skill_workflow_case.json):

```powershell
python -m aigc_director_kit validate-workflow `
  examples/skill_workflow_case.json `
  --library examples/action_library.json
```

This is a deterministic handoff and dry-run boundary. It does not bundle
private Skills, Blender, FFmpeg, model accounts, paid generation, or final
video QC.

The optional adapter manifest makes the boundary explicit: it maps only Skill
labels, input/output contract names, and evidence semantics. It cannot carry
Skill source, prompts, paths, assets, or credentials. See
[`docs/local-skill-adapter.md`](docs/local-skill-adapter.md) and validate the
included example with:

```powershell
python -m aigc_director_kit validate-local-skill-adapter `
  examples/local_skill_adapter_case.json `
  --json
```

Validate that the reusable adapter and one project workflow actually agree:

```powershell
python -m aigc_director_kit validate-skill-integration `
  examples/local_skill_adapter_case.json `
  examples/skill_workflow_case.json `
  --library examples/action_library.json `
  --json
```

This cross-check rejects undeclared workflow stages, mismatched Skill labels,
output contracts or evidence semantics, action requests assigned to the wrong
producer, and high-confidence leaks in both files such as credentials, emails, and
absolute local paths. A passing result still requires manual privacy review.

To create one packet for an optional runtime adapter:

```powershell
python -m aigc_director_kit build-runtime-handoff `
  examples/skill_workflow_case.json `
  --library examples/action_library.json `
  --adapter blender-previs `
  --json
```

The packet is always a dry-run handoff: it does not launch Blender or render
media, and it keeps render/QC evidence separate from contract validation.

Prompt packs and QC evidence use separate contracts:

```powershell
python -m aigc_director_kit validate-prompt-pack `
  examples/prompt_pack_case.json `
  --plan examples/one_take_previs_case.json

python -m aigc_director_kit validate-qc-report examples/qc_report_unverified_case.json
```

Prompt validation does not generate an image or video. QC validation does not
open or interpret media; a `pass` or `fail` result requires explicitly marked
observed evidence from an available artifact.

## Contribute and report a real run

Use the [contribution guide](CONTRIBUTING.md), [Code of Conduct](CODE_OF_CONDUCT.md),
and [verified feedback template](docs/feedback-template.md). Bug reports,
feature requests, and verified run feedback use structured GitHub forms so that
environment, commands, and evidence boundaries are clear. A maintainer's
alternate account may report a real bug, but it is not independent adoption evidence.

[![CI](https://github.com/cyou1314/cinethread/actions/workflows/ci.yml/badge.svg)](https://github.com/cyou1314/cinethread/actions/workflows/ci.yml)

面向 AI 动画、AI 漫剧和分镜预演的轻量合同工具包：把镜头任务、相机路径、入/出镜状态和动作选择写成可验证、可复现的 JSON。

这是一个从真实 AIGC 导演预演工作流中抽出的公开 MVP。核心运行时只依赖 Python 标准库，不要求安装 Blender，也不会联网或触发付费生成。

## 它解决什么问题

AIGC 视频返工经常不是“不会生成”，而是镜头合同没有锁定：

- 镜头时长、帧率和相机路径不一致；
- 前一镜头的尾状态没有交给下一镜头；
- 自然语言动作请求超出动作库，却被悄悄编成了不存在的动作；
- 技术预演、正式生成和成片 QC 被混成一个结论。

本项目 v0.2 先把最稳定、最容易复用的部分做成工具：

1. `validate-plan`：校验镜头计划的结构、时长、相机关键点和预算，并提示相邻镜头的出场状态与入场状态是否需要人工确认；
2. `list-actions`：从用户自己的动作目录检索动作；
3. `compile-action`：把中英文自然语言请求编译成已知动作的确定性选择结果。

动作请求只会选择目录中已有的动作。找不到动作时返回失败，不会编造 choreography、接触、表情或镜头运动。

## 快速开始

无需安装第三方运行时。

Windows 用户也可以直接双击 [`run_examples.bat`](run_examples.bat) 查看示例结果。脚本只使用本仓库源码；如果电脑没有 Python 3.10 或更高版本，按窗口提示安装 Python 后再次双击。

命令行方式：

```powershell
python -m aigc_director_kit verify-examples --json --output cinethread-verify.json
python -m aigc_director_kit validate-plan examples/shot_plan.json
python -m aigc_director_kit list-actions --library examples/action_library.json --query 跑
python -m aigc_director_kit compile-action `
  --library examples/action_library.json `
  --text "快速跑步然后急停，过渡0.2秒，原地" `
  --output outputs/action-request.json
```

也可以安装为本地 CLI：

```powershell
python -m pip install -e .
aigc-director-kit --version
aigc-director-kit verify-examples --root . --output cinethread-verify.json
aigc-director-kit validate-plan examples/shot_plan.json
```

运行测试：

```powershell
python -m unittest discover -s tests -v
```

## 镜头计划最小示例

```json
{
  "contract": "aigc-director-shot-plan",
  "version": 1,
  "project": "lantern-bridge",
  "fps": 24,
  "resolution": {"width": 1280, "height": 720},
  "shots": [
    {
      "id": "S01",
      "duration_s": 4,
      "intent": "建立人物从暗处走向灯光的方向",
      "evidence": "designed",
      "entry_state": {"actors": ["scout"], "screen_axis": "left-to-right"},
      "exit_state": {"actors": ["scout"], "screen_axis": "left-to-right"},
      "camera": {
        "rig": "dolly",
        "job": "保持人物在前景并逐步显露桥面",
        "path": [
          {"time_s": 0, "position": [0, -4, 1.6]},
          {"time_s": 4, "position": [0, -1, 1.6]}
        ]
      },
      "next_handle": "以灯笼位于画面右侧的尾状态切入下一镜"
    }
  ]
}
```

完整示例见 [`examples/shot_plan.json`](examples/shot_plan.json)，字段说明见 [`schemas/shot-plan.v1.json`](schemas/shot-plan.v1.json)。

来自真实本地预演工作流的脱敏案例清单见 [`docs/real-workflow-evidence.md`](docs/real-workflow-evidence.md)；基础运行说明见 [`docs/sanitized-workflow-example.md`](docs/sanitized-workflow-example.md)。

## 设计边界

本仓库不包含：

- 私人角色图、参考视频、Blender `.blend` 文件或生成成片；
- 未核验可再分发许可的动捕数据；
- Blender、MCP、Seedance、Dreamina 或其他平台的账号/密钥；
- 对最终画面、动作自然度或模型服从度的保证。

计划校验通过，只代表 JSON 合同满足当前工具规则。Blender 预演、正式视频生成和成片 QC 是后续独立证据层。

## 路线图

- `0.1.x`：稳定合同、动作目录和 CLI；
- `0.2.x`：可选 Blender 适配器、镜头计划到低模场景的桥接示例；
- `0.3.x`：资产清单和跨镜头连续性报告；
- 后续：视频抽帧、Prompt 编译和更多运行时适配器，但保持核心无云、无额度依赖。

## 开源状态

当前版本是 Alpha。本项目会优先记录真实 Issue、变更、测试和使用反馈，不购买 Stars、不制造虚假 PR，也不把本地技术验证写成社区采用证据。

GitHub Actions 会在提交和 Pull Request 上用 Python 3.10–3.13 运行测试、校验公开示例并解析 JSON Schema。

## License

MIT，见 [`LICENSE`](LICENSE)。
