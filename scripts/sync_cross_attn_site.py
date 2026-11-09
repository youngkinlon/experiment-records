"""Export the selected Obsidian notes to GitHub Pages without modifying the vault."""

from __future__ import annotations

import hashlib
import html
import json
import os
import csv
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "长视频生成实验"
PAGES = {
    "Q5：.md": ("docs/Q05-ca-residual-scaling.md", "CA Residual Scaling"),
    "Q6：.md": ("docs/Q06-sa-ca-alignment.md", "SA–CA Write Alignment over Time"),
    "Q7.md": ("docs/Q07-history-ca-query.md", "History-Dependent CA Query Intervention"),
    "Self-Forcing inference 过程详解：.md": ("docs/self-forcing-inference.md", "Self-Forcing inference 过程详解"),
}


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def strip_front_matter(text):
    return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S).strip()


def front_matter(title):
    return "---\nlayout: default\ntitle: " + json.dumps(title, ensure_ascii=False) + "\n---\n\n"


def normalize_math(text):
    """Use kramdown's native double-dollar math delimiters, including inline math."""
    parts = re.split(r"(```.*?```|`[^`\n]+`)", text, flags=re.S)
    pattern = re.compile(r"\$\$(.*?)\$\$|\\\[(.*?)\\\]|\\\((.*?)\\\)|(?<!\$)\$(?!\$)([^$]+?)\$(?!\$)", re.S)
    for index in range(0, len(parts), 2):
        source = parts[index]

        def replace(match):
            body = next(group for group in match.groups() if group is not None).strip()
            first = source.rfind("\n", 0, match.start()) + 1
            last = source.find("\n", match.end())
            last = len(source) if last < 0 else last
            standalone = not source[first:match.start()].strip() and not source[match.end():last].strip()
            display = match.group(2) is not None or (match.group(1) is not None and standalone)
            return "\n\n$$\n" + body + "\n$$\n\n" if display else "$$" + body + "$$"

        parts[index] = pattern.sub(replace, source)
    return "".join(parts)


