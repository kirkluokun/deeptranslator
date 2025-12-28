"""LangGraph 图定义"""

from typing import Literal
from langgraph.graph import StateGraph, END

from .state import TranslationState
from .nodes.acquire import acquire_document
from .nodes.prepare import prepare_segments
from .nodes.translate import translate_segments
from .nodes.review import review_segments
from .nodes.parse import parse_and_validate
from .nodes.render import render_output


def should_review(state: TranslationState) -> Literal["review", "parse"]:
    """判断是否需要审核"""
    # 检查是否有需要审核的段落
    for seg in state.get("segments", []):
        if seg.get("status") == "reviewing":
            return "review"
    return "parse"


def check_review_complete(state: TranslationState) -> Literal["review", "parse"]:
    """检查审核是否完成"""
    for seg in state.get("segments", []):
        status = seg.get("status")
        if status == "reviewing":
            return "review"
    return "parse"


def check_error(state: TranslationState) -> Literal["continue", "end"]:
    """检查是否有错误"""
    if state.get("error"):
        return "end"
    return "continue"


def build_translation_graph() -> StateGraph:
    """构建翻译工作流图
    
    流程：
    acquire -> prepare -> translate -> review (loop) -> parse -> render
    
    Returns:
        编译好的图
    """
    # 创建图
    workflow = StateGraph(TranslationState)
    
    # 添加节点
    workflow.add_node("acquire", acquire_document)
    workflow.add_node("prepare", prepare_segments)
    workflow.add_node("translate", translate_segments)
    workflow.add_node("review", review_segments)
    workflow.add_node("parse", parse_and_validate)
    workflow.add_node("render", render_output)
    
    # 设置入口
    workflow.set_entry_point("acquire")
    
    # 添加边 - 正常流程
    workflow.add_edge("acquire", "prepare")
    workflow.add_edge("prepare", "translate")
    
    # translate -> review 或 parse
    workflow.add_conditional_edges(
        "translate",
        should_review,
        {
            "review": "review",
            "parse": "parse"
        }
    )
    
    # review -> 继续 review 或 parse
    workflow.add_conditional_edges(
        "review",
        check_review_complete,
        {
            "review": "review",
            "parse": "parse"
        }
    )
    
    # parse -> render
    workflow.add_edge("parse", "render")
    
    # render -> END
    workflow.add_edge("render", END)
    
    return workflow.compile()


def run_translation(
    source_path: str,
    source_type: str,
    book_id: str | None = None
) -> TranslationState:
    """运行翻译流程
    
    Args:
        source_path: 源文件路径
        source_type: 文件类型 (md | epub)
        book_id: 可选的书籍 ID（用于续传）
    
    Returns:
        最终状态
    """
    from .nodes.acquire import generate_book_id
    from .state import create_initial_state
    
    # 生成或使用提供的 book_id
    if not book_id:
        book_id = generate_book_id(source_path)
    
    # 创建初始状态
    initial_state = create_initial_state(
        book_id=book_id,
        book_name="",  # 将在 acquire 阶段填充
        source_path=source_path,
        source_type=source_type
    )
    
    # 构建并运行图
    graph = build_translation_graph()
    final_state = graph.invoke(initial_state)
    
    return final_state
