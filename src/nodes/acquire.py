"""Stage 1: Acquire - 文档获取与清洗"""

import hashlib
from pathlib import Path

from ..state import TranslationState, CheckpointState
from ..config import DATA_DIR
from ..utils.markdown_cleaner import load_markdown_file, clean_markdown, extract_title
from ..utils.epub_converter import convert_epub_to_markdown, get_epub_metadata


def generate_book_id(source_path: str) -> str:
    """生成书籍唯一 ID
    
    基于文件路径生成短哈希作为 ID
    """
    hash_str = hashlib.md5(source_path.encode()).hexdigest()[:8]
    return hash_str


def acquire_document(state: TranslationState) -> TranslationState:
    """获取并清洗文档
    
    Stage 1 节点：
    - 根据文件类型加载内容
    - 清洗 Markdown
    - 创建数据目录
    - 保存 raw.md
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    source_path = Path(state["source_path"])
    source_type = state["source_type"]
    book_id = state["book_id"]
    
    print(f"📖 加载文档: {source_path.name}")
    
    try:
        # 根据类型加载内容
        if source_type == "epub":
            raw_content = convert_epub_to_markdown(source_path)
            # 尝试获取元数据作为书名
            try:
                metadata = get_epub_metadata(source_path)
                book_name = metadata.get("title") or source_path.stem
            except Exception:
                book_name = source_path.stem
        else:  # md
            raw_content = load_markdown_file(source_path)
            book_name = extract_title(raw_content) or source_path.stem
        
        # 确保内容被清洗
        raw_content = clean_markdown(raw_content)
        
        # 创建数据目录
        book_dir = DATA_DIR / book_id
        book_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (book_dir / "segments").mkdir(exist_ok=True)
        (book_dir / "translations").mkdir(exist_ok=True)
        (book_dir / "reviews").mkdir(exist_ok=True)
        (book_dir / "output").mkdir(exist_ok=True)
        
        # 保存 raw.md
        raw_file = book_dir / "raw.md"
        with open(raw_file, "w", encoding="utf-8") as f:
            f.write(raw_content)
        
        print(f"✅ 已清洗并保存: {raw_file}")
        print(f"   书名: {book_name}")
        print(f"   字符数: {len(raw_content):,}")
        
        # 初始化断点状态
        checkpoint = CheckpointState(
            book_id=book_id,
            stage="acquire",
            completed_segments=[],
            failed_segments=[],
            last_update=""
        )
        checkpoint.save(book_dir)
        
        # 更新状态
        return {
            **state,
            "book_name": book_name,
            "raw_content": raw_content,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return {
            **state,
            "error": str(e)
        }


def load_from_checkpoint(book_dir: Path) -> tuple[CheckpointState | None, str | None]:
    """从断点加载状态
    
    Args:
        book_dir: 书籍数据目录
    
    Returns:
        (checkpoint_state, raw_content)
    """
    checkpoint = CheckpointState.load(book_dir)
    if not checkpoint:
        return None, None
    
    raw_file = book_dir / "raw.md"
    if not raw_file.exists():
        return checkpoint, None
    
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_content = f.read()
    
    return checkpoint, raw_content
