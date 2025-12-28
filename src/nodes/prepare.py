"""Stage 2: Prepare - 文档分段"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict

from ..state import TranslationState, Segment, CheckpointState
from ..config import config, DATA_DIR
from ..utils.markdown_cleaner import count_words


@dataclass
class SegmentMeta:
    """分段元数据"""
    id: int
    start_line: int
    end_line: int
    word_count: int
    preview: str  # 前50字符预览


def find_paragraph_boundaries(content: str) -> list[int]:
    """找到所有段落边界（行号）
    
    段落边界包括：
    - 空行
    - 标题行（#开头）
    - 水平线（---）
    
    Args:
        content: 文档内容
    
    Returns:
        边界行号列表（1-indexed）
    """
    lines = content.split('\n')
    boundaries = [0]  # 开始
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 空行
        if not stripped:
            boundaries.append(i)
        # 标题
        elif stripped.startswith('#'):
            boundaries.append(i)
        # 水平线
        elif stripped in ('---', '***', '___'):
            boundaries.append(i)
    
    boundaries.append(len(lines))  # 结束
    return sorted(set(boundaries))


def segment_by_rules(content: str, target_words: int = 5000) -> list[tuple[int, int]]:
    """基于规则的分段策略
    
    策略：
    1. 找到所有自然段落边界
    2. 累积段落直到接近目标词数
    3. 在最近的边界处分割
    
    Args:
        content: 文档内容
        target_words: 每段目标词数
    
    Returns:
        [(start_line, end_line), ...] (0-indexed)
    """
    lines = content.split('\n')
    boundaries = find_paragraph_boundaries(content)
    
    segments = []
    current_start = 0
    current_words = 0
    
    for i, line in enumerate(lines):
        line_words = count_words(line)
        current_words += line_words
        
        # 如果达到目标词数，在最近的边界分割
        if current_words >= target_words and i > current_start:
            # 找最近的边界
            closest_boundary = current_start
            for b in boundaries:
                if b > current_start and b <= i:
                    closest_boundary = b
            
            # 如果找到了更好的边界
            if closest_boundary > current_start:
                segments.append((current_start, closest_boundary))
                current_start = closest_boundary
                # 重新计算剩余词数
                current_words = sum(count_words(lines[j]) for j in range(closest_boundary, i + 1))
    
    # 添加最后一段
    if current_start < len(lines):
        segments.append((current_start, len(lines)))
    
    return segments


def prepare_segments(state: TranslationState) -> TranslationState:
    """分段处理
    
    Stage 2 节点：
    - 使用规则分段（MVP 阶段）
    - 保存各段落文件
    - 生成元数据
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    book_id = state["book_id"]
    raw_content = state["raw_content"]
    
    if not raw_content:
        return {**state, "error": "raw_content 为空，请先执行 acquire"}
    
    print(f"✂️  开始分段...")
    
    try:
        target_words = config.segment_words
        lines = raw_content.split('\n')
        
        # 执行分段
        segment_ranges = segment_by_rules(raw_content, target_words)
        
        book_dir = DATA_DIR / book_id
        segments_dir = book_dir / "segments"
        
        segments = []
        segment_metas = []
        
        for idx, (start, end) in enumerate(segment_ranges):
            segment_id = idx + 1
            segment_lines = lines[start:end]
            segment_content = '\n'.join(segment_lines)
            word_count = count_words(segment_content)
            
            # 保存分段文件
            segment_file = segments_dir / f"segment_{segment_id:03d}.md"
            with open(segment_file, "w", encoding="utf-8") as f:
                f.write(segment_content)
            
            # 创建 Segment 对象
            segment = Segment(
                id=segment_id,
                content=segment_content,
                translation="",
                status="pending",
                review_count=0,
                review_notes=[]
            )
            segments.append(segment.to_dict())
            
            # 创建元数据
            preview = segment_content[:50].replace('\n', ' ')
            meta = SegmentMeta(
                id=segment_id,
                start_line=start + 1,  # 1-indexed
                end_line=end,
                word_count=word_count,
                preview=preview + "..." if len(segment_content) > 50 else preview
            )
            segment_metas.append(asdict(meta))
            
            print(f"   段落 {segment_id}: {word_count:,} 词")
        
        # 保存元数据
        meta_file = book_dir / "segments_meta.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_segments": len(segments),
                "target_words": target_words,
                "segments": segment_metas
            }, f, ensure_ascii=False, indent=2)
        
        # 更新断点状态
        checkpoint = CheckpointState.load(book_dir)
        if checkpoint:
            checkpoint.stage = "prepare"
            checkpoint.save(book_dir)
        
        total_words = sum(m["word_count"] for m in segment_metas)
        print(f"✅ 分段完成: {len(segments)} 段, 共 {total_words:,} 词")
        
        return {
            **state,
            "segments": segments,
            "total_segments": len(segments),
            "completed_segments": 0,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ 分段失败: {e}")
        return {**state, "error": str(e)}


def load_segments_from_disk(book_id: str) -> list[dict]:
    """从磁盘加载分段
    
    用于断点续传时恢复分段数据
    """
    book_dir = DATA_DIR / book_id
    segments_dir = book_dir / "segments"
    translations_dir = book_dir / "translations"
    
    segments = []
    
    # 加载元数据
    meta_file = book_dir / "segments_meta.json"
    if not meta_file.exists():
        return segments
    
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    for seg_meta in meta["segments"]:
        segment_id = seg_meta["id"]
        segment_file = segments_dir / f"segment_{segment_id:03d}.md"
        translation_file = translations_dir / f"segment_{segment_id:03d}.md"
        
        # 加载原文
        content = ""
        if segment_file.exists():
            with open(segment_file, "r", encoding="utf-8") as f:
                content = f.read()
        
        # 检查是否已翻译
        translation = ""
        status = "pending"
        if translation_file.exists():
            with open(translation_file, "r", encoding="utf-8") as f:
                translation = f.read()
            status = "done"
        
        segment = Segment(
            id=segment_id,
            content=content,
            translation=translation,
            status=status,
            review_count=0,
            review_notes=[]
        )
        segments.append(segment.to_dict())
    
    return segments
