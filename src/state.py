"""状态定义模块 - LangGraph State"""

from typing import TypedDict, Literal
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


SegmentStatus = Literal["pending", "translating", "reviewing", "done", "failed"]


@dataclass
class Segment:
    """翻译段落"""
    id: int
    content: str                          # 原文内容
    translation: str = ""                 # 译文
    status: SegmentStatus = "pending"
    review_count: int = 0                 # 审核轮次
    review_notes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "translation": self.translation,
            "status": self.status,
            "review_count": self.review_count,
            "review_notes": self.review_notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Segment":
        return cls(**data)


class TranslationState(TypedDict):
    """LangGraph 翻译状态"""
    # 元信息
    book_id: str
    book_name: str
    source_path: str
    source_type: str  # md | epub
    
    # 处理状态
    raw_content: str                    # 清洗后的原始内容
    segments: list[dict]                # 分段列表 (Segment.to_dict())
    current_batch: list[int]            # 当前并行处理的 segment IDs
    
    # 统计信息
    total_segments: int
    completed_segments: int
    failed_segments: list[int]
    
    # 输出
    final_output: str
    
    # Token 消耗追踪
    tokens_used: dict  # {model_name: {input: x, output: y}}
    
    # 错误信息
    error: str | None


@dataclass
class CheckpointState:
    """断点续传状态"""
    book_id: str
    stage: str                           # acquire | prepare | translate | review | parse | render
    completed_segments: list[int]
    failed_segments: list[int]
    last_update: str
    
    def to_dict(self) -> dict:
        return {
            "book_id": self.book_id,
            "stage": self.stage,
            "completed_segments": self.completed_segments,
            "failed_segments": self.failed_segments,
            "last_update": self.last_update
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointState":
        return cls(**data)
    
    def save(self, data_dir: Path) -> None:
        """保存到文件"""
        self.last_update = datetime.now().isoformat()
        state_file = data_dir / "state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, data_dir: Path) -> "CheckpointState | None":
        """从文件加载"""
        state_file = data_dir / "state.json"
        if not state_file.exists():
            return None
        with open(state_file, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


def create_initial_state(
    book_id: str,
    book_name: str,
    source_path: str,
    source_type: str
) -> TranslationState:
    """创建初始状态"""
    return TranslationState(
        book_id=book_id,
        book_name=book_name,
        source_path=source_path,
        source_type=source_type,
        raw_content="",
        segments=[],
        current_batch=[],
        total_segments=0,
        completed_segments=0,
        failed_segments=[],
        final_output="",
        tokens_used={},
        error=None
    )
