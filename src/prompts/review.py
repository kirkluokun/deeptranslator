"""审核 Prompt 模板 - 支持多语言"""

from ..config import config
from .translate import get_language_name


def get_review_system_prompt(source_lang: str, target_lang: str) -> str:
    """生成审核系统提示词"""
    source_name = get_language_name(source_lang)
    target_name = get_language_name(target_lang)
    
    return f"""You are a senior translation review expert, responsible for comparing {source_name} original text with {target_name} translations.

## Review Dimensions (by priority)

### 1. Format Preservation Review (Highest Priority)
- Check heading levels: Does the number of `#` match between original and translation?
- Check chapter numbering: Is numbering consistent in {target_name}?
- Check lists, blockquotes, and horizontal rules are preserved

### 2. Completeness Review
- Is any content from the original missing in the translation?
- Is paragraph order consistent with the original?
- Are there any untranslated sentences or paragraphs?

### 3. Accuracy Review
- Are there translation errors or misunderstandings?
- Are proper nouns, numbers, and dates accurate?

### 4. Fluency Review
- Is the translation smooth and natural?
- Does it follow {target_name} expression conventions?

## Key Checkpoints
- Each `#` in original must correspond to a `#` in translation
- Each `##` in original must correspond to a `##` in translation
- Code blocks, links, and special formatting must remain unchanged"""


def get_review_user_prompt(original: str, translation: str, source_lang: str, target_lang: str) -> str:
    """生成审核用户提示词"""
    source_name = get_language_name(source_lang)
    target_name = get_language_name(target_lang)
    
    return f"""Please compare the following {source_name} original and {target_name} translation for quality review.

## Original
{original}

## Translation
{translation}

---

**Key Checks**:
1. Are Markdown headings (# ## ###) fully preserved?
2. Is chapter/part numbering consistent?
3. Is any content missing?
4. Is paragraph order correct?

**Review Requirements**:
1. If the translation has no issues, simply reply: APPROVED
2. If issues are found, list them as:
   - [Issue Type]: [Description] → [Suggested Fix]
3. If there are issues, provide the corrected full translation at the end

Please begin review:"""


def get_review_prompt(original: str, translation: str) -> tuple[str, str]:
    """获取审核 Prompt
    
    Returns:
        (system_prompt, user_prompt)
    """
    source_lang = config.source_language
    target_lang = config.target_language
    
    system_prompt = get_review_system_prompt(source_lang, target_lang)
    user_prompt = get_review_user_prompt(original, translation, source_lang, target_lang)
    
    return system_prompt, user_prompt


def parse_review_response(response: str) -> tuple[bool, str | None, list[str]]:
    """解析审核响应
    
    Args:
        response: LLM 响应
    
    Returns:
        (is_approved, corrected_translation, issues)
    """
    response = response.strip()
    
    # 检查是否通过
    if response.upper().startswith("APPROVED"):
        return True, None, []
    
    # 解析问题和修正
    lines = response.split('\n')
    issues = []
    corrected_start = -1
    
    for i, line in enumerate(lines):
        line = line.strip()
        # 收集问题
        if line.startswith('- [') and ']:' in line:
            issues.append(line)
        # 找到修正译文的开始
        if '修正' in line or '修改后' in line or '完整译文' in line or 'corrected' in line.lower():
            corrected_start = i + 1
            break
    
    # 提取修正后的译文
    corrected = None
    if corrected_start > 0 and corrected_start < len(lines):
        corrected_lines = lines[corrected_start:]
        corrected = '\n'.join(corrected_lines).strip()
        if corrected:
            # 移除可能的 markdown 代码块标记
            if corrected.startswith('```'):
                corrected = '\n'.join(corrected.split('\n')[1:])
            if corrected.endswith('```'):
                corrected = '\n'.join(corrected.split('\n')[:-1])
    
    return False, corrected or None, issues
