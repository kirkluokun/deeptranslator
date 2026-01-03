#!/usr/bin/env python3
"""重新翻译指定的段落

用法:
    python -m src.tools.retranslate_segments <book_id> <segment_id1> [segment_id2] ...
    
示例:
    python -m src.tools.retranslate_segments 026194f1 6 23 44 45
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.translate import translate_segment
from src.state import Segment
from src.config import DATA_DIR


async def retranslate_segment(book_id: str, segment_id: int):
    """重新翻译单个段落"""
    book_dir = DATA_DIR / book_id
    
    # 读取原始段落
    segment_file = book_dir / "segments" / f"segment_{segment_id:03d}.md"
    if not segment_file.exists():
        print(f"❌ 段落文件不存在: {segment_file}")
        return
    
    with open(segment_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 创建 Segment 对象
    segment = Segment(
        id=segment_id,
        content=content,
        status="pending"
    )
    
    print(f"🔄 重新翻译段落 {segment_id}...")
    try:
        # 翻译
        translated = await translate_segment(segment)
        
        # 保存翻译结果
        translation_file = book_dir / "translations" / f"segment_{segment_id:03d}.md"
        with open(translation_file, "w", encoding="utf-8") as f:
            f.write(translated.translation)
        
        print(f"✅ 段落 {segment_id} 翻译完成")
        print(f"   输出: {translation_file}")
        
    except Exception as e:
        print(f"❌ 段落 {segment_id} 翻译失败: {e}")
        raise


async def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python retranslate_segments.py <book_id> <segment_id1> [segment_id2] ...")
        print("示例: python retranslate_segments.py 026194f1 6 23 44 45")
        sys.exit(1)
    
    book_id = sys.argv[1]
    segment_ids = [int(sid) for sid in sys.argv[2:]]
    
    print(f"📖 书籍 ID: {book_id}")
    print(f"📝 待翻译段落: {segment_ids}")
    print()
    
    # 并发翻译
    tasks = [retranslate_segment(book_id, sid) for sid in segment_ids]
    await asyncio.gather(*tasks)
    
    print("\n✅ 所有段落翻译完成")


if __name__ == "__main__":
    asyncio.run(main())
