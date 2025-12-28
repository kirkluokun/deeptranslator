"""Stage 5: Render - 合并输出"""

from datetime import datetime
from pathlib import Path

from ..state import TranslationState, Segment, CheckpointState
from ..config import DATA_DIR
from ..llm import LLMManager


def render_output(state: TranslationState) -> TranslationState:
    """合并所有翻译段落，生成最终输出
    
    Stage 5 节点：
    - 按顺序合并所有翻译
    - 生成目录（可选）
    - 添加元信息
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    book_id = state["book_id"]
    book_name = state["book_name"]
    segments_data = state["segments"]
    
    print(f"📝 合并输出...")
    
    try:
        book_dir = DATA_DIR / book_id
        output_dir = book_dir / "output"
        
        # 按 ID 排序
        sorted_segments = sorted(segments_data, key=lambda x: x["id"])
        
        # 合并翻译内容
        translations = []
        for seg_data in sorted_segments:
            translation = seg_data.get("translation", "")
            if translation:
                translations.append(translation)
        
        if not translations:
            return {**state, "error": "没有可合并的翻译内容"}
        
        # 拼接内容
        final_content = "\n\n".join(translations)
        
        # 添加元信息
        meta_info = generate_meta_info(state)
        final_output = f"{final_content}\n\n---\n\n{meta_info}"
        
        # 保存输出文件
        safe_name = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()
        output_file = output_dir / f"{safe_name}_zh.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)
        
        # 更新断点状态
        checkpoint = CheckpointState.load(book_dir)
        if checkpoint:
            checkpoint.stage = "render"
            checkpoint.save(book_dir)
        
        print(f"✅ 输出完成: {output_file}")
        print(f"   总字符数: {len(final_output):,}")
        
        return {
            **state,
            "final_output": str(output_file),
            "error": None
        }
        
    except Exception as e:
        print(f"❌ 合并失败: {e}")
        return {**state, "error": str(e)}


def generate_meta_info(state: TranslationState) -> str:
    """生成翻译元信息"""
    book_name = state["book_name"]
    total_segments = state["total_segments"]
    completed = state["completed_segments"]
    failed = state["failed_segments"]
    tokens_used = LLMManager.get_usage()
    
    lines = [
        "## 翻译信息",
        "",
        f"- **书名**: {book_name}",
        f"- **翻译日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- **段落**: {completed}/{total_segments} 完成",
    ]
    
    if failed:
        lines.append(f"- **失败段落**: {failed}")
    
    if tokens_used:
        lines.append("")
        lines.append("### Token 使用统计")
        for model, usage in tokens_used.items():
            lines.append(f"- {model}: 输入 {usage['input']:,} / 输出 {usage['output']:,}")
    
    lines.append("")
    lines.append("*由 DeepTranslator 自动翻译*")
    
    return "\n".join(lines)
