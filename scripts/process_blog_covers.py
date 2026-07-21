from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageOps


TARGET_SIZE = (1200, 630)


def process_cover(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        image = ImageOps.fit(
            original.convert("RGB"),
            TARGET_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        image.save(
            destination,
            format="JPEG",
            quality=86,
            optimize=True,
            progressive=True,
            subsampling="4:2:0",
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create optimized 1200x630 covers from generated PNG files.")
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args(argv)

    from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS

    for slug in BLOG_ARTICLE_BLUEPRINTS:
        source = args.source_dir / f"{slug}.png"
        destination = args.output_dir / f"{slug}.jpg"
        process_cover(source, destination)
        print(f"processed {slug}: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
