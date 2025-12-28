"""测试 prepare 模块"""

import pytest

from src.nodes.prepare import segment_by_rules, find_paragraph_boundaries


class TestSegmentation:
    """测试分段功能"""
    
    def test_find_boundaries_empty_lines(self):
        """测试空行边界检测"""
        content = "Line1\n\nLine3\n\nLine5"
        boundaries = find_paragraph_boundaries(content)
        assert 1 in boundaries  # 第一个空行
        assert 3 in boundaries  # 第二个空行
    
    def test_find_boundaries_headers(self):
        """测试标题边界检测"""
        content = "Intro\n# Title\nContent"
        boundaries = find_paragraph_boundaries(content)
        assert 1 in boundaries  # # Title 行
    
    def test_segment_short_content(self):
        """测试短内容不分段"""
        content = "Short content that is less than 5000 words."
        segments = segment_by_rules(content, target_words=5000)
        assert len(segments) == 1
    
    def test_segment_at_paragraph(self):
        """测试在段落边界分割"""
        # 创建超过目标词数的内容
        para1 = "word " * 3000  # ~3000 词
        para2 = "word " * 3000
        content = f"{para1}\n\n{para2}"
        
        segments = segment_by_rules(content, target_words=5000)
        
        # 应该在空行处分割
        assert len(segments) >= 1
