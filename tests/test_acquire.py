"""测试 acquire 模块"""

import pytest
from pathlib import Path

from src.utils.markdown_cleaner import clean_markdown, count_words, extract_title


class TestMarkdownCleaner:
    """测试 Markdown 清洗功能"""
    
    def test_clean_images(self):
        """测试图片引用清除"""
        content = "Some text ![alt](image.png) more text"
        result = clean_markdown(content)
        assert "![alt]" not in result
        assert "image.png" not in result
        assert "Some text" in result
        assert "more text" in result
    
    def test_clean_img_tags(self):
        """测试 img 标签清除"""
        content = 'Text <img src="test.jpg"/> more'
        result = clean_markdown(content)
        assert "<img" not in result
        assert "Text" in result
    
    def test_clean_multiple_newlines(self):
        """测试多余空行压缩"""
        content = "Line1\n\n\n\n\nLine2"
        result = clean_markdown(content)
        assert result == "Line1\n\nLine2"
    
    def test_count_words(self):
        """测试单词计数"""
        text = "Hello world, this is a test!"
        count = count_words(text)
        assert count == 6
    
    def test_extract_title_h1(self):
        """测试 H1 标题提取"""
        content = "# My Title\n\nSome content"
        title = extract_title(content)
        assert title == "My Title"
    
    def test_extract_title_fallback(self):
        """测试无标题时的回退"""
        content = "Just some text without a title"
        title = extract_title(content)
        assert title is not None
        assert len(title) <= 53  # 50 + "..."


class TestAcquireNode:
    """测试 acquire 节点"""
    
    def test_generate_book_id(self):
        """测试书籍 ID 生成"""
        from src.nodes.acquire import generate_book_id
        
        id1 = generate_book_id("/path/to/book.md")
        id2 = generate_book_id("/path/to/book.md")
        id3 = generate_book_id("/different/book.epub")
        
        assert id1 == id2  # 相同路径应该生成相同 ID
        assert id1 != id3  # 不同路径应该生成不同 ID
        assert len(id1) == 8  # ID 应该是 8 字符
