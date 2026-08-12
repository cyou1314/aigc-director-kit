# 运行反馈模板

只填写实际运行过的结果，不要为了活动申请制造反馈、Stars、Issue 或 PR。

最快方式是先在克隆或解压后的仓库目录运行：

```powershell
python -m aigc_director_kit verify-examples --json --output cinethread-verify.json
```

它会写入带版本号的报告，只输出相对路径和通用环境信息；在公开前仍请自行检查输出，删除不应公开的内容。随后在仓库的 **Issues → New issue** 中选择 **Verified run feedback**，或参考 [`docs/try-it.md`](try-it.md) 的完整步骤。

```text
版本/commit:
运行环境:
安装方式:
使用的案例或脱敏输入:
执行命令:
预期结果:
实际结果:
是否可以公开:
与仓库维护者的关系: 独立用户 / 同一维护者的另一账号 / 合作者
```

如果反馈来自维护者自己的另一个 GitHub 账号，必须标为“同一维护者的另一账号”。它可以帮助发现真实问题，但不能被描述成独立社区采用证据。
