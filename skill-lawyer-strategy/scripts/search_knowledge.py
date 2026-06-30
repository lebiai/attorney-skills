#!/usr/bin/env python3
"""
search_knowledge.py v3 — 双源知识库检索

检索方式：LIKE 全文匹配（支持中文，无需外部依赖）
评分方式：完整关键词命中计数（案由匹配权重更高）

接口：python3 search_knowledge.py <关键词1> <关键词2> ...

依赖：Python 内置模块（sqlite3, json, sys, os）
"""

import sys
import os
import json
import sqlite3

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
PUBLIC_DB = os.path.join(DATA_DIR, "distilled.db")
PRIVATE_DB = os.path.join(DATA_DIR, "personal.db")


def _safe_json_parse(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def _extract_content(analysis_data):
    """从 analysis JSON 中提取最有信息量的文字"""
    parts = []
    lm = analysis_data.get("litigation_motive", {}) or {}
    if isinstance(lm, dict):
        uc = lm.get("underlying_conflict", "") or ""
        if len(str(uc)) > 5:
            parts.append(str(uc))
        te = lm.get("trigger_event", {}) or {}
        if isinstance(te, dict):
            val = te.get("value", "") or ""
            if val:
                parts.append(str(val)[:200])
    eb = analysis_data.get("evidence_battle", {}) or {}
    if isinstance(eb, dict):
        for side in ("plaintiff_evidence", "defendant_evidence"):
            evs = eb.get(side, []) or []
            if isinstance(evs, list):
                for e in evs:
                    if isinstance(e, dict):
                        en = e.get("evidence", "") or ""
                        if len(str(en)) >= 2:
                            parts.append(str(en))
    bi = analysis_data.get("basic_info", {}) or {}
    if isinstance(bi, dict):
        ct = bi.get("case_type", "") or ""
        if ct:
            parts.append(str(ct))
    return " ".join(parts)


def _score_result(analysis_text, case_type, keywords):
    """
    评分规则（纯整词匹配，无子串干扰）：
    - 完整关键词出现在 analysis 中：+10
    - 完整关键词出现在 case_type 中：+15（案由匹配最重要）
    - 需要至少 1 个整词命中 case_type 或 2 个整词命中 analysis 才算相关
    """
    score = 0
    for kw in keywords:
        clean = kw.strip()
        if not clean:
            continue
        if clean in analysis_text:
            score += 10
        if clean in case_type:
            score += 15
    return score


def search_db(db_path, keywords, top_k):
    """检索单个数据库：LIKE 主通道（兼容 FTS5 不可靠的中文环境）"""
    results = []
    if not os.path.exists(db_path):
        return results
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        combined = []
        seen_ids = set()
        
        # 主通道: LIKE 多关键词检索
        for kw in keywords:
            if not kw.strip():
                continue
            try:
                for row in conn.execute(
                    "SELECT id, case_no, case_type, court_name, result_type, analysis "
                    "FROM cases WHERE analysis LIKE ? LIMIT ?",
                    (f'%{kw}%', top_k)
                ):
                    if row["id"] not in seen_ids:
                        seen_ids.add(row["id"])
                        combined.append(dict(row))
            except Exception:
                pass
        
        conn.close()
        
        # 评分排序
        scored = []
        for c in combined:
            analysis = _safe_json_parse(c.get("analysis"))
            analysis_text = json.dumps(analysis, ensure_ascii=False)
            content = _extract_content(analysis)
            score = _score_result(analysis_text, c.get("case_type", "") or "", keywords)
            scored.append({
                "case_no": c.get("case_no", "") or "",
                "case_type": c.get("case_type", "") or "",
                "court_name": c.get("court_name", "") or "",
                "result_type": c.get("result_type", "") or "",
                "content": content[:200],
                "score": score,
                "source": "public" if "distilled" in db_path else "personal",
            })
        
        scored.sort(key=lambda r: r["score"], reverse=True)
        results = scored[:top_k]
    except Exception as e:
        print(f"[search] WARNING: {os.path.basename(db_path)} 检索异常: {e}", file=sys.stderr)
    
    return results


def main():
    if len(sys.argv) < 2:
        print("NO_RESULTS")
        sys.exit(1)
    
    keywords = [kw.strip() for kw in sys.argv[1:] if kw.strip()]
    if not keywords:
        print("NO_RESULTS")
        sys.exit(0)
    
    results = search_db(PUBLIC_DB, keywords, 8)
    results += search_db(PRIVATE_DB, keywords, 3)
    
    # 去重
    seen, deduped = set(), []
    for r in results:
        k = r["case_no"]
        if k and k not in seen:
            seen.add(k)
            deduped.append(r)
        elif not k:
            deduped.append(r)
    
    if not deduped:
        print("NO_RESULTS")
        sys.exit(0)
    
    # 判断相关性（阈值 20 = 1个案由匹配 + 1个原文匹配 / 2个原文匹配）
    relevant = [r for r in deduped if r["score"] >= 20]
    
    if not relevant:
        print("NO_EXACT_MATCH")
        for r in deduped[:3]:
            line = "|".join([
                r["case_no"], r["case_type"], r["court_name"],
                r["result_type"], r["content"][:150],
                str(r["score"]), r["source"],
            ])
            print(line)
        sys.exit(0)
    
    for r in relevant[:5]:
        line = "|".join([
            r["case_no"], r["case_type"], r["court_name"],
            r["result_type"], r["content"][:150],
            str(r["score"]), r["source"],
        ])
        print(line)


if __name__ == "__main__":
    main()
