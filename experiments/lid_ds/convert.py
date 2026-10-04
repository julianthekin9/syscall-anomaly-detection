"""Конвертер LID-DS 2021 -> нативний формат проєкту.

Самостійний скрипт: не імпортує syscall_hids, лише stdlib.

Вхід:  <LID_DS_ROOT>/<сценарій>/{training,validation,test}/*.zip
       кожен zip містить <ім'я>.sc (8 колонок sysdig) та <ім'я>.json (метадані).
Вихід: <OUT>/<сценарій>/training/*.sc
       <OUT>/<сценарій>/validation/*.sc
       <OUT>/<сценарій>/test/normal/*.sc
       <OUT>/<сценарій>/test/abnormal/*.sc
       <OUT>/<сценарій>/manifest.json

Формат рядка на виході (як у eBPF-колектора): "ts_ns process syscall dir params".

Атакуючі записи: у test/abnormal пишеться лише сегмент від моменту першого
експлойту (time.exploit[].absolute) до кінця запису — один файл на запис.
Частина до експлойту за прапорцем --pre-attack-to-normal іде в test/normal.
"""

import argparse
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

SPLITS = ("training", "validation", "test")

# Колонки LID-DS 2021 (dataloader/syscall_2021.py)
LID_TS, LID_PROCESS, LID_SYSCALL, LID_DIRECTION, LID_PARAMS = 0, 3, 5, 6, 7
LID_MAX_SPLIT = 7


def convert_line(raw: str) -> tuple[int, str] | None:
    """Рядок LID-DS -> (ts_ns, рядок нативного формату). None для пошкоджених рядків."""
    fields = raw.rstrip("\n").split(" ", LID_MAX_SPLIT)
    if len(fields) <= LID_DIRECTION:
        return None
    try:
        ts_ns = int(fields[LID_TS])
    except ValueError:
        return None
    parts = [fields[LID_TS], fields[LID_PROCESS], fields[LID_SYSCALL], fields[LID_DIRECTION]]
    if len(fields) > LID_PARAMS and fields[LID_PARAMS]:
        parts.append(fields[LID_PARAMS])
    return ts_ns, " ".join(parts) + "\n"


def read_metadata(zf: zipfile.ZipFile) -> dict:
    name = next(n for n in zf.namelist() if n.endswith(".json"))
    with zf.open(name) as f:
        return json.load(f)


def exploit_start_ns(meta: dict) -> int | None:
    """Найраніший момент експлойту в наносекундах або None для нормального запису."""
    if not meta.get("exploit"):
        return None
    times = [e["absolute"] for e in meta.get("time", {}).get("exploit", []) if "absolute" in e]
    if not times:
        return None
    return int(min(times) * 1e9)


def convert_recording(zip_path: Path, split: str, out_dir: Path, pre_to_normal: bool) -> dict:
    """Конвертує один zip потоково (без завантаження .sc у пам'ять)."""
    name = zip_path.stem
    info: dict = {"source": str(zip_path), "split": split}

    with zipfile.ZipFile(zip_path) as zf:
        meta = read_metadata(zf)
        attack_ns = exploit_start_ns(meta)
        info["exploit_start_ns"] = attack_ns
        info["exploit_name"] = meta.get("exploit_name") if attack_ns is not None else None

        if attack_ns is not None and split != "test":
            info["status"] = "skipped: exploit outside test split"
            return info
        if meta.get("exploit") and attack_ns is None:
            info["status"] = "skipped: exploit=true without exploit time"
            return info

        if attack_ns is None:
            sub = "test/normal" if split == "test" else split
            targets = {"main": out_dir / sub / f"{name}.sc"}
        else:
            targets = {"attack": out_dir / "test/abnormal" / f"{name}.sc"}
            if pre_to_normal:
                targets["pre"] = out_dir / "test/normal" / f"{name}__pre.sc"

        for p in targets.values():
            p.parent.mkdir(parents=True, exist_ok=True)
        handles = {k: open(p, "w", encoding="utf-8") for k, p in targets.items()}
        counts = dict.fromkeys(targets, 0)
        bad = 0
        try:
            sc_name = next(n for n in zf.namelist() if n.endswith(".sc"))
            with zf.open(sc_name) as raw:
                for raw_line in io.TextIOWrapper(raw, encoding="utf-8", errors="ignore"):
                    converted = convert_line(raw_line)
                    if converted is None:
                        bad += 1
                        continue
                    ts_ns, line = converted
                    if attack_ns is None:
                        key = "main"
                    elif ts_ns >= attack_ns:
                        key = "attack"
                    elif pre_to_normal:
                        key = "pre"
                    else:
                        continue
                    handles[key].write(line)
                    counts[key] += 1
        finally:
            for h in handles.values():
                h.close()

    # Порожні сегменти не залишаємо
    for key, path in targets.items():
        if counts[key] == 0:
            path.unlink()
    info["outputs"] = {k: str(targets[k].relative_to(out_dir)) for k in targets if counts[k]}
    info["lines"] = {k: c for k, c in counts.items() if c}
    info["bad_lines"] = bad
    info["status"] = "ok" if any(counts.values()) else "empty"
    return info


def convert_scenario(scenario_dir: Path, out_root: Path, pre_to_normal: bool, limit: int | None) -> dict:
    out_dir = out_root / scenario_dir.name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    records = []
    for split in SPLITS:
        zips = sorted((scenario_dir / split).glob("*.zip"))
        if limit is not None:
            zips = zips[:limit]
        for i, zp in enumerate(zips, 1):
            try:
                records.append(convert_recording(zp, split, out_dir, pre_to_normal))
            except (zipfile.BadZipFile, StopIteration, json.JSONDecodeError, KeyError) as e:
                records.append({"source": str(zp), "split": split, "status": f"error: {e!r}"})
            print(f"\r{scenario_dir.name}/{split}: {i}/{len(zips)}", end="", file=sys.stderr)
        print(file=sys.stderr)

    summary = {
        "scenario": scenario_dir.name,
        "pre_attack_to_normal": pre_to_normal,
        "recordings": records,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description="LID-DS 2021 -> нативний формат проєкту")
    p.add_argument("lid_ds_root", type=Path, help="Тека з розпакованими сценаріями LID-DS 2021")
    p.add_argument("out_root", type=Path, help="Куди писати сконвертований датасет")
    p.add_argument("--scenarios", nargs="*", default=None, help="Лише ці сценарії (за замовчуванням усі)")
    p.add_argument("--pre-attack-to-normal", action="store_true",
                   help="Частину атакуючого запису до експлойту писати в test/normal")
    p.add_argument("--limit", type=int, default=None, help="Не більше N записів на спліт (для швидкої перевірки)")
    args = p.parse_args()

    scenarios = sorted(d for d in args.lid_ds_root.iterdir() if (d / "training").is_dir())
    if args.scenarios:
        scenarios = [d for d in scenarios if d.name in args.scenarios]
    if not scenarios:
        sys.exit(f"Не знайдено сценаріїв у {args.lid_ds_root}")

    for sc in scenarios:
        s = convert_scenario(sc, args.out_root, args.pre_attack_to_normal, args.limit)
        statuses: dict[str, int] = {}
        for r in s["recordings"]:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        print(f"{sc.name}: {statuses}")


if __name__ == "__main__":
    main()