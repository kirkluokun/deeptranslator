"""Stage 3: Translate - 翻译"""

import asyncio
import re
from pathlib import Path

from ..state import TranslationState, Segment, CheckpointState
from ..config import config, DATA_DIR
from ..llm import LLMManager, retry_with_backoff
from ..prompts.translate import get_translate_prompt


def detect_source_language_ratio(text: str, source_lang: str) -> float:
    """检测文本中源语言的比例
    
    Args:
        text: 待检测文本
        source_lang: 源语言代码
    
    Returns:
        源语言字符占比 (0.0 - 1.0)
    """
    if not text:
        return 0.0
    
    # 越南语特征字符（带声调的拉丁字母）
    vi_lower = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    vi_chars = set(vi_lower + vi_lower.upper())
    
    # 中文字符范围
    zh_pattern = re.compile(r'[\u4e00-\u9fff]')
    
    # 统计字符
    total_chars = len(text.replace(" ", "").replace("\n", ""))
    if total_chars == 0:
        return 0.0
    
    if source_lang == "vi":
        # 越南语：检测带声调字符
        vi_count = sum(1 for c in text if c in vi_chars)
        return vi_count / total_chars
    elif source_lang == "zh":
        # 中文：检测汉字
        zh_count = len(zh_pattern.findall(text))
        return zh_count / total_chars
    elif source_lang == "en":
        # 英语：检测纯ASCII字母比例
        ascii_count = sum(1 for c in text if c.isascii() and c.isalpha())
        return ascii_count / total_chars
    
    return 0.0


def is_translation_valid(original: str, translation: str, source_lang: str, target_lang: str) -> tuple[bool, str]:
    """验证翻译是否有效
    
    Args:
        original: 原文
        translation: 译文
        source_lang: 源语言代码
        target_lang: 目标语言代码
    
    Returns:
        (是否有效, 原因)
    """
    if not translation or len(translation.strip()) < 10:
        return False, "翻译结果为空或过短"
    
    # 检测源语言残留比例
    source_ratio = detect_source_language_ratio(translation, source_lang)
    
    # 如果源语言残留超过 30%，认为翻译失败
    if source_ratio > 0.30:
        return False, f"源语言残留过多 ({source_ratio:.1%})"
    
    # 检测目标语言比例
    if target_lang == "zh":
        zh_pattern = re.compile(r'[\u4e00-\u9fff]')
        zh_count = len(zh_pattern.findall(translation))
        total_chars = len(translation.replace(" ", "").replace("\n", ""))
        if total_chars > 0 and zh_count / total_chars < 0.3:
            return False, f"目标语言(中文)比例过低 ({zh_count}/{total_chars})"
    
    return True, "翻译有效"


@retry_with_backoff()
async def translate_segment(segment: Segment, max_retries: int = 3) -> Segment:
    """翻译单个段落（带质量检测和重试）
    
    Args:
        segment: 待翻译的段落
        max_retries: 质量检测失败后的最大重试次数
    
    Returns:
        翻译后的段落
    """
    source_lang = config.source_language
    target_lang = config.target_language
    
    for attempt in range(max_retries):
        system_prompt, user_prompt = get_translate_prompt(segment.content)
        
        translation = await LLMManager.invoke(
            purpose="translate",
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        translation = translation.strip()
        
        # 验证翻译质量
        is_valid, reason = is_translation_valid(
            segment.content, translation, source_lang, target_lang
        )
        
        if is_valid:
            segment.translation = translation
            segment.status = "done"  # 翻译成功
            return segment
        else:
            if attempt < max_retries - 1:
                print(f"   ⚠️ 段落 {segment.id} 翻译质量不合格 ({reason})，重试 {attempt + 2}/{max_retries}")
            else:
                print(f"   ❌ 段落 {segment.id} 翻译质量检测失败: {reason}")
                segment.translation = translation  # 保存失败的翻译供人工检查
                segment.status = "failed"
                segment.review_notes.append(f"翻译质量检测失败: {reason}")
    
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
                
                if result.status == "done":
                    print(f"✅ 段落 {seg.id} 翻译完成")
                else:
                    print(f"⚠️ 段落 {seg.id} 翻译质量不合格，标记为失败")
                return result
            except Exception as e:
                print(f"❌ 段落 {seg.id} 翻译异常: {e}")
                seg.status = "failed"
                seg.review_notes.append(f"翻译异常: {str(e)}")
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
    """翻译所有段落（异步实现）
    
    包含自动重试机制：
    1. 第一轮翻译所有段落
    2. 检测失败段落，自动重试（最多3轮）
    3. 仅当全部成功或达到最大重试次数后才继续
    """
    book_id = state["book_id"]
    segments_data = state["segments"]
    max_rounds = 3  # 最大重试轮次
    
    if not segments_data:
        return {**state, "error": "segments 为空，请先执行 prepare"}
    
    print(f"🌐 开始翻译 {len(segments_data)} 个段落...")
    
    try:
        book_dir = DATA_DIR / book_id
        parallel = config.parallel_workers
        semaphore = asyncio.Semaphore(parallel)
        
        # 转换为 Segment 对象，只处理未完成的
        all_segments = {seg_data["id"]: Segment.from_dict(seg_data) for seg_data in segments_data}
        
        for round_num in range(1, max_rounds + 1):
            # 收集待翻译段落
            segments_to_translate = [
                seg for seg in all_segments.values() 
                if seg.status in ("pending", "failed")
            ]
            
            if not segments_to_translate:
                print(f"✅ 所有段落翻译完成")
                break
            
            if round_num > 1:
                print(f"\n🔄 第 {round_num} 轮重试 - 重新翻译 {len(segments_to_translate)} 个失败段落...")
            else:
                print(f"   待翻译: {len(segments_to_translate)} 段 (并发: {parallel})")
            
            # 批量翻译
            translated = await translate_batch(segments_to_translate, book_dir, semaphore)
            
            # 更新 all_segments
            for seg in translated:
                all_segments[seg.id] = seg
            
            # 统计结果
            done_count = sum(1 for s in all_segments.values() if s.status == "done")
            failed_count = sum(1 for s in all_segments.values() if s.status == "failed")
            
            print(f"   第 {round_num} 轮结果: {done_count} 成功, {failed_count} 失败")
            
            if failed_count == 0:
                break
        
        # 构建最终结果
        updated_segments = []
        completed = 0
        failed = []
        
        for seg_id in sorted(all_segments.keys()):
            seg = all_segments[seg_id]
            updated_segments.append(seg.to_dict())
            if seg.status == "done":
                completed += 1
            elif seg.status == "failed":
                failed.append(seg_id)
        
        # 更新断点状态
        checkpoint = CheckpointState.load(book_dir)
        if checkpoint:
            checkpoint.stage = "translate"
            checkpoint.completed_segments = [s["id"] for s in updated_segments if s.get("status") == "done"]
            checkpoint.failed_segments = failed
            checkpoint.save(book_dir)
        
        # 报告最终结果
        print(f"\n{'='*50}")
        print(f"📊 翻译结果: {completed}/{len(segments_data)} 段完成")
        
        if failed:
            print(f"⚠️  失败段落 ({len(failed)} 个): {failed}")
            print(f"   这些段落需要人工检查或重新翻译")
        else:
            print(f"✅ 全部翻译成功！")
        print(f"{'='*50}\n")
        
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
