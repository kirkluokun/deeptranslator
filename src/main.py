"""DeepTranslator CLI 入口"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from .config import config, DATA_DIR
from .graph import run_translation
from .nodes.acquire import load_from_checkpoint, generate_book_id
from .nodes.prepare import load_segments_from_disk
from .state import create_initial_state

console = Console()


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        description="DeepTranslator - 整书翻译工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # translate 命令
    translate_parser = subparsers.add_parser("translate", help="翻译文档")
    translate_parser.add_argument("file", help="输入文件路径 (MD 或 EPUB)")
    translate_parser.add_argument("-o", "--output", help="输出目录")
    translate_parser.add_argument("--stage", choices=["acquire", "prepare", "translate", "review", "parse", "render"],
                                  help="仅执行到指定阶段")
    translate_parser.add_argument("--dry-run", action="store_true", help="预估成本，不实际执行")
    
    # resume 命令
    resume_parser = subparsers.add_parser("resume", help="从断点继续")
    resume_parser.add_argument("data_dir", help="数据目录路径 (data/<book_id>)")
    
    # validate 命令
    validate_parser = subparsers.add_parser("validate", help="验证输出文件格式")
    validate_parser.add_argument("file", help="待验证的 Markdown 文件")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "translate":
            cmd_translate(args)
        elif args.command == "resume":
            cmd_resume(args)
        elif args.command == "validate":
            cmd_validate(args)
    except KeyboardInterrupt:
        console.print("\n⚠️  用户中断", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ 错误: {e}", style="red")
        sys.exit(1)


def cmd_translate(args):
    """执行翻译命令"""
    source_path = Path(args.file).resolve()
    
    if not source_path.exists():
        console.print(f"❌ 文件不存在: {source_path}", style="red")
        sys.exit(1)
    
    # 判断文件类型
    suffix = source_path.suffix.lower()
    if suffix == ".md":
        source_type = "md"
    elif suffix == ".epub":
        source_type = "epub"
    else:
        console.print(f"❌ 不支持的文件格式: {suffix}", style="red")
        sys.exit(1)
    
    console.print(Panel(
        f"[bold]DeepTranslator[/bold]\n"
        f"📄 文件: {source_path.name}\n"
        f"📁 类型: {source_type.upper()}\n"
        f"🔧 模型: {config.get_model('translate')['name']}",
        title="开始翻译"
    ))
    
    if args.dry_run:
        console.print("\n📊 [yellow]Dry Run 模式 - 不实际执行[/yellow]")
        # TODO: 实现成本估算
        console.print("   成本估算功能待实现")
        return
    
    # 运行翻译
    result = run_translation(
        source_path=str(source_path),
        source_type=source_type
    )
    
    if result.get("error"):
        console.print(f"\n❌ 翻译失败: {result['error']}", style="red")
        sys.exit(1)
    
    if result.get("final_output"):
        console.print(f"\n✅ [green]翻译完成![/green]")
        console.print(f"   输出文件: {result['final_output']}")


def cmd_resume(args):
    """从断点继续"""
    data_dir = Path(args.data_dir).resolve()
    
    if not data_dir.exists():
        console.print(f"❌ 目录不存在: {data_dir}", style="red")
        sys.exit(1)
    
    checkpoint, raw_content = load_from_checkpoint(data_dir)
    
    if not checkpoint:
        console.print(f"❌ 未找到断点状态", style="red")
        sys.exit(1)
    
    console.print(Panel(
        f"[bold]断点续传[/bold]\n"
        f"📁 Book ID: {checkpoint.book_id}\n"
        f"📍 阶段: {checkpoint.stage}\n"
        f"✅ 已完成: {len(checkpoint.completed_segments)} 段\n"
        f"❌ 失败: {len(checkpoint.failed_segments)} 段",
        title="恢复状态"
    ))
    
    # 加载分段
    segments = load_segments_from_disk(checkpoint.book_id)
    
    # 创建恢复状态
    state = create_initial_state(
        book_id=checkpoint.book_id,
        book_name="",
        source_path="",
        source_type=""
    )
    state["raw_content"] = raw_content or ""
    state["segments"] = segments
    state["total_segments"] = len(segments)
    state["completed_segments"] = len(checkpoint.completed_segments)
    state["failed_segments"] = checkpoint.failed_segments
    
    # 根据阶段决定从哪里开始
    from .graph import build_translation_graph
    graph = build_translation_graph()
    
    # TODO: 实现从特定阶段恢复
    console.print("\n⚠️  完整的断点续传功能待完善")


def cmd_validate(args):
    """验证文件格式"""
    file_path = Path(args.file).resolve()
    
    if not file_path.exists():
        console.print(f"❌ 文件不存在: {file_path}", style="red")
        sys.exit(1)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    from .nodes.parse import validate_markdown
    issues = validate_markdown(content)
    
    if issues:
        console.print(f"\n⚠️  发现 {len(issues)} 个问题:", style="yellow")
        for issue in issues:
            console.print(f"   - {issue}")
    else:
        console.print("\n✅ [green]格式验证通过[/green]")


if __name__ == "__main__":
    main()
