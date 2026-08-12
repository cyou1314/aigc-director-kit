# 真实工作流证据（脱敏）

本页记录本项目如何从一个真实的本地 AIGC 导演预演工作流中抽取公开合同案例。

重要边界：以下案例由同一维护者从本地 `DaoYan-box` forward-test 计划脱敏而来。它们证明本项目能承载真实工作流中的镜头合同，不证明外部社区采用，也不等同于独立用户反馈。

## 案例清单

| 公共案例 | 来源类型 | 关键约束 | 校验结果 |
| --- | --- | --- | --- |
| [`one_take_previs_case.json`](../examples/one_take_previs_case.json) | 本地一镜到底预演 | 4 秒、相机路径、人物移动、尾状态 | 1 镜头、96 帧、valid |
| [`film_contract_handoff_case.json`](../examples/film_contract_handoff_case.json) | 本地电影镜头合同 forward test | 横移、焦点交接、注意力顺序、右手动作尾状态 | 1 镜头、96 帧、valid |
| [`multi_actor_prop_case.json`](../examples/multi_actor_prop_case.json) | 本地双人道具交接 forward test | 互视、道具持有、接触状态、共享尾状态 | 1 镜头、120 帧、valid |
| [`shot_plan.json`](../examples/shot_plan.json) | 公开灯笼桥示例 | 两镜头交接、7 秒、168 帧 | 2 镜头、168 帧、valid |

## 可复现命令

```powershell
python -m aigc_director_kit validate-plan examples/one_take_previs_case.json --json
python -m aigc_director_kit validate-plan examples/film_contract_handoff_case.json --json
python -m aigc_director_kit validate-plan examples/multi_actor_prop_case.json --json
python -m unittest discover -s tests -v
```

## 尚未公开的部分

- Blender 场景、角色白模、参考图、`.blend` 文件和渲染视频；
- 本地动作文件、动捕原始数据和许可证材料；
- 本机绝对路径、账号信息和运行输出目录；
- 未经独立用户验证的“采用量”或“社区反馈”。

动作库中的实际动作资产仍由用户自己的运行时适配器负责。本仓库只提供无资产依赖的动作描述和确定性选择边界。
