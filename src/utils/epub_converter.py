"""EPUB 转 MD 工具"""

import re
from pathlib import Path

try:
    from ebooklib import epub
    import html2text
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False


def convert_epub_to_markdown(epub_path: str | Path) -> str:
    """将 EPUB 文件转换为 Markdown 文本
    
    Args:
        epub_path: EPUB 文件路径
    
    Returns:
        Markdown 格式的文本内容
    """
    if not EPUB_AVAILABLE:
        raise ImportError("请安装 ebooklib 和 html2text: pip install ebooklib html2text")
    
    epub_path = Path(epub_path)
    if not epub_path.exists():
        raise FileNotFoundError(f"文件不存在: {epub_path}")
    
    book = epub.read_epub(str(epub_path))
    
    # 配置 html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True  # 忽略图片
    h.ignore_emphasis = False
    h.body_width = 0  # 不限制行宽
    
    markdown_parts = []
    
    # 遍历所有文档项
    for item in book.get_items():
        if item.get_type() == epub.ITEM_DOCUMENT:
            html_content = item.get_content().decode('utf-8', errors='ignore')
            md_content = h.handle(html_content)
            
            # 清理过度的空行
            md_content = re.sub(r'\n{3,}', '\n\n', md_content)
            
            if md_content.strip():
                markdown_parts.append(md_content.strip())
    
    return '\n\n---\n\n'.join(markdown_parts)


def get_epub_metadata(epub_path: str | Path) -> dict:
    """获取 EPUB 元数据
    
    Args:
        epub_path: EPUB 文件路径
    
    Returns:
        元数据字典
    """
    if not EPUB_AVAILABLE:
        raise ImportError("请安装 ebooklib: pip install ebooklib")
    
    book = epub.read_epub(str(epub_path))
    
    def get_meta(name: str) -> str | None:
        meta = book.get_metadata('DC', name)
        return meta[0][0] if meta else None
    
    return {
        'title': get_meta('title'),
        'author': get_meta('creator'),
        'language': get_meta('language'),
        'publisher': get_meta('publisher'),
        'date': get_meta('date'),
    }
