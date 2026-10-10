"""Копія test-сплітів сконвертованих сценаріїв LID-DS з обрізаними атакуючими сегментами.

convert.py позначає атакою все від експлойта до кінця запису. Запис з атакою LID-DS зупиняє через
випадкові 5–15 с після виходу контейнера атакувальника (lid_ds/core/scenario.py, _recording),
тому в кінці кожного атакуючого сегмента лежить 5–15 с звичайного трафіку з міткою «атака».

--tail-sec T відкидає останні T секунд кожного файлу test/abnormal. T = 5 прибирає лише
гарантовану норму; більше T прибирає більше норми, але в записах з коротким хвостом зрізає й
кінець атаки, а сегменти коротші за T зникають повністю (файл не записується, рахується в dropped).
--attack-max-sec A залишає лише перші A секунд від першого рядка (= моменту експлойта).
Обидва обмеження можна поєднувати. test/normal переноситься без змін; train/validation не
копіюються: модель не перенавчається, оцінюється лише test.

    python experiments/lid_ds/trim_attacks.py DATASET_LIDDS --out DATASET_LIDDS_tail10 --tail-sec 10
    python experiments/lid_ds/trim_attacks.py DATASET_LIDDS --out DATASET_LIDDS_a20 --attack-max-sec 20 --scenarios CVE-2012-2122
    hids-eval --service CVE-2012-2122 --checkpoint <модель>.pt --eval-test-split --dataset_root DATASET_LIDDS_tail10

Тільки stdlib, код проєкту не імпортується. У кожному сценарії пишеться trim_manifest.json:
параметри, тривалість сегмента і кількість рядків до/після для кожного файлу.
"""

import argparse
import json
import os
import shutil
import statistics
import sys
from pathlib import Path


def link_or_copy(src: Path, dst: Path) -> None:
    """Жорстке посилання (без копіювання даних), якщо ФС не дозволяє — копія."""
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def first_last_ts(path: Path) -> tuple[int, int]:
    """Час першого й останнього рядка без читання всього файлу."""
    with open(path, "rb") as f:
        first = f.readline()
        size = f.seek(0, os.SEEK_END)
        f.seek(max(0, size - 65536))
        last = f.read().rstrip(b"\n").rsplit(b"\n", 1)[-1]
    return int(first.split(b" ", 1)[0]), int(last.split(b" ", 1)[0])


def trim_file(src: Path, dst: Path, attack_max_sec: float | None, tail_sec: float) -> dict:
    """Залишає рядки в [t0, min(t0 + A, t_last - T)]; файл читається потоково.
    Якщо не лишилось жодного рядка, dst не створюється."""
    t0, t_last = first_last_ts(src)
    end = t_last - int(tail_sec * 1e9)
    if attack_max_sec is not None:
        end = min(end, t0 + int(attack_max_sec * 1e9))
    total = kept = 0
    with open(src, "rb") as f, open(dst, "wb") as g:
        for line in f:
            total += 1
            if int(line.split(b" ", 1)[0]) <= end:
                g.write(line)
                kept += 1
    if kept == 0:
        dst.unlink()
    return {"lines": total, "kept": kept, "duration_sec": round((t_last - t0) / 1e9, 3)}


def trim_scenario(scenario_dir: Path, out_dir: Path, attack_max_sec: float | None, tail_sec: float) -> dict | None:
    test = scenario_dir / "test"
    abnormal = sorted((test / "abnormal").glob("*.sc"))
    if not abnormal:
        return None
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "test" / "abnormal").mkdir(parents=True)
    (out_dir / "test" / "normal").mkdir(parents=True)

    normal = sorted((test / "normal").glob("*.sc"))
    for p in normal:
        link_or_copy(p, out_dir / "test" / "normal" / p.name)

    files = {}
    for i, p in enumerate(abnormal, 1):
        files[p.name] = trim_file(p, out_dir / "test" / "abnormal" / p.name, attack_max_sec, tail_sec)
        print(f"\r{scenario_dir.name}: {i}/{len(abnormal)}", end="", file=sys.stderr)
    print(file=sys.stderr)

    durations = [f["duration_sec"] for f in files.values()]
    summary = {
        "scenario": scenario_dir.name,
        "attack_max_sec": attack_max_sec,
        "tail_sec": tail_sec,
        "normal_files": len(normal),
        "abnormal_files": len(files),
        "abnormal_lines_before": sum(f["lines"] for f in files.values()),
        "abnormal_lines_after": sum(f["kept"] for f in files.values()),
        "files_trimmed": sum(0 < f["kept"] < f["lines"] for f in files.values()),
        "files_dropped": sum(f["kept"] == 0 for f in files.values()),
        "duration_deciles_sec": [round(x, 1) for x in statistics.quantiles(durations, n=10)] if len(durations) > 1 else durations,
        "files": files,
    }
    with open(out_dir / "trim_manifest.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dataset_root", type=Path, help="Root with converted scenarios (output of convert.py)")
    p.add_argument("--out", type=Path, required=True, help="Where to write the trimmed test copies")
    p.add_argument("--tail-sec", type=float, default=0.0,
                   help="Drop the last T seconds of each attack segment (LID-DS stops recording 5-15 s after the attack)")
    p.add_argument("--attack-max-sec", type=float, default=None,
                   help="Keep at most this many seconds of each attack segment after the exploit")
    p.add_argument("--scenarios", nargs="*", default=None, help="Only these scenarios (default: all)")
    args = p.parse_args()

    if args.tail_sec <= 0 and args.attack_max_sec is None:
        p.error("set --tail-sec and/or --attack-max-sec")
    if args.out.resolve() == args.dataset_root.resolve():
        p.error("--out must differ from dataset_root: trimming must not overwrite the source data")

    dirs = sorted(d for d in args.dataset_root.iterdir() if d.is_dir() and (d / "test").is_dir())
    if args.scenarios:
        dirs = [d for d in dirs if d.name in args.scenarios]
    for d in dirs:
        s = trim_scenario(d, args.out / d.name, args.attack_max_sec, args.tail_sec)
        if s is None:
            print(f"{d.name}: no test/abnormal, skipped")
            continue
        share = s["abnormal_lines_after"] / max(s["abnormal_lines_before"], 1)
        print(f"{d.name}: abnormal lines {s['abnormal_lines_before']:,} -> {s['abnormal_lines_after']:,} "
              f"({share:.0%}), trimmed {s['files_trimmed']}, dropped {s['files_dropped']} of {s['abnormal_files']} files, "
              f"segment duration deciles, s: {s['duration_deciles_sec']}")


if __name__ == "__main__":
    main()
