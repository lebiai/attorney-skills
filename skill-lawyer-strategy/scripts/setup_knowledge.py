#!/usr/bin/env python3
"""
setup_knowledge.py — 律师策略知识库安装/更新工具

功能：
1. 检测本地 data/distilled.db 是否存在
2. 存在 → 读取版本号（kb_meta 表），请求 GitHub API 查最新 Release 版本
3. 有新版本 → 询问用户是否更新
4. 不存在 → 从 GitHub Releases 下载最新版
5. 校验完整性（文件大小 > 1MB，能 SELECT COUNT(*)）

依赖：Python 内置模块（sqlite3, urllib.request, json, os, sys）
无需 pip install。
"""

import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error

# ===== 配置 =====
# 技能知识库 GitHub Releases 地址
GITHUB_OWNER = "lebiai"
GITHUB_REPO = "attorney-skills"
RELEASE_API = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
DOWNLOAD_URL_TEMPLATE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest/download/distilled.db"

# 本地路径
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "distilled.db")

# 最小文件大小（1MB）
MIN_SIZE = 1 * 1024 * 1024


def get_local_version(db_path: str) -> str:
    """读取本地知识库版本号"""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT value FROM kb_meta WHERE key='version'"
        ).fetchone()
        conn.close()
        return row[0] if row else "0.0"
    except Exception:
        return "0.0"


def get_remote_version() -> tuple:
    """查询 GitHub API 获取最新 Release 版本和下载 URL
    
    返回: (version: str, download_url: str) 或 (None, None)
    """
    try:
        req = urllib.request.Request(
            RELEASE_API,
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "lebi-strategy-skill"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        tag = data.get("tag_name", "").lstrip("v")
        # 找资产中的 distilled.db
        for asset in data.get("assets", []):
            if asset["name"] == "distilled.db":
                return tag, asset["browser_download_url"]
        # 没有匹配资产，用默认 URL
        return tag, None
    except Exception:
        return None, None


def download_file(url: str, dest: str) -> bool:
    """下载文件到本地路径"""
    print(f"[setup] 正在下载知识库...")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"[setup] 下载失败: {e}")
        return False


def verify_db(path: str) -> bool:
    """校验知识库完整性"""
    if not os.path.exists(path):
        print("[setup] 文件不存在")
        return False
    size = os.path.getsize(path)
    if size < MIN_SIZE:
        print(f"[setup] 文件过小: {size} bytes (需 > {MIN_SIZE})")
        return False
    try:
        conn = sqlite3.connect(path)
        count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        conn.close()
        print(f"[setup] 知识库验证通过: {count} 件案例, {size / 1024 / 1024:.1f}MB")
        return True
    except Exception as e:
        print(f"[setup] 数据库验证失败: {e}")
        return False


def ask_user(prompt: str) -> bool:
    """询问用户是否执行操作，从 stdin 读入"""
    print(prompt)
    try:
        answer = input("(y/N): ").strip().lower()
        return answer in ("y", "yes")
    except EOFError:
        return True  # 非交互模式默认同意


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    local_ver = get_local_version(DB_PATH)
    
    if local_ver:
        print(f"[setup] 本地知识库版本: v{local_ver}")
        
        # 检查远程版本
        remote_ver, remote_url = get_remote_version()
        if remote_ver is None:
            print("[setup] 无法查询最新版本（网络异常），使用本地版本")
            print("STATUS: OK")
            return
        
        print(f"[setup] 远程知识库版本: v{remote_ver}")
        
        # 比较版本
        if local_ver == remote_ver:
            print("[setup] 知识库已是最新")
            print("STATUS: OK")
            return
        
        # 有新版本，询问
        print(f"[setup] 发现新版知识库 v{remote_ver}（当前 v{local_ver}）")
        if ask_user("是否更新知识库？不影响您已保存的私人知识库。"):
            url = remote_url or DOWNLOAD_URL_TEMPLATE
            if download_file(url, DB_PATH):
                if verify_db(DB_PATH):
                    print("[setup] 更新完成")
                    print("STATUS: UPDATED")
                else:
                    print("[setup] 更新失败：文件损坏")
                    print("STATUS: FAILED")
            else:
                print("[setup] 更新失败：下载错误")
                print("STATUS: FAILED")
        else:
            print("[setup] 已跳过更新，继续使用当前版本")
            print("STATUS: OK")
    else:
        # 首次安装
        print("[setup] 本地未发现知识库，正在下载...")
        url = DOWNLOAD_URL_TEMPLATE
        if download_file(url, DB_PATH):
            if verify_db(DB_PATH):
                print("[setup] 知识库安装完成")
                print("STATUS: DOWNLOADED")
            else:
                print("[setup] 下载文件损坏")
                print("STATUS: FAILED")
        else:
            print("[setup] 下载失败，请检查网络连接")
            print("STATUS: FAILED")


if __name__ == "__main__":
    main()
