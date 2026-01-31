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
    
    # 현재 시간
    current_time = datetime.now().strftime("%Y-%m-%d")
    
    # 사이트맵 시작
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
    
    <!-- 메인 페이지 -->
    <url>
        <loc>{base_url}/</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>

    <!-- 나이 계산 페이지 -->
    <url>
        <loc>{base_url}/age</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>

    <!-- 반려동물 나이 계산 페이지 -->
    <url>
        <loc>{base_url}/dog</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/cat</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>

    <!-- 아기 개월 수 계산 페이지 -->
    <url>
        <loc>{base_url}/baby-months</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>

    <!-- 안내 페이지 -->
    <url>
        <loc>{base_url}/guide</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/faq</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/privacy</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/terms</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <!-- 정적 리소스 -->
    <url>
        <loc>{base_url}/static/css/style.css</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.3</priority>
    </url>
    
    <url>
        <loc>{base_url}/static/js/age-calculator.js</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.3</priority>
    </url>
    
    <!-- 이미지 리소스 (있는 경우) -->
    <url>
        <loc>{base_url}/static/images/og-image.png</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>yearly</changefreq>
        <priority>0.2</priority>
    </url>
    
    <url>
        <loc>{base_url}/favicon.ico</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>yearly</changefreq>
        <priority>0.1</priority>
    </url>
    
    <url>
        <loc>{base_url}/apple-touch-icon.png</loc>
        <lastmod>{current_time}</lastmod>
        <changefreq>yearly</changefreq>
        <priority>0.1</priority>
    </url>
    
</urlset>"""
    
    return sitemap

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
