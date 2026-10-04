"""
Рекурсивно розпаковує zip-записи LID-DS 2021 і залишає лише .sc та .json.

Структура тек зберігається (<сценарій>/training, <сценарій>/validation, <сценарій>/test/...),
тож результат одразу підходить для config.DATASET_ROOT. Зайві файли архіву (.pcap, .res тощо)
на диск взагалі не записуються — розпаковуються лише .sc та .json, обидва з іменем архіву
(<ім'я>.zip -> <ім'я>.sc + <ім'я>.json), як того очікує lid_ds_data.py.

Usage:
    # у нову теку, оригінальні архіви не чіпаються
    python unpack_lid_ds.py --src /data/LID-DS-2021 --dst ./DATASET

    # на місці: поруч з архівом, архіви після успішної розпаковки видаляються
    python unpack_lid_ds.py --src ./DATASET --delete-zips

Повторний запуск безпечний: вже розпаковані файли з тим самим розміром пропускаються
(--force — перезаписати).
"""

import argparse
import os
import shutil
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

KEEP_EXTENSIONS = (".sc", ".json")
COPY_CHUNK = 1024 * 1024


def _extract_one(zip_path_str: str, out_dir_str: str, force: bool, delete_zip: bool) -> dict:
    zip_path = Path(zip_path_str)
    out_dir = Path(out_dir_str)
    stem = zip_path.stem
    result = {
        "zip": zip_path_str, "out_dir": out_dir_str, "stem": stem,
        "ok": False, "written_bytes": 0, "extracted": 0, "skipped": 0, "missing": [], "error": None,
    }

    try:
        with zipfile.ZipFile(zip_path) as zf:
            members: dict[str, zipfile.ZipInfo] = {}
            for info in zf.infolist():
                if info.is_dir():
                    continue
                ext = Path(info.filename).suffix.lower()
                if ext in KEEP_EXTENSIONS and ext not in members:
                    members[ext] = info
            result["missing"] = [ext for ext in KEEP_EXTENSIONS if ext not in members]

            out_dir.mkdir(parents=True, exist_ok=True)
            for ext, info in members.items():
                target = out_dir / f"{stem}{ext}"
                if not force and target.exists() and target.stat().st_size == info.file_size:
                    result["skipped"] += 1
                    continue
                tmp = target.with_name(target.name + ".part")  # щоб обірваний запуск не лишив "половинчастий" файл
                with zf.open(info) as src, open(tmp, "wb") as dst:
                    shutil.copyfileobj(src, dst, COPY_CHUNK)
                os.replace(tmp, target)
                result["extracted"] += 1
                result["written_bytes"] += info.file_size
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["ok"] = True
    if delete_zip and not result["missing"]:
        zip_path.unlink()
    return result


def _sweep_leftovers(out_dir: Path, stems: set[str]) -> int:
    """
    Видаляє у теці рештки записів, що оброблені: <ім'я>.pcap, <ім'я>.res, <ім'я>.sc.part тощо.
    Залишаються лише <ім'я>.sc, <ім'я>.json та самі .zip (їх прибирає --delete-zips).
    """
    removed = 0
    for path in out_dir.iterdir():
        if not path.is_file() or path.suffix.lower() in (*KEEP_EXTENSIONS, ".zip"):
            continue
        if path.name.split(".", 1)[0] in stems:
            path.unlink()
            removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--src", required=True, help="Тека з LID-DS (шукаються всі *.zip рекурсивно)")
    parser.add_argument("--dst", default=None, help="Куди розпаковувати зі збереженням структури тек (за замовчуванням — на місці)")
    parser.add_argument("--delete-zips", action="store_true", help="Видаляти архів після успішної розпаковки")
    parser.add_argument("--force", action="store_true", help="Перезаписувати вже розпаковані файли")
    parser.add_argument("--workers", type=int, default=4, help="Кількість паралельних процесів")
    args = parser.parse_args()

    src = Path(args.src).resolve()
    dst = Path(args.dst).resolve() if args.dst else None
    if not src.is_dir():
        print(f"Не знайдено теку {src}", file=sys.stderr)
        return 1
    if dst is not None and dst == src:
        dst = None  # --dst збігається з --src: те саме, що розпаковка на місці

    zips = sorted(src.rglob("*.zip"))
    if not zips:
        print(f"У {src} не знайдено жодного .zip")
        return 0

    jobs = []
    for zip_path in zips:
        out_dir = zip_path.parent if dst is None else dst / zip_path.parent.relative_to(src)
        jobs.append((str(zip_path), str(out_dir), args.force, args.delete_zips))
    print(f"Архівів: {len(jobs)}, потоків: {args.workers}, режим: {'на місці' if dst is None else dst}")

    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_extract_one, *job) for job in jobs]
        for i, future in enumerate(as_completed(futures), start=1):
            res = future.result()
            results.append(res)
            if res["error"]:
                print(f"[{i}/{len(jobs)}] ПОМИЛКА {res['zip']}: {res['error']}")
            elif res["missing"]:
                print(f"[{i}/{len(jobs)}] УВАГА {res['zip']}: у архіві немає {', '.join(res['missing'])}")
            elif i % 50 == 0 or i == len(jobs):
                print(f"[{i}/{len(jobs)}] оброблено")

    stems_by_dir: dict[str, set[str]] = {}
    for res in results:
        if res["ok"]:
            stems_by_dir.setdefault(res["out_dir"], set()).add(res["stem"])
    swept = sum(_sweep_leftovers(Path(d), stems) for d, stems in stems_by_dir.items())

    errors = [r for r in results if r["error"]]
    incomplete = [r for r in results if r["missing"] and not r["error"]]
    print(
        f"\nГотово: розпаковано записів — {sum(r['ok'] for r in results) - len(incomplete)}, "
        f"файлів записано — {sum(r['extracted'] for r in results)}, "
        f"пропущено (вже є) — {sum(r['skipped'] for r in results)}, "
        f"обсяг — {sum(r['written_bytes'] for r in results) / 1024**2:.1f} МБ, "
        f"видалено залишків — {swept}"
    )
    if incomplete:
        print(f"Неповних архівів (немає .sc або .json), вони не видалялись: {len(incomplete)}")
    if errors:
        print(f"Архівів з помилками: {len(errors)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
