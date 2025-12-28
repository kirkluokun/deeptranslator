"""Markdown 清洗工具"""

import re
from pathlib import Path


def clean_pandoc_artifacts(content: str) -> str:
    """清理 Pandoc 转换产生的特定伪影"""
    # 1. 清理锚点: []{...} (内容为空的带属性括号)
    content = re.sub(r'\[\]\{.*?\}', '', content)
    
    # 2. 清理带属性的 Span，保留内容: [内容]{.属性} -> 内容
    # 循环多次以处理嵌套情况
    for _ in range(3):
        content = re.sub(r'\[([^\]]+)\]\{[^\}]+\}', r'\1', content)
    
    # 3. 清理行尾或块级属性: { .属性 } 或 { #id }
    content = re.sub(r'\{[.#][^}]*\}', '', content)
    
    # 4. 清理容器围栏: ::: 或 :::::: 及其属性
    content = re.sub(r'^\s*:::+.*$', '', content, flags=re.MULTILINE)
    
    # 5. 清理特定的导航链接: [Skip Notes](#...)
    content = re.sub(r'\[Skip Notes\]\(#[^\)]*\)', '', content, flags=re.IGNORECASE)
    
    # 6. 清理可能残余的空方括号
    content = re.sub(r'\[\]', '', content)
    
    # 7. 清理内部链接 (通常指向电子书内部锚点): [内容](#锚点) -> 内容
    # 这包括脚注引用 [\[\*1\]](#...)
    # 使用 [((?:\\\]|[^\]])+)\] 来正确处理括号内的转义括号
    content = re.sub(r'\[((?:\\\]|[^\]])+)\]\(#[^\)]*\)', r'\1', content)

    # 8. 清理特定的常见脚注标记，如 [\[\*1\]] 或类似的纯数字/星号引用
    # 这些通常在上一步被 stripped 成了 link text，例如 [\[\*1\]]
    content = re.sub(r'\[\s*\\?\[\s*[\*0-9]+\s*\\?\]\s*\]', '', content)
    
    # 9. 清理 HTML 标签 remnants (figure, figcaption, div)
    # 移除 figure 和 div 标签，保留内容
    content = re.sub(r'</?(figure|div)[^>]*>', '', content, flags=re.IGNORECASE)
    # 处理 figcaption: 移除标签，内容可能包含 <p>
    content = re.sub(r'</?figcaption[^>]*>', '', content, flags=re.IGNORECASE)
    
    # 10. 处理 HTML 段落标签 <p>
    content = re.sub(r'<p[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</p>', '\n', content, flags=re.IGNORECASE)

    # 11. 清理单独成行的 URL 链接 (通常是引用来源)
    # 格式: [https://...](https://...)
    # 确保不删除包含描述性文字的链接，只删除文本和链接相同的及其变体
    content = re.sub(r'^\s*\[https?://[^\]]+\]\(https?://[^\)]+\)\s*$', '', content, flags=re.MULTILINE)

    # 12. 清理 HTML 形式的脚注引用 <a ...>[*1]</a>
    # 使用 \s* 来匹配 <a 后的空白（包括换行符），并开启 DOTALL
    content = re.sub(r'<a\s+[^>]*class="[^"]*footnote[^"]*"[^>]*>.*?</a>', '', content, flags=re.IGNORECASE | re.DOTALL)
    # 补充清理: 任何包含 [*n] 的 a 标签
    content = re.sub(r'<a\s+[^>]*>\[\s*[\*0-9]+\s*\]</a>', '', content, flags=re.IGNORECASE | re.DOTALL)

    # 13. 转换常见行内 HTML 标签为 Markdown
    # <em>, <i> -> *
    content = re.sub(r'</?(em|i)[^>]*>', '*', content, flags=re.IGNORECASE)
    # <b>, <strong> -> **
    content = re.sub(r'</?(b|strong)[^>]*>', '**', content, flags=re.IGNORECASE)

    # 14. 清理 "Figure N" 这种单纯的图片编号行
    # 匹配独立的一行 Figure 1, Figure 12 等
    # 确保 Figure 前后没有其他文字，只有空白
    content = re.sub(r'^\s*Figure\s+\d+\s*$', '', content, flags=re.MULTILINE | re.IGNORECASE)
    
    return content


def clean_markdown(content: str) -> str:
    """清洗 Markdown 内容
    
    清洗规则:
    - 去除图片引用 ![...](...) 和 <img> 标签
    - 清理 Pandoc/EPUB 特定伪影 (锚点、围栏、属性)
    - 去除多余空行
    - 去除特殊控制字符
    - 统一换行符
    
    Args:
        content: 原始 Markdown 内容
    
    Returns:
        清洗后的内容
    """
    # 统一换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 去除图片引用 ![alt](url) 或 ![alt][ref]
    content = re.sub(r'!\[([^\]]*)\]\([^)]*\)', '', content)
    content = re.sub(r'!\[([^\]]*)\]\[[^\]]*\]', '', content)
    
    # 去除 <img> 标签
    content = re.sub(r'<img[^>]*/?>', '', content, flags=re.IGNORECASE)
    
    # 清理 Pandoc 伪影
    content = clean_pandoc_artifacts(content)
    
    # 去除 HTML 注释
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # 去除特殊 Unicode 控制字符，但保留常见符号
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
    
    # 去除 零宽字符
    content = re.sub(r'[\u200b-\u200d\ufeff]', '', content)
    
    # 压缩多余空行（3个以上变成2个）
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 去除行尾空格
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    
    # 去除首尾空白
    content = content.strip()
    
    return content


def load_markdown_file(filepath: str | Path) -> str:
    """加载并清洗 Markdown 文件
    
    Args:
        filepath: 文件路径
    
    Returns:
        清洗后的内容
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return clean_markdown(content)


def count_words(text: str) -> int:
    """统计英文单词数量
    
    简单的单词计数，按空格分割
    
    Args:
        text: 文本内容
    
    Returns:
        单词数量
    """
    # 只统计字母数字组成的单词
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text)
    return len(words)


def extract_title(content: str) -> str | None:
    """从 Markdown 内容提取标题
    
    优先从 H1 标题提取，否则取前 50 个字符
    
    Args:
        content: Markdown 内容
    
    Returns:
        标题或 None
    """
    # 尝试匹配 H1 标题
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    # 取第一行非空文本
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            return line[:50] + ('...' if len(line) > 50 else '')
    
    return None
