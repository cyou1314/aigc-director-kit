# 脱敏工作流案例：锁定镜头交接和动作选择

> 本案例抽象自真实 AIGC 导演预演中的合同约束，只保留可公开的 JSON、动作目录和校验结果。角色图、参考视频、Blender 工程、成片和账号信息均不在仓库中。本案例不宣称外部社区已经采用本项目。

## 场景

一个 7 秒、24 fps、1280×720 的两镜头片段：

- S01 用 4 秒建立人物、灯笼和桥面的关系；
- S02 用 3 秒继续同一屏幕轴线；
- S01 的尾状态通过 `next_handle` 交给 S02 的 `entry_state`；
- 动作请求只能从提供的动作目录中选择。

对应文件是 [`examples/shot_plan.json`](../examples/shot_plan.json) 和 [`examples/action_library.json`](../examples/action_library.json)。

## 1. 先校验镜头合同

```powershell
python -m aigc_director_kit validate-plan examples/shot_plan.json --json
```

关键结果：

```json
{
  "valid": true,
  "summary": {
    "shot_count": 2,
    "shot_ids": ["S01", "S02"],
    "total_duration_s": 7.0,
    "total_frames": 168,
    "fps": 24
  }
}
```

如果把 S02 的 `entry_state.screen_axis` 改成与 S01 不同，校验仍会保留结构有效，但会输出 `S01 -> S02` 的交接警告。这样“需要人工确认”不会被误报成“工具已经修好了连续性”。

## 2. 编译一个有边界的动作请求

```powershell
python -m aigc_director_kit compile-action `
  --library examples/action_library.json `
  --text "快速跑步然后急停，过渡0.2秒，原地"
```

当前目录会匹配 `run_quick_stop`，并保留 `0.2` 秒过渡、原地和速度修饰信息。运行时适配器仍需自行把动作 ID 映射到实际资产。

## 3. 未知动作明确失败

```powershell
python -m aigc_director_kit compile-action `
  --library examples/action_library.json `
  --text "后空翻接地滚"
```

结果为 `valid: false`，并说明没有匹配到支持的动作。工具不会把未提供的动作偷偷编成 choreography、接触或镜头运动。

## 这个案例证明什么

- 证明当前版本的合同、示例和 CLI 可以被复现运行；
- 证明镜头交接和动作选择是可检查的中间证据层；
- 不证明最终视频质量、动作自然度、模型服从度或社区采用情况。
