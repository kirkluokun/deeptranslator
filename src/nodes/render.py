"""Stage 5: Render - 合并输出"""

from datetime import datetime
from pathlib import Path

from ..state import TranslationState, Segment, CheckpointState
from ..config import DATA_DIR, config
from ..llm import LLMManager


def render_output(state: TranslationState) -> TranslationState:
    """合并所有翻译段落，生成最终输出
    
    Stage 5 节点：
    - 检查是否有失败段落（如有则报错）
    - 按顺序合并所有翻译
    - 输出到输入文件同目录
    - 添加元信息
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    book_id = state["book_id"]
    book_name = state["book_name"]
    source_path = state["source_path"]
    segments_data = state["segments"]
    failed_segments = state.get("failed_segments", [])
    
    print(f"📝 合并输出...")
    
    # 检查是否有失败段落
    if failed_segments:
        print(f"⚠️  存在 {len(failed_segments)} 个失败段落: {failed_segments}")
        print(f"   将继续合并，但这些段落可能包含未翻译内容")
    
    try:
        book_dir = DATA_DIR / book_id
        
        # 确定输出路径：输入文件同目录
        source_file = Path(source_path)
        if source_file.exists():
            output_dir = source_file.parent
            # 输出文件名基于输入文件名
            input_stem = source_file.stem  # 不带扩展名的文件名
            target_lang = config.target_language
            output_filename = f"{input_stem}_{target_lang}.md"
        else:
            # 回退到默认目录
            output_dir = book_dir / "output"
            output_dir.mkdir(exist_ok=True)
            safe_name = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()
            output_filename = f"{safe_name}_{config.target_language}.md"
        
        output_file = output_dir / output_filename
        
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
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)
        
        # 同时在 data 目录保存一份备份
        backup_dir = book_dir / "output"
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / output_filename
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(final_output)
        
        # 更新断点状态
        checkpoint = CheckpointState.load(book_dir)
        if checkpoint:
            checkpoint.stage = "render"
            checkpoint.save(book_dir)
        
        print(f"✅ 输出完成:")
        print(f"   主文件: {output_file}")
        print(f"   备份: {backup_file}")
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
