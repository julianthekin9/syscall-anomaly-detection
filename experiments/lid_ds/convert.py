"""Конвертер LID-DS 2021 -> нативний формат проєкту.

Самостійний скрипт: не імпортує syscall_hids, лише stdlib.

Вхід:  zip-архів сценарію (як його віддає LID-DS) або тека з розпакованими сценаріями;
       всередині <сценарій>/{training,validation,test}/**/*.zip,
       кожен zip-запис містить <ім'я>.sc (8 колонок sysdig) та <ім'я>.json (метадані).
       Теки __MACOSX і файли "._*" ігноруються.
Вихід: <OUT>/<сценарій>/training/*.sc
       <OUT>/<сценарій>/validation/*.sc
       <OUT>/<сценарій>/test/normal/*.sc
       <OUT>/<сценарій>/test/abnormal/*.sc
       <OUT>/<сценарій>/manifest.json

Формат рядка на виході (як у eBPF-колектора): "ts_ns process syscall dir params".

Атакуючі записи: у test/abnormal пишеться лише сегмент від моменту першого
експлойту (time.exploit[].absolute) до кінця запису — один файл на запис.
Частина атакуючого запису до експлойту відкидається. У test/normal потрапляють
лише записи з теки test/normal LID-DS без експлойту.
"""

import argparse
import io
import json
import random
import shutil
import sys
import zipfile
from contextlib import ExitStack
from pathlib import Path
from typing import Callable, NamedTuple

SPLITS = ("training", "validation", "test")


class Recording(NamedTuple):
    """Один zip-запис LID-DS незалежно від того, звідки він узявся (тека чи архів сценарію)."""
    scenario: str
    split: str
    name: str
    folder: str  # тека, в якій лежить zip (у test: normal або normal_and_attack)
    source: str  # для manifest.json
    open: Callable[[], zipfile.ZipFile]

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


def _is_junk(path_parts: list[str]) -> bool:
    """Службові файли macOS: тека __MACOSX та AppleDouble-файли "._*"."""
    return "__MACOSX" in path_parts or path_parts[-1].startswith("._")


def _scan_dir(root: Path) -> list[Recording]:
    """Тека з розпакованими сценаріями: <root>/<сценарій>/{training,validation,test}/**/*.zip."""
    found: list[Recording] = []
    for scenario_dir in sorted(d for d in root.iterdir() if (d / "training").is_dir()):
        for split in SPLITS:
            # test у LID-DS 2021 розбитий на test/normal і test/normal_and_attack, тому rglob
            for zp in sorted((scenario_dir / split).rglob("*.zip")):
                if _is_junk(list(zp.parts)):
                    continue
                found.append(Recording(
                    scenario_dir.name, split, zp.stem, zp.parent.name, str(zp),
                    lambda zp=zp: zipfile.ZipFile(zp),
                ))
    return found


def _scan_archive(archive: zipfile.ZipFile, archive_path: Path) -> list[Recording]:
    """Zip-архив сценарію, як його віддає LID-DS: <сценарій>/{training,validation,test}/**/*.zip.

    Внутрішні zip-и записів читаються в пам'ять по одному (кілька МБ кожен),
    на диск нічого не розпаковується."""
    found: list[Recording] = []
    for info in sorted(archive.infolist(), key=lambda i: i.filename):
        parts = info.filename.split("/")
        if info.is_dir() or not parts[-1].endswith(".zip") or _is_junk(parts):
            continue
        split_idx = next((i for i, p in enumerate(parts) if p in SPLITS), None)
        if split_idx is None or split_idx == 0:
            continue
        found.append(Recording(
            parts[split_idx - 1], parts[split_idx], Path(parts[-1]).stem, parts[-2],
            f"{archive_path}!{info.filename}",
            lambda info=info: zipfile.ZipFile(io.BytesIO(archive.read(info))),
        ))
    return found


def convert_recording(rec: Recording, out_dir: Path) -> dict:
    """Конвертує один zip-запис потоково (без завантаження .sc у пам'ять)."""
    name, split = rec.name, rec.split
    info: dict = {"source": rec.source, "split": split}

    with rec.open() as zf:
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
        if split == "test" and attack_ns is None and rec.folder != "normal":
            info["status"] = f"skipped: no exploit in test/{rec.folder}"
            return info

        if attack_ns is None:
            sub = "test/normal" if split == "test" else split
            targets = {"main": out_dir / sub / f"{name}.sc"}
        else:
            targets = {"attack": out_dir / "test/abnormal" / f"{name}.sc"}

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
                    else:
                        continue  # частина до експлойту не використовується
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


