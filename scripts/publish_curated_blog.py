from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env.rss"
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "data" / "blog-release-backups"
BACKUP_SCHEMA_VERSION = 1

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


_load_env_file(ENV_FILE)

from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS  # noqa: E402
from models.blog_models import FeedItem, FeedSource, GeneratedPost, PostSource  # noqa: E402
from scripts.adsense_blog_review import audit_post  # noqa: E402
from scripts.seed_public_blog_posts import build_seed_post_payload  # noqa: E402


class ReleaseError(RuntimeError):
    """Raised when the curated-blog release cannot be completed safely."""


class BackupIntegrityError(ReleaseError):
    """Raised when a release backup is malformed or has been altered."""


AuditCallback = Callable[[GeneratedPost], tuple[bool, str]]


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _post_record(post: GeneratedPost) -> dict[str, object]:
    return {
        "id": post.id,
        "slug": post.slug,
        "title": post.title,
        "excerpt": post.excerpt,
        "content_html": post.content_html,
        "cover_image_url": post.cover_image_url,
        "status": post.status,
        "published_at": _iso(post.published_at),
        "created_at": _iso(post.created_at),
        "updated_at": _iso(post.updated_at),
    }


def _source_record(source: PostSource) -> dict[str, object]:
    return {
        "id": source.id,
        "generated_post_id": source.generated_post_id,
        "feed_item_id": source.feed_item_id,
        "source_name": source.source_name,
        "source_url": source.source_url,
        "attribution_text": source.attribution_text,
    }


