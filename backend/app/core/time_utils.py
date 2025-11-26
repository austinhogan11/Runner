def hhmmss_to_seconds(hhmmss: str) -> int:
    """
    Convert 'HH:MM:SS' -> total seconds (int).
    Example: '00:45:32' -> 2732
    """
    parts = hhmmss.split(":")
    if len(parts) != 3:
        raise ValueError("Duration must be in HH:MM:SS format")

    hours, minutes, seconds = map(int, parts)
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_hhmmss(total_seconds: int) -> str:
    """
    Convert total seconds (int) -> 'HH:MM:SS'.
    Example: 2732 -> '00:45:32'
    """
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def compute_pace(duration_seconds: int, distance_mi: float) -> str:
    """
    Compute pace per mile as 'M:SS/mi' or 'MM:SS/mi'.
    Example: duration=2732 sec, distance=7.35 -> '6:11/mi'
    """
    if distance_mi <= 0:
        return "0:00/mi"

    pace_sec = int(duration_seconds / distance_mi)

    minutes = pace_sec // 60
    seconds = pace_sec % 60
    return f"{minutes}:{seconds:02d}/mi"


def hhmm_to_time(hhmm: str):
    """Parse time strings into datetime.time.

    Accepts common formats:
      - 'HH:MM' (24h)
      - 'HH:MM:SS' (24h)
      - 'H:MM AM/PM' (12h), case-insensitive
      - 'H AM/PM'

    Returns None for empty strings.
    """
    if hhmm is None:
        return None
    s = hhmm.strip()
    if s == "":
        return None

    from datetime import datetime

    candidates = [
        "%H:%M",
        "%H:%M:%S",
        "%I:%M %p",
        "%I %p",
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    raise ValueError("Start time must be in formats like 'HH:MM' or '10:00 AM'")


def time_to_hhmm(t) -> str | None:
    """Format datetime.time -> 'HH:MM'. Returns None if t is None."""
    if t is None:
        return None
    return f"{t.hour:02d}:{t.minute:02d}"


def to_local_datetime(dt, tz_name: str | None = None):
    """Convert a datetime from source tz (assume UTC if naive) to local or given tz.

    - If `tz_name` is 'local' or None: use system local timezone.
    - If `tz_name` is IANA tz name (e.g., 'America/New_York'): use that.
    - If `dt` has no tzinfo, assume UTC.
    """
    from datetime import timezone
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if tz_name and tz_name != "local":
            try:
                from zoneinfo import ZoneInfo
                return dt.astimezone(ZoneInfo(tz_name))
            except Exception:
                return dt.astimezone()
        else:
            return dt.astimezone()
    except Exception:
        return dt
