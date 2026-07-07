"""
paper_analyzer.py
论文分析助手的核心库：从 PDF 提取文本、解析常见段落（标题、作者、摘要、引言、结论）、生成摘要与关键词。
设计目标：可在 Jupyter 笔记本中直接调用。尽量减少硬依赖，若可用则使用 transformers 进行更好摘要。
"""
from typing import Dict, List, Tuple
import re
import io
import math

# 尽量使用 pdfplumber（纯 Python，效果好）
try:
    import pdfplumber
except Exception:
    pdfplumber = None

# 摘要（可选，若 transformers 可用则调用）
try:
    from transformers import pipeline
    _SUMMARIZER = pipeline("summarization")
except Exception:
    _SUMMARIZER = None

# 简单停用词集合
_STOPWORDS = set("""
and the of to in a is for that on with as are by an be this which or from at it we can have has was were
""".split())


def extract_text_from_pdf(path: str) -> str:
    """从 PDF 提取纯文本。若未安装 pdfplumber，则抛出 RuntimeError。"""
    if pdfplumber is None:
        raise RuntimeError("pdfplumber 未安装。请先 pip install pdfplumber")
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text_parts.append(txt)
    return "\n\n".join(text_parts)


def _first_heading_match(text: str, heading: str) -> Tuple[int,int]:
    """返回 heading 在 text 中第一次出现的 span 索引（start, end），找不到返回 (-1,-1)"""
    pattern = re.compile(r"^\s*" + re.escape(heading) + r"\s*$", flags=re.IGNORECASE | re.MULTILINE)
    m = pattern.search(text)
    if m:
        return m.start(), m.end()
    return -1, -1


def split_into_sections(text: str) -> Dict[str,str]:
    """用简单启发式将文章拆成常见段落：title, authors, abstract, introduction, methods, results, conclusion, references
    依赖关键词匹配，非万能但在大多数论文上有效。"""
    sections = {"full_text": text}

    # 尝试抽取 abstract
    abstract_match = re.search(r"^\s*Abstract\b[\s\S]{10,1000}?\n(?=\n|Introduction|1\.|I\.)", text, flags=re.IGNORECASE | re.MULTILINE)
    if abstract_match:
        sections['abstract'] = abstract_match.group(0).strip()
    else:
        # 备用：查找 'Abstract' 后面到第一个两行空行
        m = re.search(r"Abstract[:\s]*\n([\s\S]{50,2000}?)\n\s*\n", text, flags=re.IGNORECASE)
        if m:
            sections['abstract'] = m.group(1).strip()

    # 标题和作者：通常位于文档开头
    head = text.split('\n')[:20]
    head_text = '\n'.join(head).strip()
    # 移除过长的头部
    candidate_lines = [l.strip() for l in head_text.split('\n') if l.strip()]
    if candidate_lines:
        # 假设第一行是标题，后面一行或两行是作者
        sections['title'] = candidate_lines[0]
        if len(candidate_lines) >= 2:
            sections['authors'] = candidate_lines[1]

    # 简单定位 Introduction 和 Conclusion 段
    intro_pos = None
    concl_pos = None
    for kw in ["Introduction", "INTRODUCTION", "1. Introduction", "I. Introduction"]:
        p = text.find(kw)
        if p != -1:
            intro_pos = p
            break
    for kw in ["Conclusion", "CONCLUSION", "Conclusion and Future Work", "Conclusions"]:
        p = text.find(kw)
        if p != -1:
            concl_pos = p
            break

    if intro_pos is not None and concl_pos is not None and concl_pos > intro_pos:
        sections['introduction'] = text[intro_pos: min(concl_pos, intro_pos + 5000)].strip()
        sections['conclusion'] = text[concl_pos: concl_pos + 2000].strip()
    else:
        # 备用：截取前后若干字
        sections.setdefault('introduction', text[:2000].strip())
        sections.setdefault('conclusion', text[-2000:].strip())

    return sections


def summarize_text(text: str, max_words: int = 150) -> str:
    """生成摘要：若 transformers 可用则调用其模型，否则返回首段或首若干句作为摘要。"""
    if not text or len(text.strip()) == 0:
        return ""
    if _SUMMARIZER is not None:
        # transformers 的 summarizer 通常按字符/标记长度限制，分段处理
        try:
            # 截断为适当长度的片段并合并结果
            chunk_size = 1000
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            summaries = []
            for c in chunks:
                out = _SUMMARIZER(c, max_length= max_words//len(chunks), min_length=30)
                summaries.append(out[0]['summary_text'])
            return ' '.join(summaries)
        except Exception:
            pass
    # fallback: take first 3 sentences
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(sents[:3])


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """非常轻量的关键词提取：去停用词，按词频排序，返回前 K。"""
    if not text:
        return []
    tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    freq = {}
    for t in tokens:
        if t in _STOPWORDS:
            continue
        freq[t] = freq.get(t, 0) + 1
    items = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w,_ in items[:top_k]]


def analyze_paper_from_pdf(path: str) -> Dict[str, object]:
    """主用函数：接收 PDF 路径，返回关键信息字典。"""
    text = extract_text_from_pdf(path)
    sections = split_into_sections(text)
    # 生成摘要（优先摘要段，否则用全文）
    abstract = sections.get('abstract') or ''
    summary = summarize_text(abstract if abstract else sections.get('introduction','')[:4000])
    keywords = extract_keywords(sections.get('abstract','') + '\n' + sections.get('introduction',''))
    result = {
        'title': sections.get('title',''),
        'authors': sections.get('authors',''),
        'abstract': sections.get('abstract',''),
        'summary': summary,
        'keywords': keywords,
        'introduction': sections.get('introduction',''),
        'conclusion': sections.get('conclusion',''),
        'full_text': sections.get('full_text','')[:200000],  # 截断以防内存爆炸
    }
    return result


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description='简单的论文分析器，输入 PDF，输出 JSON。')
    parser.add_argument('pdf', help='论文 PDF 路径')
    parser.add_argument('--out', help='输出 JSON 路径（默认 stdout）')
    args = parser.parse_args()
    res = analyze_paper_from_pdf(args.pdf)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))
