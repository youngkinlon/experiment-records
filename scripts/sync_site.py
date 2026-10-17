"""Sync the Obsidian overview to the website and normalize image embeds."""

from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "长视频生成实验"


def sync():
    source = VAULT / "实验总表.md"
    text = source.read_text(encoding="utf-8")
    readme = re.sub(
        r"(\]\()([^\s)]+\.md)(\))",
        lambda m: m[1] + "长视频生成实验/" + m[2] + m[3],
        text,
    )
    homepage = re.sub(
        r"(\]\()([^\s)]+)\.md(\))",
        lambda m: m[1] + quote(unquote(m[2]), safe="/") + ".html" + m[3],
        readme,
    )
    (ROOT / "index.md").write_text(homepage, encoding="utf-8")
    (ROOT / "README.md").write_text(readme, encoding="utf-8")

    converted = 0
    for path in VAULT.glob("*.md"):
        original = path.read_text(encoding="utf-8")

        def image(match):
            nonlocal converted
            name = match[1].split("|", 1)[0]
            if not (path.parent / name).is_file():
                raise ValueError(f"Missing embedded image: {path.name}: {name}")
            converted += 1
            return "![](" + quote(name, safe="/:") + ")"

        updated = re.sub(r"!\[\[([^\]]+)\]\]", image, original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")

    checked = 0
    for path in [ROOT / "index.md", ROOT / "README.md", *VAULT.glob("*.md")]:
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            destination = path.parent / unquote(parts.path)
            if path.name == "index.md" and destination.suffix == ".html":
                destination = destination.with_suffix(".md")
            if not destination.is_file():
                raise ValueError(f"Missing link: {path.name}: {target}")
            checked += 1
    print(f"Overview synced; {converted} image embeds normalized; {checked} local links verified.")


if __name__ == "__main__":
    sync()