def balance_test(out_dir: Path, records: list[dict], seed: int) -> dict:
    """Вирівнює test за кількістю рядків: normal ≈ abnormal.

    Нормальні записи test/normal перемішуються з
    фіксованим seed і проходяться жадібно: файл лишається, якщо з ним сума рядків
    ближча до суми атакуючих рядків, ніж без нього, інакше видаляється з диска.
    Записи не обрізаються, щоб кожен файл лишався природною сесією.
    Видалені файли позначаються в манифесті полем "balanced_out" і відтворюються
    повторною конвертацією з тим самим seed."""
    test = [r for r in records if r.get("split") == "test"]
    target = sum(r.get("lines", {}).get("attack", 0) for r in test)
    normal = [r for r in test if "main" in r.get("outputs", {})]
    before = sum(r["lines"]["main"] for r in normal)

    random.Random(seed).shuffle(normal)
    kept_lines = kept_files = 0
    for r in normal:
        n = r["lines"]["main"]
        if kept_lines + n / 2 <= target:  # з файлом ближче до цілі, ніж без нього
            kept_lines += n
            kept_files += 1
        else:
            rel = r["outputs"].pop("main")
            (out_dir / rel).unlink()
            r["balanced_out"] = rel

    return {
        "seed": seed,
        "attack_lines": target,
        "normal_lines_before": before,
        "normal_lines_after": kept_lines,
        "normal_files_before": len(normal),
        "normal_files_after": kept_files,
    }


def write_manifest(out_dir: Path, summary: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def rebalance_existing(scenario_dir: Path, seed: int) -> dict:
    """Балансування вже сконвертованого сценарію за його manifest.json, без повторної конвертації."""
    with open(scenario_dir / "manifest.json", encoding="utf-8") as f:
        summary = json.load(f)
    if "test_balance" in summary:
        sys.exit(f"{scenario_dir}: test уже збалансований ({summary['test_balance']})")
    summary["test_balance"] = balance_test(scenario_dir, summary["recordings"], seed)
    write_manifest(scenario_dir, summary)
    return summary


def convert_scenario(
    scenario: str, recordings: list[Recording], out_root: Path, limit: int | None,
    balance_seed: int | None,
) -> dict:
    out_dir = out_root / scenario
    if out_dir.exists():
        shutil.rmtree(out_dir)
    records = []
    for split in SPLITS:
        recs = [r for r in recordings if r.split == split]
        if limit is not None:
            recs = recs[:limit]
        for i, rec in enumerate(recs, 1):
            try:
                records.append(convert_recording(rec, out_dir))
            except (zipfile.BadZipFile, StopIteration, json.JSONDecodeError, KeyError) as e:
                records.append({"source": rec.source, "split": split, "status": f"error: {e!r}"})
            print(f"\r{scenario}/{split}: {i}/{len(recs)}", end="", file=sys.stderr)
        print(file=sys.stderr)

    summary = {
        "scenario": scenario,
        "recordings": records,
    }
    if balance_seed is not None:
        summary["test_balance"] = balance_test(out_dir, records, balance_seed)
    write_manifest(out_dir, summary)
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description="LID-DS 2021 -> нативний формат проєкту")
    p.add_argument("inputs", type=Path, nargs="*",
                   help="Zip-архіви сценаріїв LID-DS 2021 та/або теки з розпакованими сценаріями")
    p.add_argument("--out", type=Path, help="Куди писати сконвертований датасет")
    p.add_argument("--scenarios", nargs="*", default=None, help="Лише ці сценарії (за замовчуванням усі)")
    p.add_argument("--limit", type=int, default=None, help="Не більше N записів на спліт (для швидкої перевірки)")
    p.add_argument("--balance-test", action="store_true",
                   help="Вирівняти test: сумарна кількість рядків normal ≈ abnormal (зайві normal-файли видаляються)")
    p.add_argument("--seed", type=int, default=0, help="Seed для --balance-test та --rebalance")
    p.add_argument("--rebalance", type=Path, nargs="+", metavar="SCENARIO_DIR",
                   help="Збалансувати вже сконвертовані сценарії за їхнім manifest.json, без конвертації")
    args = p.parse_args()

    if args.rebalance:
        for scenario_dir in args.rebalance:
            print(f"{scenario_dir.name}: {rebalance_existing(scenario_dir, args.seed)['test_balance']}")
        return
    if not args.inputs or args.out is None:
        p.error("потрібні вхідні архіви/теки та --out (або --rebalance)")

    with ExitStack() as stack:
        recordings: list[Recording] = []
        for src in args.inputs:
            if src.is_dir():
                recordings += _scan_dir(src)
            elif zipfile.is_zipfile(src):
                recordings += _scan_archive(stack.enter_context(zipfile.ZipFile(src)), src)
            else:
                sys.exit(f"{src} — не тека і не zip-архів")

        by_scenario: dict[str, list[Recording]] = {}
        for rec in recordings:
            by_scenario.setdefault(rec.scenario, []).append(rec)
        if args.scenarios:
            by_scenario = {k: v for k, v in by_scenario.items() if k in args.scenarios}
        if not by_scenario:
            sys.exit(f"Не знайдено сценаріїв у {', '.join(map(str, args.inputs))}")

        for scenario, recs in sorted(by_scenario.items()):
            s = convert_scenario(
                scenario, recs, args.out, args.limit,
                balance_seed=args.seed if args.balance_test else None,
            )
            statuses: dict[str, int] = {}
            for r in s["recordings"]:
                statuses[r["status"]] = statuses.get(r["status"], 0) + 1
            print(f"{scenario}: {statuses}")
            if "test_balance" in s:
                print(f"{scenario}: {s['test_balance']}")


if __name__ == "__main__":
    main()