class Exporter:
    def __init__(self):
        self.assets = {}
        self.pages = []

    def asset(self, source, destination_page):
        source = source.resolve()
        if not source.is_file() or not source.is_relative_to(VAULT.resolve()):
            raise ValueError(f"Missing or out-of-vault asset: {source.name}")
        digest = sha256(source)
        if digest not in self.assets:
            stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", source.relative_to(VAULT).with_suffix("").as_posix()).strip("-")[-90:]
            target = ROOT / "assets" / "cross-attn" / f"{stem}-{digest[:10]}{source.suffix.lower()}"
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or sha256(target) != digest:
                shutil.copy2(source, target)
            assert target.stat().st_size < 100 * 1024**2, "Asset exceeds GitHub's normal Git file limit"
            self.assets[digest] = dict(source=source.relative_to(ROOT).as_posix(),
                                       output=target.relative_to(ROOT).as_posix(), sha256=digest,
                                       bytes=target.stat().st_size)
        target = ROOT / self.assets[digest]["output"]
        return Path(os.path.relpath(target, destination_page.parent)).as_posix()

    def link(self, target, source_page, destination_page):
        parts = urlsplit(target)
        if parts.scheme or parts.netloc or not parts.path:
            return target
        local = (source_page.parent / unquote(parts.path)).resolve()
        if local.suffix.lower() == ".md":
            output = ROOT / PAGES[local.name][0] if local.name in PAGES else local
            if not output.is_file() and local.name not in PAGES:
                raise ValueError(f"Missing note target: {local.name}")
            relative = Path(os.path.relpath(output.with_suffix(".html"), destination_page.parent)).as_posix()
            return quote(relative, safe="/:") + ("#" + parts.fragment if parts.fragment else "")
        return self.asset(local, destination_page)

    def media(self, raw, source_page, destination_page, alt="Experiment figure"):
        parts = raw.split("|", 1)
        name = unquote(parts[0])
        width = parts[1] if len(parts) == 2 and parts[1].isdigit() else None
        source = source_page.parent / name
        url = self.asset(source, destination_page)
        if source.suffix.lower() in {".mp4", ".webm", ".mov", ".ogv"}:
            return f'<video controls preload="metadata" playsinline src="{url}">Your browser does not support this video. <a href="{url}">Download the video</a>.</video>'
        if source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
            size = f' width="{width}"' if width else ""
            return f'<img src="{url}" alt="{html.escape(alt, quote=True)}" loading="lazy"{size} />'
        return f'<a href="{url}">{html.escape(source.name)}</a>'

    def convert(self, source_page, destination_page):
        original = source_page.read_text(encoding="utf-8")
        text = strip_front_matter(original)
        if source_page.name == "Q5：.md":
            text = text.replace("基本效果不明显，无论减弱还是增强 观察到明确的生成质量或连续性改善，",
                                "基本效果不明显：无论减弱还是增强，均未观察到明确的生成质量或连续性改善。")
        if source_page.name == "Q7.md":
            text = text.replace("baseline(7个chunk+完整当前块)", "baseline（6个历史 chunk + 当前块，共7个 chunk）")
        text = re.sub(r"!\[\[([^\]]+)\]\]", lambda m: self.media(m[1], source_page, destination_page), text)
        text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                      lambda m: self.media(m[2], source_page, destination_page, m[1] or "Inference diagram"), text)

        def wiki(match):
            target, *alias = match[1].split("|", 1)
            target = target if Path(target).suffix else target + ".md"
            url = self.link(target, source_page, destination_page)
            return f"[{alias[0] if alias else Path(target).stem}]({url})"

        text = re.sub(r"(?<!!)\[\[([^\]]+)\]\]", wiki, text)
        text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)",
                      lambda m: f"[{m[1]}]({self.link(m[2], source_page, destination_page)})", text)
        lines, result, in_details = text.splitlines(), [], False
        for line in lines:
            callout = re.match(r">\s*\[![^\]]+\]([-+])?\s*(.*)", line)
            if callout:
                if in_details:
                    result += ["</div>", "</details>", ""]
                result += ["", "<details>", f"<summary>{html.escape(callout[2] or 'Details')}</summary>",
                           '<div class="callout-body" markdown="1">', ""]
                in_details = True
                continue
            if in_details and line.startswith(">"):
                result.append(re.sub(r"^> ?", "", line))
            else:
                if in_details:
                    result += ["", "</div>", "</details>", ""]
                    in_details = False
                result.append(line)
        if in_details:
            result += ["", "</div>", "</details>"]
        text = normalize_math("\n".join(result))
        blocks = text.split("\n\n")
        text = "\n\n".join("```text\n"+b+"\n```" if "↓" in b and "$$" not in b else b for b in blocks)
        assert "![[" not in text and not re.search(r"[A-Z]:[\\/]", text)
        self.pages.append(dict(source=source_page.relative_to(ROOT).as_posix(),
                               output=destination_page.relative_to(ROOT).as_posix(), source_sha256=sha256(source_page)))
        return text


