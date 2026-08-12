# 60 秒试用 CineThread

这是一套公开 JSON 合同和确定性干跑校验工具。它不会联网、不会调用付费模型、不会生成或渲染视频，也不会检查私人素材。

## 1. 获取仓库

在 GitHub 仓库页选择 **Code → Download ZIP**，解压后进入 `cinethread` 文件夹；也可以使用你熟悉的 Git 克隆方式。

## 2. 运行公开验证

Windows 用户可直接双击 `run_examples.bat`。脚本会检查常见 Python 安装位置，并运行全部公开示例。

在终端中，也可以运行：

```powershell
# Windows（已安装 Python Launcher）
py -3 -m aigc_director_kit verify-examples --json --output cinethread-verify.json

# macOS / Linux
python3 -m aigc_director_kit verify-examples --json --output cinethread-verify.json
```

检查成功时，报告会显示 `valid: true`，并显示 11 项公开检查全部通过。`cinethread-verify.json` 只包含相对路径、版本和通用运行环境；公开前仍请自行检查内容。

## 3. 留下真实结果

在仓库的 **Issues → New issue** 中选择 **Verified run feedback**：

- 全部通过也可以提交，它仍是有价值的真实运行记录；
- 失败或无法完成时，填写实际错误；
- 选择你与维护者的真实关系；维护者自己的其他账号不算独立采用；
- 不要附私人素材、账号、Cookie、密钥或本机绝对路径。

如果发现明确的程序错误，也可以使用 **Bug report** 表单。
