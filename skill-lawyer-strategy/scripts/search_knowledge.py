#!/usr/bin/env python3
"""
search_knowledge.py v2 — 双源知识库检索（改进版）
"""

import sys
import os
import json
import sqlite3
import re

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


def _build_fts5_query(keywords):
    clauses = []
    for kw in keywords:
        clean = re.sub(r'[\s,，。、；：""''【】（）()《》]', '', kw)
        if not clean:
            continue
        if len(clean) == 1:
            clauses.append(clean)
        else:
            chars = " AND ".join(list(clean))
            clauses.append(f"({chars})")
    return " OR ".join(clauses)


def _score_result(analysis_text, case_type, keywords):
    score = 0
    for kw in keywords:
        clean = kw.strip()
        if not clean:
            continue
        # 原词匹配
        if clean in analysis_text:
            score += 3
        if clean in case_type:
            score += 5
        # 双字子串匹配
        for i in range(len(clean) - 1):
            bigram = clean[i:i+2]
            if len(bigram) >= 2 and bigram in analysis_text:
                score += 1
    return score


def search_db(db_path, keywords, top_k):
    results = []
    if not os.path.exists(db_path):
        return results
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        fts5_query = _build_fts5_query(keywords)
        combined = []
        seen_ids = set()
        
        # 通道1: FTS5
        if fts5_query.strip() and fts5_query != "OR":
            try:
                for row in conn.execute(
                    """SELECT c.id, c.case_no, c.court_name, c.case_type,
                              c.result, c.result_type, c.analysis
                       FROM cases_fts f JOIN cases c ON c.id = f.case_id
                       WHERE cases_fts MATCH ?
                       ORDER BY rank LIMIT ?""",
                    (fts5_query, top_k * 2)
                ):
                    if row["id"] not in seen_ids:
                        seen_ids.add(row["id"])
                        combined.append(dict(row))
            except Exception:
                pass
        
        # 通道2: LIKE 兜底
        if len(combined) < top_k:
            for kw in keywords:
                if not kw.strip():
                    continue
                try:
                    for row in conn.execute(
                        "SELECT * FROM cases WHERE analysis LIKE ? LIMIT ?",
                        (f'%{kw}%', top_k - len(combined))
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
    
    results = search_db(PUBLIC_DB, keywords, 5)
    results += search_db(PRIVATE_DB, keywords, 2)
    
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
    
    # 判断相关性
    relevant = [r for r in deduped if r["score"] >= 5]
    
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
