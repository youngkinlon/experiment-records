"""Plot Q02 candidate counts and fixed-group membership at three measured times."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/Q02-B-heads.csv"))
    parser.add_argument("--output-stem", type=Path,
                        default=Path("长视频生成实验/附件/Q02-候选成员更替"))
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 360 or len({(r["layer"], r["head"]) for r in rows}) != 360:
        raise ValueError("Expected 360 unique heads")
    times = (5, 15, 30)
    groups = {key: [] for key in ("persistent", "late_new", "early_lost", "returned", "middle_only", "never")}
    for row in rows:
        state = tuple(float(row[f"min_gain_pp_{t}s"]) > 10 for t in times)
        if state == (True, True, True):
            group = "persistent"
        elif not state[0] and state[2]:
            group = "late_new"
        elif state[0] and not state[2]:
            group = "early_lost"
        elif state == (True, False, True):
            group = "returned"
        elif state == (False, True, False):
            group = "middle_only"
        else:
            group = "never"
        groups[group].append(dict(layer=int(row["layer"]), head=int(row["head"]),
                                 group=group, **{f"qualified_{t}s": int(s) for t, s in zip(times, state)}))
    totals = [sum(float(r[f"min_gain_pp_{t}s"]) > 10 for r in rows) for t in times]
    assert totals == [32, 38, 25]
    assert [len(g) for g in groups.values()] == [14, 8, 15, 3, 12, 308]
    keys = list(groups)[:-1]
    matrix = [[sum(r[f"qualified_{t}s"] for r in groups[key]) for t in times] for key in keys]
    assert [sum(r[i] for r in matrix) for i in range(3)] == totals
    args.output_stem.parent.mkdir(parents=True, exist_ok=True)
    with args.output_stem.with_suffix(".csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["group", "total_heads", "qualified_5s", "qualified_15s", "qualified_30s"])
        writer.writeheader()
        for key, counts in zip(keys, matrix):
            writer.writerow(dict(group=key, total_heads=len(groups[key]),
                                 **{f"qualified_{t}s": n for t, n in zip(times, counts)}))
    head_file = args.output_stem.parent / (args.output_stem.name + "-heads.csv")
    with head_file.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(groups["persistent"][0]))
        writer.writeheader()
        writer.writerows(r for group in groups.values() for r in group)

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
        available = {f.name for f in font_manager.fontManager.ttflist}
        family = next((f for f in ("Noto Sans CJK SC", "Microsoft YaHei", "SimHei") if f in available), "DejaVu Sans")
    plt.rcParams.update({"font.family": family, "font.size": 11, "axes.unicode_minus": False,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "svg.fonttype": "none", "axes.linewidth": 1.1})
    colors = ["#2E6FA8", "#C27B32", "#788590", "#3E9490", "#8F76A0"]
    fig = plt.figure(figsize=(12, 6.1))
    grid = fig.add_gridspec(1, 2, width_ratios=(.9, 1.65), left=.07, right=.97, top=.77, bottom=.22, wspace=.7)
    ax = fig.add_subplot(grid[0, 0])
    bars = ax.bar(range(3), totals, width=.56, color=colors[0], zorder=3)
    ax.bar_label(bars, padding=6, fontsize=16, fontweight="bold")
    ax.set_xticks(range(3), [f"{t} 秒" for t in times])
    ax.set(ylim=(0, 44), ylabel="达标 head 数量", title="A  各时刻候选数量")
    ax.set_yticks([0, 10, 20, 30, 40])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="both", length=0, pad=8)
    ax.grid(axis="y", color="#E4E7EB", linewidth=.7, zorder=0)
    ax.title.set_position((.5, 1.04))

    ax = fig.add_subplot(grid[0, 1])
    labels = ["三个时间均达标（14）", "30秒新达标（8）", "30秒退出（15）",
              "15秒未达标、两端达标（3）", "仅15秒达标（12）"]
    for i, (counts, color) in enumerate(zip(matrix, colors)):
        for j, n in enumerate(counts):
            ax.add_patch(Rectangle((j-.45, i-.38), .9, .76, facecolor=color if n else "#F2F4F6",
                                   alpha=.19 if n else 1, edgecolor="white", linewidth=1.2))
            ax.text(j, i, str(n), ha="center", va="center", fontsize=17,
                    color=color if n else "#9AA2AB", fontweight="bold" if n else "normal")
    ax.set_xticks(range(3), [f"{t} 秒" for t in times])
    ax.set_yticks(range(5), labels)
    ax.set(xlim=(-.5, 2.5), ylim=(4.5, -.6), title="B  固定分组中，各时刻有多少 head 达标")
    ax.xaxis.tick_top()
    ax.tick_params(axis="both", length=0, pad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for tick, color in zip(ax.get_yticklabels(), colors):
        tick.set_color(color)
    ax.title.set_position((.5, 1.14))
    fig.text(.5, .95, "Retrieval-like 候选的成员更替", ha="center", fontsize=19, fontweight="bold")
    fig.text(.5, .875, "B方向增益 >10 个百分点 · 每个时间五个 prompt 均满足 · 不要求 top1", ha="center", color="#535C66", fontsize=11)
    fig.text(.5, .115, "5秒与30秒共同达标 17 个 = 持续达标 14 个 + 中间未达标后恢复 3 个。", ha="center", fontsize=11)
    fig.text(.5, .06, "新达标 / 退出比较5秒和30秒；每格是 head 数量，不是 attention 强度。另有308个 head 三次均未达标。", ha="center", color="#626B75", fontsize=9.5)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(args.output_stem.with_suffix("."+ext), dpi=300, facecolor="white")
    plt.close(fig)
    metadata = dict(source=str(args.input), source_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                    condition="minimum paired B gain across all five prompts >10 percentage points; no top1",
                    time_totals=totals, groups={k: len(v) for k, v in groups.items()},
                    figure_meaning="Snapshots of candidate membership; threshold crossings do not establish function emergence or loss.")
    args.output_stem.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(image=str(args.output_stem.with_suffix('.png')), counts=metadata['groups']), ensure_ascii=True))


if __name__ == "__main__":
    main()
