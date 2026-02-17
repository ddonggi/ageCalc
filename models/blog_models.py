from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class FeedSource(Base):
    __tablename__ = "feed_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    rss_url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    site_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    items: Mapped[list["FeedItem"]] = relationship("FeedItem", back_populates="source")


class FeedItem(Base):
    __tablename__ = "feed_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("feed_sources.id"), nullable=False)
    original_title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    source: Mapped["FeedSource"] = relationship("FeedSource", back_populates="items")
    mapped_posts: Mapped[list["PostSource"]] = relationship("PostSource", back_populates="feed_item")


class GeneratedPost(Base):
    __tablename__ = "generated_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str] = mapped_column(String(500), nullable=True)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    sources: Mapped[list["PostSource"]] = relationship("PostSource", back_populates="post")


class PostSource(Base):
    __tablename__ = "post_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generated_post_id: Mapped[int] = mapped_column(ForeignKey("generated_posts.id"), nullable=False)
    feed_item_id: Mapped[int] = mapped_column(ForeignKey("feed_items.id"), nullable=False)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    attribution_text: Mapped[str] = mapped_column(String(255), nullable=True)

    post: Mapped["GeneratedPost"] = relationship("GeneratedPost", back_populates="sources")
    feed_item: Mapped["FeedItem"] = relationship("FeedItem", back_populates="mapped_posts")
