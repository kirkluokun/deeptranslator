"""Stage 3: Translate - 翻译"""

import asyncio
from pathlib import Path

from ..state import TranslationState, Segment, CheckpointState
from ..config import config, DATA_DIR
from ..llm import LLMManager, retry_with_backoff
from ..prompts.translate import get_translate_prompt


@retry_with_backoff()
async def translate_segment(segment: Segment) -> Segment:
    """翻译单个段落
    
    Args:
        segment: 待翻译的段落
    
    Returns:
        翻译后的段落
    """
    system_prompt, user_prompt = get_translate_prompt(segment.content)
    
    translation = await LLMManager.invoke(
        purpose="translate",
        prompt=user_prompt,
        system_prompt=system_prompt
    )
    
    segment.translation = translation.strip()
    segment.status = "reviewing"  # 等待审核
    
    return segment


async def translate_batch(
    segments: list[Segment],
    book_dir: Path,
    semaphore: asyncio.Semaphore
) -> list[Segment]:
    """批量翻译段落
    
    Args:
        segments: 待翻译的段落列表
        book_dir: 书籍数据目录
        semaphore: 并发控制信号量
    
    Returns:
        翻译后的段落列表
    """
    async def translate_with_semaphore(seg: Segment) -> Segment:
        async with semaphore:
            print(f"🔄 翻译段落 {seg.id}...")
            try:
                result = await translate_segment(seg)
                
                # 保存翻译结果
                translation_file = book_dir / "translations" / f"segment_{seg.id:03d}.md"
                with open(translation_file, "w", encoding="utf-8") as f:
                    f.write(result.translation)
                
                print(f"✅ 段落 {seg.id} 翻译完成")
                return result
            except Exception as e:
                print(f"❌ 段落 {seg.id} 翻译失败: {e}")
                seg.status = "failed"
                return seg
    
    tasks = [translate_with_semaphore(seg) for seg in segments]
    results = await asyncio.gather(*tasks)
    return results


def translate_segments(state: TranslationState) -> TranslationState:
    """翻译所有段落（同步包装）
    
    Stage 3 翻译节点：
    - 并行翻译（受并发数限制）
    - 保存翻译结果
    - 更新进度
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    return asyncio.run(translate_segments_async(state))


async def translate_segments_async(state: TranslationState) -> TranslationState:
    """翻译所有段落（异步实现）"""
    book_id = state["book_id"]
    segments_data = state["segments"]
    
    if not segments_data:
        return {**state, "error": "segments 为空，请先执行 prepare"}
    
    print(f"🌐 开始翻译 {len(segments_data)} 个段落...")
    
    try:
        book_dir = DATA_DIR / book_id
        parallel = config.parallel_workers
        semaphore = asyncio.Semaphore(parallel)
        
        # 转换为 Segment 对象，只处理未完成的
        segments_to_translate = []
        for seg_data in segments_data:
            seg = Segment.from_dict(seg_data)
            if seg.status in ("pending", "failed"):
                segments_to_translate.append(seg)
        
        print(f"   待翻译: {len(segments_to_translate)} 段 (并发: {parallel})")
        
        # 批量翻译
        translated = await translate_batch(segments_to_translate, book_dir, semaphore)
        
        # 更新状态中的 segments
        translated_map = {seg.id: seg for seg in translated}
        updated_segments = []
        completed = 0
        failed = []
        
        for seg_data in segments_data:
            seg_id = seg_data["id"]
            if seg_id in translated_map:
                seg = translated_map[seg_id]
                updated_segments.append(seg.to_dict())
                if seg.status == "done" or seg.status == "reviewing":
                    completed += 1
                elif seg.status == "failed":
                    failed.append(seg_id)
            else:
                # 已完成的保持原样
                updated_segments.append(seg_data)
                if seg_data.get("status") == "done":
                    completed += 1
        
        # 更新断点状态
        checkpoint = CheckpointState.load(book_dir)
        if checkpoint:
            checkpoint.stage = "translate"
            checkpoint.completed_segments = [s["id"] for s in updated_segments if s.get("status") in ("done", "reviewing")]
            checkpoint.failed_segments = failed
            checkpoint.save(book_dir)
        
        print(f"✅ 翻译完成: {completed}/{len(segments_data)} 段")
        
        return {
            **state,
            "segments": updated_segments,
            "completed_segments": completed,
            "failed_segments": failed,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ 翻译失败: {e}")
        return {**state, "error": str(e)}
