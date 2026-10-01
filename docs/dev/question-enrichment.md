# 设计文档：真题深度标注入库（考公脑库 · 方案 A）

状态：已实现 | 日期：2026-10-01

## 背景

考公脑库（ERRRC/kaogongzhentizhengliu）的 `10-真题/` 有 11,282 篇逐题深度标注
（资料分析 3,569 + 判断推理 7,713），字段与本系统题目模型高度对应，且 qid 与
xingcezhenti 真题库同源（`bank_imports.bank_qid`）。方案 A = 把标注转成题目的
结构化字段，让资料分析/判断推理的题目详情页自带完整深度解析。

## 字段映射

| 脑库标注 | 本系统字段 | 说明 |
|----------|-----------|------|
| `**问法模型**：` | identify_signal | 题型识别信号 |
| `## 推理链` | break_logic | 分步推理链 |
| `## 最快解法` | quick_solve | 速算/秒杀技巧 |
| `## 易错点` | error_path | 常见错误路径（多条合并） |
| `## 母题抽象` + `**同类特征**：` | background_knowledge | 母题模板与特征 |
| frontmatter `考点` 末段 | sub_point | 细分考点 |
| `### 题干/选项/官方解析/给定材料` | question_raw / answer / normal_solve / ai_raw_content | 题面与解析（✅ 提取答案） |
| frontmatter 试卷/地区/年份 + 目录 | source / tags / level1~3 | level1=模块、level2=大类、level3=细分考点 |

规则：emoji 清理（⚡⚠🧩）；图片路径改写为 `/api/naoku/media?path=90-图片/...`；
**只填充空字段**（非破坏性），已有内容一律不覆盖。

## 导入策略

- `bank_imports.bank_qid` 已存在的题目：仅回填空字段（enrich）。
- 未存在的 qid：整题导入（含 BankImport 映射，保持去重体系一致）。
- 导入后 `recalc_category_counts` 全量重算；`data/kaogong-naoku` gitignore。

## 媒体服务

`GET /api/naoku/media?path=90-图片/...`：realpath 限定在脑库克隆目录内（与资料库
media 同一防护模式），供题干/解析中的公式图与题目图加载。

## 验证

1. `--limit 50` 小样本：导入/字段/图片路径改写正确。
2. 全量：统计导入/回填/跳过数；抽查图形推理题详情页图片可显示。
3. 回归：资料库、考点计数、既有题目不受影响。
