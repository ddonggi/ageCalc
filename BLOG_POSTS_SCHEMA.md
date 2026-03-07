# Blog Posts Schema (MySQL 8)

`agecalc` 데이터베이스에서 블로그 글 저장용 단일 테이블(`posts`) 스키마입니다.
댓글 기능은 제외한 구조입니다.

## Create Table SQL

```sql
CREATE TABLE posts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  slug VARCHAR(180) NOT NULL,
  title VARCHAR(255) NOT NULL,
  excerpt VARCHAR(500) NULL,
  content LONGTEXT NOT NULL,
  content_format ENUM('html', 'markdown', 'text') NOT NULL DEFAULT 'html',

  cover_image_url VARCHAR(1000) NULL,
  cover_image_alt VARCHAR(255) NULL,
  image_urls JSON NULL,

  status ENUM('draft', 'published', 'archived') NOT NULL DEFAULT 'draft',
  is_featured TINYINT(1) NOT NULL DEFAULT 0,
  view_count BIGINT UNSIGNED NOT NULL DEFAULT 0,

  meta_title VARCHAR(255) NULL,
  meta_description VARCHAR(320) NULL,

  published_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_posts_slug (slug),
  KEY idx_posts_status_published_at (status, published_at),
  KEY idx_posts_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Column Notes

- `slug`: URL 경로 식별자. 유니크 제약으로 중복 방지.
- `content`: 본문 원문 저장(HTML/Markdown/Text).
- `image_urls`: 본문 내 추가 이미지 URL 목록(JSON 배열).
- `status`: 발행 상태(`draft`, `published`, `archived`).
- `published_at`: 실제 공개 시각. 임시저장(draft)에서는 `NULL` 가능.
- `meta_title`, `meta_description`: SEO 메타 정보.

## Example Insert

```sql
INSERT INTO posts (
  slug, title, excerpt, content, content_format,
  cover_image_url, status, published_at
) VALUES (
  'hello-agecalc-blog',
  '첫 블로그 글',
  '요약입니다.',
  '<p>본문입니다.</p>',
  'html',
  'https://cdn.example.com/post1-cover.jpg',
  'published',
  NOW()
);
```
