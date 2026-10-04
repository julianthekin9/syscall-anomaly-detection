from dataclasses import dataclass

from syscall_hids import config

@dataclass
class ParsedLine:
    timestamp: float  # абсолютные unix-секунды
    syscall: str
    process_name: str
    direction: str
    arg_count: int


def parse_log_line(line: str) -> ParsedLine | None:
    """Парсит одну строку .sc-записи. Возвращает None для "мусорных" строк."""
    fields = line.strip().split(" ")
    if len(fields) < config.MIN_RAW_FIELDS:
        return None

    try:
        timestamp_ns = int(fields[config.TIME_COLUMN_INDEX])
    except (ValueError, IndexError):
        return None

    try:
        syscall = fields[config.SYSCALL_COLUMN_INDEX]
        process_name = fields[config.PROCESS_NAME_COLUMN_INDEX]
        direction = fields[config.DIRECTION_COLUMN_INDEX]
    except IndexError:
        return None

    arg_count = max(0, len(fields) - config.PARAMS_BEGIN_INDEX)

    return ParsedLine(
        timestamp=timestamp_ns / 1e9,
        syscall=syscall,
        process_name=process_name,
        direction=direction,
        arg_count=arg_count,
    )


def read_recording(path: str) -> list[ParsedLine]:
    """Читает один .sc-файл и возвращает список распарсенных строк (без 'switch')."""
    lines: list[ParsedLine] = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            parsed = parse_log_line(raw_line)
            if parsed is not None and parsed.syscall != "switch":
                lines.append(parsed)
    return lines
