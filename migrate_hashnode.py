#!/usr/bin/env python3
"""
Migrate Hashnode exported posts to Jekyll/Chirpy format.

Usage:
    python migrate_hashnode.py <path-to-hashnode-export-dir>

The export dir should contain .md files directly or in a posts/ subdirectory.
Converted files are written to _posts/ in the current directory.
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone


POSTS_DIR = Path("_posts")


def parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm: dict = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")

    return fm, parts[2].strip()


def parse_hashnode_date(date_str: str) -> datetime:
    # "Sat Jan 31 2026 17:38:02 GMT+0000 (Coordinated Universal Time)"
    cleaned = re.sub(r"\s+GMT[+-]\d{4}.*$", "", date_str).strip()
    for fmt in ("%a %b %d %Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str!r}")


def fix_hashnode_images(body: str) -> str:
    # Remove align="center" and similar Hashnode-specific image attributes
    return re.sub(r'(!\[.*?\]\(https?://[^\s)]+)\s+align="[^"]*"(\))', r"\1\2", body)


def build_chirpy_frontmatter(fm: dict, date: datetime) -> str:
    title = fm.get("title", "Untitled")
    raw_tags = fm.get("tags", "")
    cover = fm.get("cover", "")

    tags = [t.strip() for t in raw_tags.split(",") if t.strip()] if raw_tags else []

    lines = [
        "---",
        f'title: "{title}"',
        f"date: {date.strftime('%Y-%m-%d %H:%M:%S +0000')}",
    ]

    if tags:
        category = tags[0].replace("-", " ").title()
        tags_yaml = ", ".join(f'"{t}"' for t in tags)
        lines.append(f"categories: [{category}]")
        lines.append(f"tags: [{tags_yaml}]")

    if cover:
        lines += ["image:", f"  path: {cover}"]

    lines.append("---")
    return "\n".join(lines)


def migrate_post(src: Path, output_dir: Path) -> None:
    content = src.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    if not fm:
        print(f"  SKIP {src.name}: no frontmatter")
        return

    date_str = fm.get("datePublished", "")
    slug = fm.get("slug", src.stem)

    try:
        date = parse_hashnode_date(date_str)
    except ValueError as e:
        print(f"  SKIP {src.name}: {e}")
        return

    body = fix_hashnode_images(body)
    new_fm = build_chirpy_frontmatter(fm, date)
    new_name = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
    out = output_dir / new_name
    out.write_text(f"{new_fm}\n\n{body}\n", encoding="utf-8")
    print(f"  OK   {src.name} -> {new_name}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"Error: {src} does not exist")
        sys.exit(1)

    posts_src = src / "posts" if (src / "posts").exists() else src
    md_files = sorted(posts_src.glob("*.md"))

    if not md_files:
        print(f"No .md files found in {posts_src}")
        sys.exit(1)

    POSTS_DIR.mkdir(exist_ok=True)
    print(f"Migrating {len(md_files)} post(s) to {POSTS_DIR}/\n")
    for f in md_files:
        migrate_post(f, POSTS_DIR)
    print("\nDone.")


if __name__ == "__main__":
    main()
