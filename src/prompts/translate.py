"""翻译 Prompt 模板 - 支持多语言"""

from ..config import config


def get_language_name(code: str) -> str:
    """获取语言显示名称，LLM 自动识别语言代码"""
    # 常见语言提供友好名称，其他直接用 ISO 代码（LLM 都认识）
    common = {
        "zh": "Chinese", "en": "English", "ja": "Japanese", "ko": "Korean",
        "de": "German", "fr": "French", "es": "Spanish", "pt": "Portuguese",
        "ru": "Russian", "it": "Italian", "ar": "Arabic", "vi": "Vietnamese",
        "th": "Thai", "id": "Indonesian", "nl": "Dutch", "pl": "Polish",
    }
    return common.get(code, code)  # 未知语言直接用代码，LLM 会识别


def get_translate_system_prompt(source_lang: str, target_lang: str) -> str:
    """生成翻译系统提示词"""
    source_name = get_language_name(source_lang)
    target_name = get_language_name(target_lang)
    
    # 如果是中文，明确要求简体中文
    if target_lang == "zh":
        target_spec = "Simplified Chinese (简体中文)"
    else:
        target_spec = target_name
    
    return f"""You are a professional {source_name} to {target_spec} translator, specializing in books and long documents.

## Core Translation Principles
1. **Fidelity**: Accurately convey the original meaning, never omit any content
2. **Fluency**: Ensure smooth, natural expression in {target_spec}
3. **Elegance**: Maintain the original style and tone
4. **Language Standard**: {"Use Simplified Chinese characters only (简体字), never use Traditional Chinese (繁体字)" if target_lang == "zh" else ""}

## Markdown Structure Preservation (Critical)

### Heading Hierarchy - Preserve exactly
- `#` → `#`, `##` → `##`, `###` → `###`, etc.
- The number of `#` symbols defines document structure, NEVER change it
- Only translate the heading text, not the Markdown syntax

### Chapter/Section Titles
- Translate according to {target_spec} conventions (e.g., "Chapter One" → localized format)
- Keep numbering style consistent throughout the entire document
- Applies to: Chapter, Part, Section, Appendix, Prologue, Epilogue, etc.

### Other Markdown Elements
- List markers (`-`, `*`, `1.`) → preserve
- **Bold**, *italic* → preserve
- Images `![alt](url)` → preserve exactly, do not translate alt text
- Code blocks → do not translate
- Blockquotes (`>`) → preserve
- Links → translate text only, keep URLs unchanged

## Output Requirements
- Output translation directly, no explanations
- Paragraph order must match the original exactly"""


def get_translate_user_prompt(content: str, source_lang: str, target_lang: str) -> str:
    """生成翻译用户提示词"""
    source_name = get_language_name(source_lang)
    target_name = get_language_name(target_lang)
    
    # 如果是中文，明确要求简体中文
    if target_lang == "zh":
        target_spec = "Simplified Chinese (简体中文)"
        lang_note = "\nIMPORTANT: Use Simplified Chinese characters only. Do not use Traditional Chinese."
    else:
        target_spec = target_name
        lang_note = ""
    
    return f"""Translate the following {source_name} content into {target_spec}.{lang_note}

Critical: Preserve all Markdown heading levels (# ## ###) exactly as-is.

---

{content}

---

Translation:"""


def get_translate_prompt(content: str) -> tuple[str, str]:
    """获取翻译 Prompt
    
    Returns:
        (system_prompt, user_prompt)
    """
    source_lang = config.source_language
    target_lang = config.target_language
    
    system_prompt = get_translate_system_prompt(source_lang, target_lang)
    user_prompt = get_translate_user_prompt(content, source_lang, target_lang)
    
    return system_prompt, user_prompt
