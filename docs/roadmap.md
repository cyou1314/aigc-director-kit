# CineThread roadmap

## v0.2 implementation status

- [x] Workflow, prompt-pack, and QC evidence contracts are available as
  standard-library-only validators.
- [x] A runtime adapter dry-run handoff can combine the validated plan and
  compiled action requests without launching Blender.
- [x] A metadata-only local Skill adapter can document public integration
  contracts without publishing local implementation details.
- [x] Adapter/workflow cross-validation checks stage ownership, output and
  evidence compatibility, action-producer routing, and high-confidence leaks.
- [x] The Windows example launcher accepts `AIGC_DIRECTOR_PYTHON` and checks
  common Python install locations.
- [ ] Add an optional Blender adapter that consumes the handoff and records
  real previs evidence.
- [ ] Add field-level error codes and keep the JSON output stable across
  releases.

## v0.1 — 当前范围

- [x] 镜头计划合同和确定性校验
- [x] 相邻镜头 entry/exit 状态提示
- [x] 动作目录格式和检索
- [x] 中文/英文动作请求编译
- [x] 无第三方运行时依赖

## v0.2 — 部分完成，等待真实运行时反馈

- [x] 可选运行时 dry-run 交接包，不把 Blender 加入核心依赖
- [ ] 可选 Blender 适配器，消费交接包并记录真实预演证据
- [ ] 更明确的字段级错误码和 JSON 输出稳定性

## v0.3 — 暂不承诺

- [ ] 资产清单和跨镜头连续性报告
- [ ] Prompt 编译器
- [ ] 视频抽帧和音频接口

每个路线图项目都要先有真实 Issue 或使用反馈；不为制造活动材料而虚构功能。