def overview():
    text = strip_front_matter((VAULT / "实验总表.md").read_text(encoding="utf-8"))
    before, cross = re.split(r"^## Cross-Attention Experiments\s*$", text, maxsplit=1, flags=re.M)
    candidates = {key: [] for key in ["Q05", "Q06", "Q07"]}
    for line in cross.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] in candidates:
            assert len(cells) == 7
            candidates[cells[0]].append(cells)
    rows = []
    for key, options in candidates.items():
        assert options, key
        row = options[0]
        if key == "Q05":
            row = next((r for r in options if not re.search(r"[\u4e00-\u9fff]", r[3]+r[4])), None)
            if row is None:
                # Use the English translation already reviewed in the discussion.
                row = [key, "CA Residual Scaling", options[0][2],
                       "Increase or decrease cross-attention residual writes within specified time windows. Compare CA write magnitude relative to self-attention and the residual stream across early and late stages.",
                       "No consistent late-stage increase in relative CA write magnitude was observed in the tested sample. Neither increasing nor decreasing CA residual strength produced a clear improvement in video quality or continuity.",
                       "All layers were scaled together, so layer-specific effects were not isolated. Interventions on selected layers remain untested.", ""]
            row = row.copy()
            row[-1] = "Explore self-attn–cross-attn write alignment; see Q06."
        else:
            row = row.copy()
            row[-1] = "Identify the underlying cause."
        source_name = {"Q05":"Q5：.md", "Q06":"Q6：.md", "Q07":"Q7.md"}[key]
        output, title = PAGES[source_name]
        row[1] = f"[{title}]({output})"
        rows.append("| " + " | ".join(row) + " |")
    before = before.replace("这些主要是诊断性实验，针对是self-attn", "These are diagnostic experiments focused on self-attention.")
    header = "| ID | Experiment | Hypothesis / Question | Setup and Comparison | Preliminary Results | Current Assessment / Limitations | Next Steps |\n| --- | --- | --- | --- | --- | --- | --- |"
    result = before.strip()+"\n\n## Cross-Attention Experiments\n\n"+header+"\n"+"\n".join(rows)
    result += "\n\n## Reference\n\n[Self-Forcing inference 过程详解](docs/self-forcing-inference.md)\n"

    def links(match):
        label, target = match[1], match[2]
        if target.startswith("docs/"):
            resolved = target
        else:
            resolved = "长视频生成实验/" + target
        return f"[{label}]({quote(unquote(resolved), safe='/:')})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+\.md)\)", links, result)


def validate(paths):
    checked = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        links = re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", text)
        links += re.findall(r'(?:src|href)="([^"]+)"', text)
        for target in links:
            parts = urlsplit(html.unescape(target))
            if parts.scheme or parts.netloc or not parts.path:
                continue
            destination = (path.parent / unquote(parts.path)).resolve()
            if destination.suffix == ".html" and not destination.exists():
                destination = destination.with_suffix(".md")
            assert destination.is_relative_to(ROOT.resolve()) and destination.is_file(), (path.name, target)
            checked += 1
        assert "![[" not in text
    return checked


def main():
    exporter = Exporter()
    outputs = []
    for name, (destination, title) in PAGES.items():
        source, target = VAULT/name, ROOT/destination
        text = exporter.convert(source, target)
        if not re.search(r"^# ", text, re.M):
            text = f"# {title}\n\n" + text
        target.write_text(front_matter(title)+text.strip()+"\n", encoding="utf-8")
        outputs.append(target)
    summary = overview()
    readme = ROOT/"README.md"
    readme.write_text(front_matter("Experiment Overview")+summary+"\n", encoding="utf-8")
    homepage = re.sub(r"(\]\()([^\s)]+)\.md(\))", lambda m:m[1]+m[2]+".html"+m[3], summary)
    (ROOT/"index.md").write_text(front_matter("Experiment Overview")+homepage+"\n", encoding="utf-8")
    records = []
    for line in summary.splitlines():
        if not re.match(r"\| Q0[1-7] \|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[0] in {"Q05", "Q06", "Q07"}:
            cells[2], cells[3] = cells[3], cells[2]
        records.append(cells)
    assert len(records) == 7
    with (ROOT/"experiments.csv").open("w",encoding="utf-8-sig",newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["编号", "实验", "目的", "假设", "当前结论", "局限", "后续实验"])
        writer.writerows(records)
    outputs += [readme, ROOT/"index.md"]
    checked = validate(outputs)
    manifest = dict(pages=exporter.pages, assets=list(exporter.assets.values()),
                    overview_source_sha256=sha256(VAULT/"实验总表.md"),
                    checked_links=checked, notes_modified=False,
                    summary_selection="One English Q05 row; first linked Q06/Q07 rows; concise next steps retained.")
    (ROOT/"data/cross-attn-source-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(pages=len(exporter.pages),assets=len(exporter.assets),checked_links=checked,
                          total_asset_bytes=sum(a["bytes"] for a in exporter.assets.values())),ensure_ascii=False))


if __name__ == "__main__":
    main()
