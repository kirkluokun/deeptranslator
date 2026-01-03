# DeepTranslator

[![English](https://img.shields.io/badge/Language-English-blue)](README.md) [![中文](https://img.shields.io/badge/语言-中文-red)](README_zh.md)

基于 LangGraph 框架的高质量整书翻译系统。

## 功能特性

- 📖 支持 MD 和 EPUB 格式输入
- 🌍 多语言翻译支持 (EN↔ZH, JA, KO, DE, FR, ES, RU, VI, TH, ID...)
- 🔄 智能分段，保持语义完整
- ⚡ 10 路并行翻译
- 🔍 **自动质量检测** - 检测未翻译内容，自动重试
- 💾 断点续传，中断可恢复
- 📁 **输出到源目录** - 翻译结果保存在原文件同目录
- 🎯 信达雅的翻译质量

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env 填入 GEMINI_API_KEY

# 翻译书籍
python -m src.main translate your_book.md
```

## 语言配置

编辑 `config/settings.yaml` 设置源语言和目标语言：

```yaml
language:
  source: vi    # 源语言 (任意 ISO 639-1 代码)
  target: zh    # 目标语言
```

支持的语言（示例）：
- `en` - 英语 (English)
- `zh` - 中文 (Chinese)
- `ja` - 日语 (日本語)
- `ko` - 韩语 (한국어)
- `vi` - 越南语 (Tiếng Việt)
- `de` - 德语 (Deutsch)
- `fr` - 法语 (Français)
- `es` - 西班牙语 (Español)
- `ru` - 俄语 (Русский)
- 任意 ISO 639-1 语言代码

## 使用方法

### 基本命令

```bash
# 翻译 MD 文件
python -m src.main translate book.md

# 翻译 EPUB 文件
python -m src.main translate book.epub

# 从中断处继续
python -m src.main resume data/<book_id>/

# 验证输出格式
python -m src.main validate output/book_zh.md
```

### 工具脚本

```bash
# 重新翻译指定段落（针对失败段落）
python -m src.tools.retranslate_segments <book_id> <segment_id1> [segment_id2] ...

# 合并所有翻译段落
python -m src.tools.merge_translations <book_id>
```

## 输出位置

**默认**：翻译结果保存到输入文件的同目录。

- 输入：`/path/to/book.md`
- 输出：`/path/to/book_zh.md`

同时在 `data/<book_id>/output/` 保存一份备份。

## 翻译质量检测

系统自动执行：

1. **检测源语言残留** - 标记源语言字符超过 30% 的翻译
2. **验证目标语言比例** - 确保目标语言内容充足
3. **自动重试失败段落** - 最多 3 轮重试
4. **报告失败** - 列出需要人工处理的段落

## 配置说明

- `config/models.yaml`: LLM 模型配置
- `config/settings.yaml`: 翻译参数和语言设置
- `.env`: API 密钥

### settings.yaml 选项

```yaml
language:
  source: en
  target: zh

translation:
  segment_chars: 5000      # 每段目标字符数
  parallel_workers: 10     # 并行翻译数
  max_review_rounds: 1     # 审核轮次 (0 禁用)
  enable_review: false     # 启用审核阶段

retry:
  max_attempts: 3          # 每段最大重试次数
  backoff_base: 2
  backoff_max: 60

checkpoint:
  enabled: true
```

## 项目结构

```
deeptranslator/
├── config/              # 配置文件
├── data/                # 运行时数据 (已忽略)
├── src/                 # 源代码
│   ├── nodes/           # LangGraph 节点
│   │   ├── acquire.py   # 文档加载
│   │   ├── prepare.py   # 智能分段
│   │   ├── translate.py # 翻译 + 质量检测
│   │   ├── review.py    # 可选审核
│   │   ├── parse.py     # 格式验证
│   │   └── render.py    # 合并输出
│   ├── prompts/         # Prompt 模板
│   ├── tools/           # 工具脚本
│   │   ├── merge_translations.py
│   │   └── retranslate_segments.py
│   └── utils/           # 辅助函数
└── tests/               # 测试用例
```

## 工作流程

```
输入文件
    ↓
[Acquire] → 加载并清洗文档
    ↓
[Prepare] → 智能分段 (每段约 5000 字符)
    ↓
[Translate] → 并行翻译 + 质量检测
    ↓           ↑ 质量不合格自动重试
    ↓
[Parse] → 验证 Markdown 格式
    ↓
[Render] → 合并输出到源目录
    ↓
输出文件 (与输入文件同目录)
```

## 许可证

MIT