def _canonical_json(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _checksum(payload_without_checksum: dict[str, object]) -> str:
    return hashlib.sha256(_canonical_json(payload_without_checksum)).hexdigest()


def _legacy_posts(session) -> list[GeneratedPost]:
    curated_slugs = tuple(BLOG_ARTICLE_BLUEPRINTS)
    return (
        session.query(GeneratedPost)
        .filter(~GeneratedPost.slug.in_(curated_slugs))
        .order_by(GeneratedPost.id.asc())
        .all()
    )


def _linked_sources(session, post_ids: Sequence[int]) -> list[PostSource]:
    if not post_ids:
        return []
    return (
        session.query(PostSource)
        .filter(PostSource.generated_post_id.in_(post_ids))
        .order_by(PostSource.id.asc())
        .all()
    )


def plan_release(session) -> dict[str, object]:
    legacy_posts = _legacy_posts(session)
    legacy_ids = [post.id for post in legacy_posts]
    linked_sources = _linked_sources(session, legacy_ids)
    existing_slugs = {
        slug
        for (slug,) in session.query(GeneratedPost.slug)
        .filter(GeneratedPost.slug.in_(tuple(BLOG_ARTICLE_BLUEPRINTS)))
        .all()
    }
    status_counts: dict[str, int] = {}
    for post in legacy_posts:
        status_counts[post.status] = status_counts.get(post.status, 0) + 1
    return {
        "delete_posts": len(legacy_posts),
        "delete_post_sources": len(linked_sources),
        "delete_status_counts": dict(sorted(status_counts.items())),
        "create_posts": len(BLOG_ARTICLE_BLUEPRINTS) - len(existing_slugs),
        "update_posts": len(existing_slugs),
        "publish_posts": len(BLOG_ARTICLE_BLUEPRINTS),
        "preserve_feed_items": session.query(FeedItem).count(),
        "preserve_feed_sources": session.query(FeedSource).count(),
    }


def create_backup(
    session,
    backup_dir: Path,
    *,
    posts: Sequence[GeneratedPost] | None = None,
    sources: Sequence[PostSource] | None = None,
) -> Path:
    selected_posts = list(posts) if posts is not None else _legacy_posts(session)
    selected_ids = [post.id for post in selected_posts]
    selected_sources = list(sources) if sources is not None else _linked_sources(session, selected_ids)
    body: dict[str, object] = {
        "schema_version": BACKUP_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "generated_posts": [_post_record(post) for post in selected_posts],
        "post_sources": [_source_record(source) for source in selected_sources],
    }
    payload = {**body, "sha256": _checksum(body)}
    backup_dir.mkdir(parents=True, exist_ok=True)
    filename = f"curated-blog-release-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.json"
    destination = backup_dir / filename
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{filename}.", suffix=".tmp", dir=backup_dir)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, destination)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    verify_backup(destination)
    return destination


def verify_backup(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupIntegrityError(f"cannot read backup: {path}") from exc
    if not isinstance(payload, dict):
        raise BackupIntegrityError("backup root must be a JSON object")
    if payload.get("schema_version") != BACKUP_SCHEMA_VERSION:
        raise BackupIntegrityError("unsupported backup schema version")
    recorded_checksum = payload.get("sha256")
    body = {key: value for key, value in payload.items() if key != "sha256"}
    if not isinstance(recorded_checksum, str) or recorded_checksum != _checksum(body):
        raise BackupIntegrityError("backup checksum mismatch")
    if not isinstance(payload.get("generated_posts"), list) or not isinstance(payload.get("post_sources"), list):
        raise BackupIntegrityError("backup row collections are invalid")
    return payload


def _default_audit(post: GeneratedPost) -> tuple[bool, str]:
    result = audit_post(post, require_cover_image=True)
    return result.keep, ",".join(result.issue_codes)


def apply_release(
    session,
    *,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    published_at: datetime | None = None,
    audit_callback: AuditCallback = _default_audit,
) -> dict[str, object]:
    release_plan = plan_release(session)
    legacy_posts = _legacy_posts(session)
    legacy_ids = [post.id for post in legacy_posts]
    linked_sources = _linked_sources(session, legacy_ids)
    backup_path = create_backup(session, backup_dir, posts=legacy_posts, sources=linked_sources)
    publish_time = published_at or datetime.now()

    try:
        if legacy_ids:
            session.query(PostSource).filter(PostSource.generated_post_id.in_(legacy_ids)).delete(
                synchronize_session="fetch"
            )
            session.query(GeneratedPost).filter(GeneratedPost.id.in_(legacy_ids)).delete(
                synchronize_session="fetch"
            )

        curated_posts: list[GeneratedPost] = []
        for slug in BLOG_ARTICLE_BLUEPRINTS:
            payload = build_seed_post_payload(slug)
            post = session.query(GeneratedPost).filter(GeneratedPost.slug == slug).first()
            if post is None:
                post = GeneratedPost(**payload)
                session.add(post)
            else:
                for field, value in payload.items():
                    setattr(post, field, value)
            curated_posts.append(post)
        session.flush()

        for post in curated_posts:
            passed, reason = audit_callback(post)
            if not passed:
                raise ReleaseError(f"curated post failed audit: slug={post.slug} issues={reason}")

        for post in curated_posts:
            post.status = "published"
            post.published_at = publish_time
        session.commit()
    except BaseException:
        session.rollback()
        raise

    return {
        **release_plan,
        "backup_path": str(backup_path),
        "published_at": publish_time.isoformat(),
    }


def restore_backup(session, backup_path: Path) -> dict[str, int]:
    payload = verify_backup(backup_path)
    post_rows = payload["generated_posts"]
    source_rows = payload["post_sources"]
    post_slugs = [str(row["slug"]) for row in post_rows]

    try:
        if post_slugs and session.query(GeneratedPost).filter(GeneratedPost.slug.in_(post_slugs)).count():
            raise ReleaseError("cannot restore: a generated post slug already exists")
        occupied_post_ids = {row[0] for row in session.query(GeneratedPost.id).all()}
        occupied_source_ids = {row[0] for row in session.query(PostSource.id).all()}
        backed_up_post_ids = {int(row["id"]) for row in post_rows}
        backed_up_source_ids = {int(row["id"]) for row in source_rows}
        next_post_id = max(occupied_post_ids | backed_up_post_ids | {0}) + 1
        next_source_id = max(occupied_source_ids | backed_up_source_ids | {0}) + 1
        remapped_post_ids = 0
        remapped_source_ids = 0
        restored_post_ids: dict[int, int] = {}
        restored_posts: list[tuple[int, GeneratedPost]] = []
        for row in post_rows:
            original_id = int(row["id"])
            values = {
                "slug": str(row["slug"]),
                "title": str(row["title"]),
                "excerpt": row["excerpt"],
                "content_html": str(row["content_html"]),
                "cover_image_url": row["cover_image_url"],
                "status": str(row["status"]),
                "published_at": _parse_datetime(row["published_at"]),
                "created_at": _parse_datetime(row["created_at"]),
                "updated_at": _parse_datetime(row["updated_at"]),
            }
            if original_id in occupied_post_ids:
                values["id"] = next_post_id
                next_post_id += 1
                remapped_post_ids += 1
            else:
                values["id"] = original_id
            post = GeneratedPost(**values)
            session.add(post)
            restored_posts.append((original_id, post))
        session.flush()
        for original_id, post in restored_posts:
            restored_post_ids[original_id] = post.id

        for row in source_rows:
            original_source_id = int(row["id"])
            values = {
                "generated_post_id": restored_post_ids[int(row["generated_post_id"])],
                "feed_item_id": int(row["feed_item_id"]),
                "source_name": str(row["source_name"]),
                "source_url": str(row["source_url"]),
                "attribution_text": row["attribution_text"],
            }
            if original_source_id in occupied_source_ids:
                values["id"] = next_source_id
                next_source_id += 1
                remapped_source_ids += 1
            else:
                values["id"] = original_source_id
            session.add(PostSource(**values))
        session.commit()
    except BaseException:
        session.rollback()
        raise
    return {
        "restored_posts": len(post_rows),
        "restored_post_sources": len(source_rows),
        "remapped_post_ids": remapped_post_ids,
        "remapped_post_source_ids": remapped_source_ids,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely publish the curated AgeCalc blog corpus.")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="Back up, delete unregistered rows, and publish curated posts.")
    action.add_argument("--restore", type=Path, help="Restore deleted rows from a verified JSON backup.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--expected-delete-posts", type=int)
    parser.add_argument("--expected-delete-post-sources", type=int)
    parser.add_argument("--confirm", action="store_true", help="Confirm the selected database write.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    from db import SessionLocal, init_db

    args = _build_parser().parse_args(argv)
    init_db()
    session = SessionLocal()
    try:
        if args.restore:
            if not args.confirm:
                raise ReleaseError("restore requires --confirm")
            report = restore_backup(session, args.restore)
        else:
            report = plan_release(session)
            if args.apply:
                if not args.confirm:
                    raise ReleaseError("apply requires --confirm")
                expected = (args.expected_delete_posts, args.expected_delete_post_sources)
                if None in expected:
                    raise ReleaseError("apply requires both expected deletion counts")
                actual = (report["delete_posts"], report["delete_post_sources"])
                if expected != actual:
                    raise ReleaseError(f"deletion count changed: expected={expected} actual={actual}")
                report = apply_release(session, backup_dir=args.backup_dir)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ReleaseError as exc:
        print(f"release aborted: {exc}", file=sys.stderr)
        raise SystemExit(1)
