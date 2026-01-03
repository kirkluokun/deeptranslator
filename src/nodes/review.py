"""Stage 3: Review - 翻译审核"""

import asyncio
import json
from pathlib import Path

from ..state import TranslationState, Segment, CheckpointState
from ..config import config, DATA_DIR
from ..llm import LLMManager, retry_with_backoff
from ..prompts.review import get_review_prompt, parse_review_response


@retry_with_backoff()
async def review_segment(segment: Segment) -> Segment:
    """审核单个段落
    
    Args:
        segment: 待审核的段落
    
    Returns:
        审核后的段落
    """
    system_prompt, user_prompt = get_review_prompt(
        original=segment.content,
        translation=segment.translation
    )
    
    response = await LLMManager.invoke(
        purpose="review",
        prompt=user_prompt,
        system_prompt=system_prompt
    )
    
    is_approved, corrected, issues = parse_review_response(response)
    
    segment.review_count += 1
    
    if is_approved:
        segment.status = "done"
        segment.review_notes.append("APPROVED")
    else:
        segment.review_notes.extend(issues)
        if corrected:
            segment.translation = corrected
        # 如果达到最大审核次数，标记为完成
        if segment.review_count >= config.max_review_rounds:
            segment.status = "done"
            segment.review_notes.append(f"达到最大审核次数 ({config.max_review_rounds})")
        else:
            segment.status = "reviewing"  # 继续审核
    
    return segment


async def review_batch(
    segments: list[Segment],
    book_dir: Path,
    semaphore: asyncio.Semaphore
) -> list[Segment]:
    """批量审核段落"""
    async def review_with_semaphore(seg: Segment) -> Segment:
        async with semaphore:
            print(f"🔍 审核段落 {seg.id} (第 {seg.review_count + 1} 轮)...")
            try:
                result = await review_segment(seg)
                
                # 保存审核结果
                review_file = book_dir / "reviews" / f"segment_{seg.id:03d}.json"
                with open(review_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "segment_id": seg.id,
                        "review_count": seg.review_count,
                        "status": seg.status,
                        "notes": seg.review_notes
                    }, f, ensure_ascii=False, indent=2)
                
                # 如果有修正，更新翻译文件
                if result.status == "done":
                    translation_file = book_dir / "translations" / f"segment_{seg.id:03d}.md"
                    with open(translation_file, "w", encoding="utf-8") as f:
                        f.write(result.translation)
                
                status_icon = "✅" if result.status == "done" else "🔄"
                print(f"{status_icon} 段落 {seg.id} 审核: {result.review_notes[-1] if result.review_notes else 'OK'}")
                return result
            except Exception as e:
                print(f"❌ 段落 {seg.id} 审核失败: {e}")
                seg.status = "failed"
                return seg
    
    tasks = [review_with_semaphore(seg) for seg in segments]
    results = await asyncio.gather(*tasks)
    return results


def review_segments(state: TranslationState) -> TranslationState:
    """审核所有段落（同步包装）"""
    return asyncio.run(review_segments_async(state))


async def review_segments_async(state: TranslationState) -> TranslationState:
    """审核所有段落（异步实现）"""
    book_id = state["book_id"]
    segments_data = state["segments"]
    
    # 找出需要审核的段落
    segments_to_review = []
    for seg_data in segments_data:
        seg = Segment.from_dict(seg_data)
        if seg.status == "reviewing" and seg.translation:
            segments_to_review.append(seg)
    
    if not segments_to_review:
        print("ℹ️  没有需要审核的段落")
        return state
    
    print(f"🔍 开始审核 {len(segments_to_review)} 个段落...")
    
    try:
        book_dir = DATA_DIR / book_id
        parallel = config.parallel_workers
        semaphore = asyncio.Semaphore(parallel)
        
        # 批量审核
        reviewed = await review_batch(segments_to_review, book_dir, semaphore)
        
        # 更新状态
        reviewed_map = {seg.id: seg for seg in reviewed}
        updated_segments = []
        completed = 0
        failed = []
        needs_more_review = False
        
        for seg_data in segments_data:
            seg_id = seg_data["id"]
            if seg_id in reviewed_map:
                seg = reviewed_map[seg_id]
                updated_segments.append(seg.to_dict())
                if seg.status == "done":
                    completed += 1
                elif seg.status == "reviewing":
                    needs_more_review = True
                elif seg.status == "failed":
                    failed.append(seg_id)
            else:
                updated_segments.append(seg_data)
                if seg_data.get("status") == "done":
                    completed += 1
        
        # 更新断点状态
        checkpoint = CheckpointState.load(book_dir)
        if checkpoint:
            checkpoint.stage = "review"
            checkpoint.completed_segments = [s["id"] for s in updated_segments if s.get("status") == "done"]
            checkpoint.failed_segments = failed
            checkpoint.save(book_dir)
        
        print(f"✅ 审核完成: {completed}/{len(segments_data)} 段通过")
        if needs_more_review:
            print("⚠️  部分段落需要再次审核")
        
        return {
            **state,
            "segments": updated_segments,
            "completed_segments": completed,
            "failed_segments": failed,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ 审核失败: {e}")
        return {**state, "error": str(e)}
