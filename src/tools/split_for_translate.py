#!/usr/bin/env python3
"""大文件拆分工具 - 用于翻译前预处理"""

import argparse
import sys
from pathlib import Path


def split_file(
    input_path: str,
    max_chars: int = 300000,
    output_dir: str | None = None
) -> list[Path]:
    """按字符数拆分文件
    
    Args:
        input_path: 输入文件路径
        max_chars: 每份最大字符数（默认 30 万）
        output_dir: 输出目录（默认与输入文件同目录）
    
    Returns:
        拆分后的文件路径列表
    """
    input_file = Path(input_path).resolve()
    
    if not input_file.exists():
        print(f"❌ 文件不存在: {input_file}")
        sys.exit(1)
    
    # 读取内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    total_chars = len(content)
    print(f"📄 文件: {input_file.name}")
    print(f"📊 总字符数: {total_chars:,}")
    
    # 检查是否需要拆分
    if total_chars <= max_chars:
        print(f"✅ 文件小于 {max_chars:,} 字符，无需拆分")
        return [input_file]
    
    # 确定输出目录
    out_dir = Path(output_dir) if output_dir else input_file.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 按行拆分
    lines = content.split('\n')
    parts: list[Path] = []
    current_part = []
    current_chars = 0
    part_num = 1
    
    for line in lines:
        line_chars = len(line) + 1  # +1 for newline
        
        # 如果当前部分加上这行会超限，且当前部分不为空
        if current_chars + line_chars > max_chars and current_part:
            # 保存当前部分
            part_path = _save_part(
                out_dir, input_file.stem, part_num, current_part
            )
            parts.append(part_path)
            print(f"   Part {part_num}: {current_chars:,} 字符")
            
            part_num += 1
            current_part = []
            current_chars = 0
        
        current_part.append(line)
        current_chars += line_chars
    
    # 保存最后一部分
    if current_part:
        part_path = _save_part(
            out_dir, input_file.stem, part_num, current_part
        )
        parts.append(part_path)
        print(f"   Part {part_num}: {current_chars:,} 字符")
    
    print(f"\n✅ 拆分完成，共 {len(parts)} 份")
    for p in parts:
        print(f"   - {p.name}")
    
    return parts


def _save_part(out_dir: Path, stem: str, part_num: int, lines: list[str]) -> Path:
    """保存拆分部分"""
    part_path = out_dir / f"{stem}_part{part_num}.md"
    with open(part_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return part_path


def check_need_split(input_path: str, max_chars: int = 300000) -> dict:
    """检查文件是否需要拆分
    
    Returns:
        {
            "need_split": bool,
            "total_chars": int,
            "estimated_parts": int
        }
    """
    input_file = Path(input_path).resolve()
    
    if not input_file.exists():
        return {"error": f"文件不存在: {input_file}"}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    total_chars = len(content)
    need_split = total_chars > max_chars
    estimated_parts = (total_chars // max_chars) + (1 if total_chars % max_chars else 0)
    
    return {
        "need_split": need_split,
        "total_chars": total_chars,
        "estimated_parts": estimated_parts if need_split else 1
    }


def main():
    parser = argparse.ArgumentParser(
        description="大文件拆分工具 - 翻译前预处理"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # split 命令
    split_parser = subparsers.add_parser("split", help="拆分文件")
    split_parser.add_argument("file", help="输入文件路径")
    split_parser.add_argument(
        "-m", "--max-chars",
        type=int, default=300000,
        help="每份最大字符数（默认 300000）"
    )
    split_parser.add_argument("-o", "--output", help="输出目录")
    
    # check 命令
    check_parser = subparsers.add_parser("check", help="检查是否需要拆分")
    check_parser.add_argument("file", help="输入文件路径")
    check_parser.add_argument(
        "-m", "--max-chars",
        type=int, default=300000,
        help="阈值字符数（默认 300000）"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "split":
        split_file(args.file, args.max_chars, args.output)
    elif args.command == "check":
        result = check_need_split(args.file, args.max_chars)
        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)
        
        print(f"📄 总字符数: {result['total_chars']:,}")
        if result["need_split"]:
            print(f"⚠️  需要拆分，预计 {result['estimated_parts']} 份")
        else:
            print("✅ 无需拆分")


if __name__ == "__main__":
    main()
