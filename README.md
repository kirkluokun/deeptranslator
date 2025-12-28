# DeepTranslator

[![English](https://img.shields.io/badge/Language-English-blue)](README.md) [![中文](https://img.shields.io/badge/语言-中文-red)](README_zh.md)

A high-quality book translation system powered by LangGraph framework.

## Features

- 📖 Support MD and EPUB input formats
- 🌍 Multi-language translation (EN↔ZH, JA, KO, DE, FR, ES, RU)
- 🔄 Smart segmentation with semantic integrity
- ⚡ 10-way parallel translation
- ✅ Dual-model review mechanism
- 💾 Checkpoint & resume support
- 🎯 High-fidelity translation quality

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API Key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Translate a book
python -m src.main translate your_book.md
```

## Language Configuration

Edit `config/settings.yaml` to set source and target languages:

```yaml
language:
  source: en    # Source language (en, zh, ja, ko, de, fr, es, ru)
  target: zh    # Target language
```

Supported languages:
- `en` - English
- `zh` - Chinese (中文)
- `ja` - Japanese (日本語)
- `ko` - Korean (한국어)
- `de` - German (Deutsch)
- `fr` - French (Français)
- `es` - Spanish (Español)
- `ru` - Russian (Русский)

## Usage

```bash
# Translate MD file
python -m src.main translate book.md

# Translate EPUB file
python -m src.main translate book.epub

# Specify output directory
python -m src.main translate book.md -o ./output/

# Resume from checkpoint
python -m src.main resume data/<book_id>/

# Validate output format
python -m src.main validate output/book_zh.md
```

## Configuration

- `config/models.yaml`: LLM model configuration
- `config/settings.yaml`: Translation parameters & language settings
- `.env`: API keys

## Project Structure

```
deeptranslator/
├── config/          # Configuration files
├── data/            # Runtime data (gitignored)
├── src/             # Source code
│   ├── nodes/       # LangGraph nodes
│   ├── prompts/     # Prompt templates
│   └── utils/       # Utility functions
└── tests/           # Test cases
```

## License

MIT
