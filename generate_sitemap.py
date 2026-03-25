    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사이트맵 자동 생성 스크립트
만 나이 계산기 사이트맵을 생성합니다.
"""

import os
from datetime import datetime
from urllib.parse import urljoin

def generate_sitemap(base_url="https://yourdomain.com"):
    """사이트맵 XML을 생성합니다."""
    current_time = datetime.now().strftime("%Y-%m-%d")

    page_entries = [
        ("/", "weekly", "1.0"),
        ("/age", "weekly", "0.9"),
        ("/dog", "monthly", "0.8"),
        ("/cat", "monthly", "0.8"),
        ("/baby-months", "monthly", "0.8"),
        ("/parent-child", "monthly", "0.8"),
        ("/guide", "monthly", "0.8"),
        ("/faq", "monthly", "0.8"),
        ("/privacy", "monthly", "0.8"),
        ("/terms", "monthly", "0.8"),
        ("/minigames", "monthly", "0.7"),
        ("/minigames/guess", "monthly", "0.7"),
        ("/minigames/snake", "monthly", "0.7"),
        ("/minigames/tictactoe", "monthly", "0.7"),
        ("/minigames/rps", "monthly", "0.7"),
        ("/minigames/nim", "monthly", "0.7"),
        ("/minigames/pong", "monthly", "0.7"),
        ("/minigames/hangman", "monthly", "0.7"),
        ("/minigames/memory", "monthly", "0.7"),
        ("/minigames/connect4", "monthly", "0.7"),
        ("/minigames/lightsout", "monthly", "0.7"),
        ("/minigames/minesweeper", "monthly", "0.7"),
        ("/minigames/simon", "monthly", "0.7"),
        ("/minigames/2048", "monthly", "0.7"),
        ("/minigames/blackjack", "monthly", "0.7"),
        ("/minigames/breakout", "monthly", "0.7"),
        ("/minigames/hanoi", "monthly", "0.7"),
        ("/minigames/pig", "monthly", "0.7"),
        ("/minigames/gomoku", "monthly", "0.7"),
        ("/minigames/reversi", "monthly", "0.7"),
        ("/minigames/dotsandboxes", "monthly", "0.7"),
        ("/minigames/mancala", "monthly", "0.7"),
        ("/minigames/mastermind", "monthly", "0.7"),
        ("/minigames/war", "monthly", "0.7"),
    ]

    static_entries = [
        ("/static/css/style.css", "monthly", "0.3"),
        ("/static/js/age-calculator.js", "monthly", "0.3"),
        ("/static/images/og-image.png", "yearly", "0.2"),
        ("/favicon.ico", "yearly", "0.1"),
        ("/apple-touch-icon.png", "yearly", "0.1"),
    ]

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9',
        '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">',
        "",
    ]

    for path, changefreq, priority in page_entries:
        lines.extend(
            [
                "    <url>",
                f"        <loc>{base_url}{path}</loc>",
                f"        <lastmod>{current_time}</lastmod>",
                f"        <changefreq>{changefreq}</changefreq>",
                f"        <priority>{priority}</priority>",
                "    </url>",
                "",
            ]
        )

    for path, changefreq, priority in static_entries:
        lines.extend(
            [
                "    <url>",
                f"        <loc>{base_url}{path}</loc>",
                f"        <lastmod>{current_time}</lastmod>",
                f"        <changefreq>{changefreq}</changefreq>",
                f"        <priority>{priority}</priority>",
                "    </url>",
                "",
            ]
        )

    lines.append("</urlset>")
    return "\n".join(lines)

def save_sitemap(sitemap_content, filename="sitemap.xml"):
    """사이트맵을 파일로 저장합니다."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sitemap_content)
        print(f"✅ 사이트맵이 {filename}에 성공적으로 저장되었습니다.")
        return True
    except Exception as e:
        print(f"❌ 사이트맵 저장 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 만 나이 계산기 사이트맵 생성기")
    print("=" * 50)
    
    # 사용자로부터 도메인 입력 받기
    base_url = input("도메인을 입력하세요 (예: https://example.com): ").strip()
    
    if not base_url:
        base_url = "https://yourdomain.com"
        print(f"기본값 사용: {base_url}")
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = f"https://{base_url}"
    
    print(f"\n📝 {base_url}에 대한 사이트맵을 생성합니다...")
    
    # 사이트맵 생성
    sitemap_content = generate_sitemap(base_url)
    
    # 파일로 저장
    if save_sitemap(sitemap_content):
        print("\n📋 생성된 사이트맵 내용:")
        print("-" * 30)
        print(sitemap_content)
        print("\n💡 다음 단계:")
        print("1. sitemap.xml 파일을 웹사이트 루트에 업로드")
        print("2. robots.txt의 Sitemap URL을 실제 도메인으로 수정")
        print("3. Google Search Console에 사이트맵 제출")
    
    else:
        print("❌ 사이트맵 생성에 실패했습니다.")

if __name__ == "__main__":
    main()
