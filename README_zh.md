# DeepTranslator

[![English](https://img.shields.io/badge/Language-English-blue)](README.md) [![中文](https://img.shields.io/badge/语言-中文-red)](README_zh.md)

基于 LangGraph 框架的高质量整书翻译系统。

## 功能特性

- 📖 支持 MD 和 EPUB 格式输入
- 🌍 多语言翻译支持 (EN↔ZH, JA, KO, DE, FR, ES, RU)
- 🔄 智能分段，保持语义完整
- ⚡ 10 路并行翻译
- ✅ 双模型审核机制
- 💾 断点续传，中断可恢复
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
  source: en    # 源语言 (en, zh, ja, ko, de, fr, es, ru)
  target: zh    # 目标语言
```

支持的语言：
- `en` - 英语 (English)
- `zh` - 中文 (Chinese)
- `ja` - 日语 (日本語)
- `ko` - 韩语 (한국어)
- `de` - 德语 (Deutsch)
- `fr` - 法语 (Français)
- `es` - 西班牙语 (Español)
- `ru` - 俄语 (Русский)

## 使用方法

```bash
# 翻译 MD 文件
python -m src.main translate book.md

# 翻译 EPUB 文件
python -m src.main translate book.epub

# 指定输出目录
python -m src.main translate book.md -o ./output/

# 从中断处继续
python -m src.main resume data/<book_id>/

# 验证输出格式
python -m src.main validate output/book_zh.md
```

## 配置说明

- `config/models.yaml`: LLM 模型配置
- `config/settings.yaml`: 翻译参数和语言设置
- `.env`: API 密钥

## 项目结构

```
deeptranslator/
├── config/          # 配置文件
├── data/            # 运行时数据 (已忽略)
├── src/             # 源代码
│   ├── nodes/       # LangGraph 节点
│   ├── prompts/     # Prompt 模板
│   └── utils/       # 工具函数
└── tests/           # 测试用例
```

## 许可证

MIT
