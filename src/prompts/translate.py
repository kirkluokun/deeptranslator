"""翻译 Prompt 模板 - 支持多语言"""

from ..config import config

# 语言名称映射
LANGUAGE_NAMES = {
    "en": {"en": "English", "zh": "英语", "native": "English"},
    "zh": {"en": "Chinese", "zh": "中文", "native": "中文"},
    "ja": {"en": "Japanese", "zh": "日语", "native": "日本語"},
    "ko": {"en": "Korean", "zh": "韩语", "native": "한국어"},
    "de": {"en": "German", "zh": "德语", "native": "Deutsch"},
    "fr": {"en": "French", "zh": "法语", "native": "Français"},
    "es": {"en": "Spanish", "zh": "西班牙语", "native": "Español"},
    "ru": {"en": "Russian", "zh": "俄语", "native": "Русский"},
}

# 章节翻译映射
CHAPTER_TRANSLATIONS = {
    "zh": {
        "chapter": "第{}章",
        "part": "第{}部分",
        "numbers": ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"],
    },
    "ja": {
        "chapter": "第{}章",
        "part": "第{}部",
        "numbers": ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"],
    },
    "ko": {
        "chapter": "제{}장",
        "part": "제{}부",
        "numbers": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"],
    },
    "en": {
        "chapter": "Chapter {}",
        "part": "Part {}",
        "numbers": ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                    "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty"],
    },
}


def get_language_name(code: str, display_lang: str = "native") -> str:
    """获取语言显示名称"""
    return LANGUAGE_NAMES.get(code, {}).get(display_lang, code)


def get_translate_system_prompt(source_lang: str, target_lang: str) -> str:
    """生成翻译系统提示词"""
    source_name = get_language_name(source_lang, "native")
    target_name = get_language_name(target_lang, "native")
    
    # 章节翻译规则
    chapter_rules = ""
    if target_lang in CHAPTER_TRANSLATIONS:
        ch = CHAPTER_TRANSLATIONS[target_lang]
        examples = []
        for i, num_word in enumerate(["One", "Two", "Three"], 1):
            if i <= len(ch["numbers"]):
                examples.append(f'"Chapter {num_word}" / "Chapter {i}" → "{ch["chapter"].format(ch["numbers"][i-1])}"')
        chapter_rules = "\n".join([f"- {ex}" for ex in examples])
        chapter_rules += f'\n- "Part I" → "{ch["part"].format(ch["numbers"][0])}"'
        chapter_rules += f'\n- "Part II" → "{ch["part"].format(ch["numbers"][1])}"'
    
    return f"""You are a professional {source_name} to {target_name} translator, specializing in books and long documents.

## Core Translation Principles
1. **Fidelity**: Accurately convey the original meaning, never omit any content
2. **Fluency**: Ensure smooth, natural expression in {target_name}
3. **Elegance**: Maintain the original style and tone

## Format Preservation Requirements (Critical)

### Heading Format - Must preserve 100%
- `#` in original must remain as `#` (H1)
- `##` in original must remain as `##` (H2)  
- `###` in original must remain as `###` (H3)
- The number of `#` symbols must match exactly
- Preserve blank lines before and after headings

### Chapter/Part Numbering - Must be consistent
{chapter_rules}
- Maintain consistent numbering throughout the book

### Other Format Requirements
1. List markers (`-`, `*`, `1.`) must be preserved
2. **Bold** and *italic* must be preserved
3. Code blocks remain unchanged, do not translate
4. Blockquotes (`>`) must be preserved
5. Horizontal rules (`---`) must be preserved
6. Link text can be translated, URLs stay unchanged

## Output Requirements
- Output translation directly, no explanations or comments
- Ensure output can seamlessly connect with other sections
- Paragraph order must match the original exactly"""


def get_translate_user_prompt(content: str, source_lang: str, target_lang: str) -> str:
    """生成翻译用户提示词"""
    source_name = get_language_name(source_lang, "native")
    target_name = get_language_name(target_lang, "native")
    
    return f"""Please translate the following {source_name} content into {target_name}.

**Important Reminders**:
1. All Markdown headings (# ## ###) must be preserved exactly, only translate the heading text
2. Use consistent chapter/part numbering in {target_name}
3. Do not omit any content, do not change paragraph order

---

{content}

---

Please output the translation directly:"""


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
