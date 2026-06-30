#!/usr/bin/env python3
"""
search_knowledge.py — 双源知识库检索

功能：
1. 连接 distilled.db（公共库）→ FTS5 全文检索 → top-5
2. 连接 personal.db（私人库）→ FTS5 全文检索 → top-2
3. 合并排序输出
4. 无结果时输出 "NO_RESULTS"

接口：python3 search_knowledge.py <关键词1> <关键词2> ...

依赖：Python 内置模块（sqlite3, json, sys, os）
无需 pip install。
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
    """安全解析 JSON，支持字符串和 dict 输入"""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def _extract_content(analysis_data: dict) -> str:
    """从 analysis JSON 中提取最有信息量的文字"""
    parts = []
    
    # 1. litigation_motive.underlying_conflict（争议本质）
    lm = analysis_data.get("litigation_motive", {})
    if isinstance(lm, dict):
        uc = lm.get("underlying_conflict", "")
        if uc and len(str(uc)) > 5:
            parts.append(str(uc))
        # trigger_event.value
        te = lm.get("trigger_event", {})
        if isinstance(te, dict):
            val = te.get("value", "")
            if val:
                parts.append(str(val))
        # defendant_stance
        ds = lm.get("defendant_stance", {})
        if isinstance(ds, dict):
            val = ds.get("value", "")
            if val:
                parts.append(str(val)[:200])
    
    # 2. evidence_battle 中的证据名
    eb = analysis_data.get("evidence_battle", {})
    if isinstance(eb, dict):
        for side in ("plaintiff_evidence", "defendant_evidence"):
            evs = eb.get(side, [])
            if isinstance(evs, list):
                for e in evs:
                    if isinstance(e, dict):
                        en = e.get("evidence", "")
                        if en and len(str(en)) >= 2:
                            parts.append(str(en))
    
    # 3. basic_info 中的案由、法院
    bi = analysis_data.get("basic_info", {})
    if isinstance(bi, dict):
        ct = bi.get("case_type", "")
        if ct:
            parts.append(str(ct))
    
    return " ".join(parts)


def search_fts5(db_path: str, query: str, top_k: int) -> list:
    """在单个数据库中做 FTS5 全文检索"""
    results = []
    if not os.path.exists(db_path):
        return results
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute(
            """SELECT c.id, c.case_no, c.court_name, c.case_type,
                      c.result, c.result_type, c.analysis
               FROM cases_fts f JOIN cases c ON c.id = f.case_id
               WHERE cases_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, top_k)
        ).fetchall()
        
        for row in rows:
            case = dict(row)
            analysis = _safe_json_parse(case.get("analysis"))
            content = _extract_content(analysis)
            
            results.append({
                "case_no": case.get("case_no", ""),
                "case_type": case.get("case_type", ""),
                "court_name": case.get("court_name", ""),
                "result_type": case.get("result_type", ""),
                "content": content[:200] if content else "",
                "source": "public" if "distilled" in db_path else "personal",
            })
        
        conn.close()
    except Exception as e:
        print(f"[search] WARNING: {db_path} 检索异常: {e}", file=sys.stderr)
    
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python3 search_knowledge.py <关键词1> <关键词2> ...", file=sys.stderr)
        print("NO_RESULTS")
        sys.exit(1)
    
    # FTS5 查询：空格分隔 = OR 匹配
    query = " OR ".join(sys.argv[1:])
    
    if not query.strip():
        print("NO_RESULTS")
        sys.exit(0)
    
    results = []
    results += search_fts5(PUBLIC_DB, query, 5)
    results += search_fts5(PRIVATE_DB, query, 2)
    
    # 去重
    seen = set()
    deduped = []
    for r in results:
        key = r["case_no"]
        if key and key not in seen:
            seen.add(key)
            deduped.append(r)
        elif not key:
            deduped.append(r)
    
    if not deduped:
        print("NO_RESULTS")
        sys.exit(0)
    
    # 输出：案号|案由|法院|判决结果|案情概要|来源
    for r in deduped[:5]:
        line = "|".join([
            r["case_no"],
            r["case_type"] or "",
            r["court_name"] or "",
            r["result_type"] or "",
            r["content"][:150],
            r["source"],
        ])
        print(line)


if __name__ == "__main__":
    main()
