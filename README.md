# 产品拆解总结 Word 与 HTML

以产品经理与 PRD 视角为主，从一个核心场景和最终交付出发，生成内容一致的可编辑 Word（.docx）和可离线阅读的 HTML。

## 分析主线

产品与主场景 → 场景体验及交付判断 → 围绕同一任务的关键机制深拆 → 整体架构与关键结论。

- 主线深拆：决定任务成败的流程、规则、人机协作、修改与恢复。
- 支撑简述：用于解释主线的市场、商业、竞品、端形态和成本。
- 附录备查：完整模块、字段、权限、详细证据与次要问题。

重要性与确定性分开：核心未知仍在正文突出；事实、推断和建议分别标记。评分、模型和后台实现需证据，不照搬案例结论。

## 安装与使用

将本仓库的 `product-teardown/` 文件夹复制到个人 Skills 目录 `~/.codex/skills/`，或目标项目的 `.agents/skills/` 下。更新已有版本前先备份。调用名称仍为 `$product-teardown`。

```text
$product-teardown 拆解这个产品：<产品链接>
```

可指定主场景、重点或全量范围。默认输出同名的 `.docx` 与 `.html` 两个文件；用户明确要求其他格式时遵循。

入口与规范见 [SKILL.md](product-teardown/SKILL.md)、[主次框架](product-teardown/references/framework.md)、[双文件规范](product-teardown/references/document-output.md)。

## 工具与验证

HTML 渲染与双文件检查脚本使用 Python 标准库。Word 的创建与视觉检查按输出规范使用可用文档工具，基础结构检查不替代排版与内容核验。

```sh
python3 -m unittest discover -s product-teardown/tests -v
python3 product-teardown/scripts/check_deliverables.py <报告.docx> <报告.html>
```

现有 9 项脚本测试检查文件生成、伪 DOCX、证据编号、资源引用及覆盖保护；[人工验收场景](product-teardown/tests/scenarios.md)用于后续真实产品试用，不是自动行为测试。

本仓库包含 Skill 指令、模板和工具，不是独立运行的网站。使用时默认本地交付，不自动公开产品报告、账号或项目材料。
