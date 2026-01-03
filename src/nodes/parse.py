"""Stage 4: Parse - 格式验证（简化版）"""

import re
import json
from pathlib import Path

from ..state import TranslationState
from ..config import DATA_DIR


def validate_markdown(content: str) -> list[str]:
    """验证 Markdown 格式
    
    检查项：
    - 标题层级
    - 代码块闭合
    - 链接格式
    
    Args:
        content: Markdown 内容
    
    Returns:
        问题列表
    """
    issues = []
    lines = content.split('\n')
    
    # 检查代码块闭合
    code_block_count = content.count('```')
    if code_block_count % 2 != 0:
        issues.append("代码块未闭合 (``` 数量为奇数)")
    
    # 检查标题层级跳跃
    prev_level = 0
    for i, line in enumerate(lines):
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if level > prev_level + 1 and prev_level > 0:
                issues.append(f"行 {i+1}: 标题层级跳跃 (H{prev_level} -> H{level})")
            prev_level = level
    
    # 检查链接格式
    broken_links = re.findall(r'\[([^\]]*)\]\s+\(', content)
    if broken_links:
        issues.append(f"可能的断裂链接: {broken_links[:3]}")
    
    return issues


def parse_and_validate(state: TranslationState) -> TranslationState:
    """验证所有翻译结果的格式
    
    Stage 4 节点：
    - 检查 Markdown 格式
    - 生成验证报告
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    book_id = state["book_id"]
    segments_data = state["segments"]
    
    print(f"🔎 验证格式...")
    
    try:
        book_dir = DATA_DIR / book_id
        all_issues = {}
        
        for seg_data in segments_data:
            seg_id = seg_data["id"]
            translation = seg_data.get("translation", "")
            
            if translation:
                issues = validate_markdown(translation)
                if issues:
                    all_issues[seg_id] = issues
        
        # 保存验证报告
        validation_file = book_dir / "validation.json"
        with open(validation_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_segments": len(segments_data),
                "segments_with_issues": len(all_issues),
                "issues": all_issues
            }, f, ensure_ascii=False, indent=2)
        
        if all_issues:
            print(f"⚠️  发现 {len(all_issues)} 个段落有格式问题")
            for seg_id, issues in list(all_issues.items())[:3]:
                print(f"   段落 {seg_id}: {issues[0]}")
        else:
            print(f"✅ 格式验证通过")
        
        return {**state, "error": None}
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return {**state, "error": str(e)}
