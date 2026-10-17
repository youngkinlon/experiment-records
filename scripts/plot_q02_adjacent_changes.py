"""List and visualize additions/exits separately for 5→15 and 15→30 seconds."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/Q02-B-heads.csv"))
    parser.add_argument("--output-stem", type=Path, default=Path("长视频生成实验/附件/Q02-相邻时间成员进出"))
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    by_head = {(int(r["layer"]), int(r["head"])): r for r in rows}
    if len(by_head) != 360 or len(rows) != 360:
        raise ValueError("Expected 360 unique heads")
    times = (5, 15, 30)
    gains = {head: {t: float(row[f"min_gain_pp_{t}s"]) for t in times} for head, row in by_head.items()}
    sets = {t: {head for head in by_head if gains[head][t] > 10} for t in times}
    summaries, records, groups = [], [], []
    for start, end in ((5, 15), (15, 30)):
        new = sorted(sets[end] - sets[start])
        exited = sorted(sets[start] - sets[end])
        retained = sorted(sets[start] & sets[end])
        summaries.append(dict(start_seconds=start, end_seconds=end, start_count=len(sets[start]),
                              new_count=len(new), exit_count=len(exited), retained_count=len(retained),
                              end_count=len(sets[end])))
        assert len(sets[start]) - len(exited) + len(new) == len(sets[end])
        groups.append(dict(start=start, end=end, new=new, exited=exited, retained=retained))
        for head in sorted(by_head):
            before, after = head in sets[start], head in sets[end]
            status = ("retained" if before else "new") if after else ("exit" if before else "neither")
            records.append(dict(start_seconds=start, end_seconds=end, layer=head[0], head=head[1],
                                status=status, start_qualified=int(before), end_qualified=int(after),
                                **{f"min_gain_pp_{t}s": gains[head][t] for t in times}))
    assert [(r["new_count"], r["exit_count"], r["retained_count"]) for r in summaries] == [(16, 10, 22), (7, 20, 18)]
    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_stem.with_suffix(".csv"), summaries)
    write_csv(args.output_stem.parent / (args.output_stem.name + "-全部head.csv"), records)
    write_csv(args.output_stem.parent / (args.output_stem.name + "-新增退出名单.csv"),
              [r for r in records if r["status"] in ("new", "exit")])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Rectangle
    font = Path("C:/Windows/Fonts/msyh.ttc")
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        family = font_manager.FontProperties(fname=str(font)).get_name()
    else:
        installed = {f.name for f in font_manager.fontManager.ttflist}
        family = next((name for name in ("Noto Sans CJK SC", "Microsoft YaHei", "SimHei") if name in installed), "DejaVu Sans")
    plt.rcParams.update({"font.family": family, "font.size": 10, "axes.unicode_minus": False,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 12.2), gridspec_kw={"wspace": .68})
    fig.subplots_adjust(left=.15, right=.96, top=.83, bottom=.11)
    max_rows = max(len(g["new"]) + len(g["exited"]) + 3 for g in groups)
    for ax, group in zip(axes, groups):
        start, end = group["start"], group["end"]
        labels, positions = [], []
        y = 0
        for key, heading, color in (("new", "新增", "#AD6B27"), ("exited", "退出", "#646F7C")):
            heads = group[key]
            ax.text(-.72, y, f"{heading} {len(heads)} 个", ha="right", va="center", fontweight="bold", color=color, fontsize=11)
            ax.axhline(y+.48, color="#DCE1E6", linewidth=.7)
            y += 1
            for head in heads:
                labels.append(f"L{head[0]} H{head[1]}")
                positions.append(y)
                for x, time in enumerate((start, end)):
                    value = gains[head][time]
                    qualified = value > 10
                    ax.add_patch(Rectangle((x-.46, y-.39), .92, .78,
                                           facecolor="#D7E6F2" if qualified else "#F2F4F6", edgecolor="white"))
                    displayed = f"{value:.4f}" if 0 < abs(value-10) < .005 else f"{value:.2f}"
                    ax.text(x, y, displayed, ha="center", va="center", fontsize=10,
                            color="#275E8D" if qualified else "#737D87", fontweight="bold" if qualified else "normal")
                y += 1
            y += .8
        ax.set_xlim(-.55, 1.55)
        ax.set_ylim(max_rows-.2, -1.2)
        ax.set_xticks([0, 1], [f"{start} 秒", f"{end} 秒"])
        ax.xaxis.tick_top()
        ax.set_yticks(positions, labels)
        ax.tick_params(axis="both", length=0, pad=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(f"{start} → {end} 秒\n新增 {len(group['new'])} · 退出 {len(group['exited'])} · 保留 {len(group['retained'])}",
                     fontsize=13, pad=31)
    fig.suptitle("Retrieval-like 候选：逐段查看哪些 head 加入、哪些退出", y=.985, fontsize=17, fontweight="bold")
    fig.text(.5, .942, "5秒 32 个 − 退出10个 + 新增16个 = 15秒 38 个", ha="center", fontsize=12)
    fig.text(.5, .914, "15秒 38 个 − 退出20个 + 新增7个 = 30秒 25 个", ha="center", fontsize=12)
    fig.text(.5, .063, "格内数字：五个 prompt 中的最小 B attention 增益（百分点）。浅蓝色：>10pp 达标；灰白色：未达标。", ha="center", fontsize=10)
    fig.text(.5, .037, "不要求 top1；按精确值判断，显示值作舍入，临近10pp时增加精度。退出指退出候选集合，不是删除 KV 或证明功能消失。", ha="center", fontsize=9, color="#626B75")
    for extension in ("png", "pdf", "svg"):
        fig.savefig(args.output_stem.with_suffix("."+extension), dpi=300, facecolor="white")
    plt.close(fig)
    metadata = dict(source=str(args.input), source_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                    threshold="minimum B gain across all five prompts >10pp; no top1", intervals=summaries,
                    groups=[dict(start=g["start"], end=g["end"], new=g["new"], exited=g["exited"], retained=g["retained"]) for g in groups])
    args.output_stem.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summaries, ensure_ascii=True))


if __name__ == "__main__":
    main()
