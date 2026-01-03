# DeepTranslator

[![English](https://img.shields.io/badge/Language-English-blue)](README.md) [![中文](https://img.shields.io/badge/语言-中文-red)](README_zh.md)

A high-quality book translation system powered by LangGraph framework.

## Features

- 📖 Support MD and EPUB input formats
- 🌍 Multi-language translation (EN↔ZH, JA, KO, DE, FR, ES, RU, VI, TH, ID...)
- 🔄 Smart segmentation with semantic integrity
- ⚡ 10-way parallel translation
- 🔍 **Auto quality check** - Detects untranslated content and auto-retries
- 💾 Checkpoint & resume support
- 📁 **Output to source directory** - Translation saved alongside original file
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
  source: vi    # Source language (any ISO 639-1 code)
  target: zh    # Target language
```

Supported languages (examples):
- `en` - English
- `zh` - Chinese (中文)
- `ja` - Japanese (日本語)
- `ko` - Korean (한국어)
- `vi` - Vietnamese (Tiếng Việt)
- `de` - German (Deutsch)
- `fr` - French (Français)
- `es` - Spanish (Español)
- `ru` - Russian (Русский)
- Any ISO 639-1 language code

## Usage

### Basic Commands

```bash
# Translate MD file
python -m src.main translate book.md

# Translate EPUB file
python -m src.main translate book.epub

# Resume from checkpoint
python -m src.main resume data/<book_id>/

# Validate output format
python -m src.main validate output/book_zh.md
```

### Tool Scripts

```bash
# Re-translate specific segments (for failed segments)
python -m src.tools.retranslate_segments <book_id> <segment_id1> [segment_id2] ...

# Merge all translated segments
python -m src.tools.merge_translations <book_id>
```

## Output Location

**Default**: Translation is saved to the same directory as the input file.

- Input: `/path/to/book.md`
- Output: `/path/to/book_zh.md`

A backup copy is also saved in `data/<book_id>/output/`.

## Translation Quality Check

The system automatically:

1. **Detects source language residue** - Flags translations with >30% source language characters
2. **Verifies target language ratio** - Ensures sufficient target language content
3. **Auto-retries failed segments** - Up to 3 rounds of retry for quality issues
4. **Reports failures** - Lists segments needing manual attention

## Configuration

- `config/models.yaml`: LLM model configuration
- `config/settings.yaml`: Translation parameters & language settings
- `.env`: API keys

### settings.yaml Options

```yaml
language:
  source: en
  target: zh

translation:
  segment_chars: 5000      # Target chars per segment
  parallel_workers: 10     # Parallel translation workers
  max_review_rounds: 1     # Review rounds (0 to disable)
  enable_review: false     # Enable review stage

retry:
  max_attempts: 3          # Max retry per segment
  backoff_base: 2
  backoff_max: 60

checkpoint:
  enabled: true
```

## Project Structure

```
deeptranslator/
├── config/              # Configuration files
├── data/                # Runtime data (gitignored)
├── src/                 # Source code
│   ├── nodes/           # LangGraph nodes
│   │   ├── acquire.py   # Document loading
│   │   ├── prepare.py   # Segmentation
│   │   ├── translate.py # Translation + quality check
│   │   ├── review.py    # Optional review
│   │   ├── parse.py     # Format validation
│   │   └── render.py    # Output merging
│   ├── prompts/         # Prompt templates
│   ├── tools/           # Utility scripts
│   │   ├── merge_translations.py
│   │   └── retranslate_segments.py
│   └── utils/           # Helper functions
└── tests/               # Test cases
```

## Workflow

```
Input File
    ↓
[Acquire] → Load & clean document
    ↓
[Prepare] → Smart segmentation (~5000 chars each)
    ↓
[Translate] → Parallel translation with quality check
    ↓           ↑ Auto-retry if quality fails
    ↓
[Parse] → Validate Markdown format
    ↓
[Render] → Merge & output to source directory
    ↓
Output File (same directory as input)
```

## License

MIT
