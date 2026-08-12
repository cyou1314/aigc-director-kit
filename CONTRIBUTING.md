# Contributing

感谢参与。这个项目优先解决 AIGC 分镜生产中的可复现合同、动作选择和交接问题。

## 开始

```powershell
python -m unittest discover -s tests -v
python -m aigc_director_kit validate-plan examples/shot_plan.json
python -m aigc_director_kit list-actions --library examples/action_library.json --query 跑
```

## 提交变更

- 一个 Pull Request 只解决一个明确问题。
- 新增合同字段时，同时更新代码、schema、示例和测试。
- 如果引入外部动作、模型或素材，必须先说明来源、许可证和可再分发边界。
- 不提交生成视频、私人参考图、账号信息或本地机器路径。
- 任何“看起来能用”的提示词规则，都要区分设计假设和真实生成/QC 证据。
- 反馈必须来自真实运行，并如实标注反馈者与维护者的关系；维护者的另一个账号不算独立社区采用证据。
