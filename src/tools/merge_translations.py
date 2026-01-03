#!/usr/bin/env python3
"""合并所有翻译段落生成最终文档

用法:
    python -m src.tools.merge_translations <book_id>
    
示例:
    python -m src.tools.merge_translations 026194f1
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATA_DIR
from src.nodes.render import render_output
from src.state import TranslationState, CheckpointState


def load_state_from_checkpoint(book_id: str) -> TranslationState | None:
    """从断点加载状态"""
    book_dir = DATA_DIR / book_id
    checkpoint = CheckpointState.load(book_dir)
    
    if not checkpoint:
        return None
    
    # 读取 segments_meta.json
    segments_meta_file = book_dir / "segments_meta.json"
    if not segments_meta_file.exists():
        return None
    
    import json
    with open(segments_meta_file, "r", encoding="utf-8") as f:
        segments_meta = json.load(f)
    
    # 读取所有翻译文件
    translations_dir = book_dir / "translations"
    segments = []
    total_segments = len(segments_meta.get("segments", []))
    
    for i in range(1, total_segments + 1):
        translation_file = translations_dir / f"segment_{i:03d}.md"
        translation = ""
        status = "pending"
        
        if translation_file.exists():
            with open(translation_file, "r", encoding="utf-8") as f:
                translation = f.read().strip()
            status = "done" if translation else "pending"
        
        # 读取原始内容
        segment_file = book_dir / "segments" / f"segment_{i:03d}.md"
        content = ""
        if segment_file.exists():
            with open(segment_file, "r", encoding="utf-8") as f:
                content = f.read()
        
        segments.append({
            "id": i,
            "content": content,
            "translation": translation,
            "status": status,
            "review_count": 0,
            "review_notes": []
        })
    
    # 读取书名 - 从 raw.md 或 segments_meta.json
    book_name = "Việt Nam Sử Lược"
    raw_file = book_dir / "raw.md"
    if raw_file.exists():
        with open(raw_file, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line.startswith("#"):
                book_name = first_line.lstrip("#").strip()
    
    if book_name == "Unknown":
        book_name = segments_meta.get("book_name", "Việt Nam Sử Lược")
    
    return {
        "book_id": book_id,
        "book_name": book_name,
        "source_path": str(book_dir / "raw.md"),
        "source_type": "md",
        "raw_content": "",
        "segments": segments,
        "current_batch": [],
        "total_segments": total_segments,
        "completed_segments": sum(1 for s in segments if s["status"] == "done"),
        "failed_segments": [],
        "error": None,
        "final_output": None
    }


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python merge_translations.py <book_id>")
        print("示例: python merge_translations.py 026194f1")
        sys.exit(1)
    
    book_id = sys.argv[1]
    
    print(f"📖 书籍 ID: {book_id}")
    print("📝 开始合并翻译...")
    print()
    
    # 加载状态
    state = load_state_from_checkpoint(book_id)
    
    if not state:
        print("❌ 无法加载状态，尝试直接合并文件...")
        # 直接合并翻译文件
        book_dir = DATA_DIR / book_id
        translations_dir = book_dir / "translations"
        output_dir = book_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 查找所有翻译文件
        translation_files = sorted(translations_dir.glob("segment_*.md"))
        
        if not translation_files:
            print("❌ 未找到翻译文件")
            sys.exit(1)
        
        # 合并内容
        translations = []
        for tf in translation_files:
            with open(tf, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    translations.append(content)
        
        final_content = "\n\n".join(translations)
        
        # 读取书名
        segments_meta_file = book_dir / "segments_meta.json"
        book_name = "Việt Nam Sử Lược"
        if segments_meta_file.exists():
            import json
            with open(segments_meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                book_name = meta.get("book_name", book_name)
        
        # 添加元信息
        meta_info = f"""---

## 翻译信息

- **书名**: {book_name}
- **翻译日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **段落**: {len(translations)}/{len(translation_files)} 完成

*由 DeepTranslator 自动翻译*
"""
        
        final_output = f"{final_content}\n\n{meta_info}"
        
        # 保存
        safe_name = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()
        output_file = output_dir / f"{safe_name}_zh.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output)
        
        print(f"✅ 合并完成: {output_file}")
        print(f"   总字符数: {len(final_output):,}")
        print(f"   段落数: {len(translations)}")
        return
    
    # 使用 render_output 函数
    result = render_output(state)
    
    if result.get("error"):
        print(f"❌ 合并失败: {result['error']}")
        sys.exit(1)
    
    print(f"\n✅ 合并完成!")
    print(f"   输出文件: {result.get('final_output')}")


if __name__ == "__main__":
    main()
