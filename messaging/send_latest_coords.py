import csv
from pathlib import Path
import requests
from datetime import datetime

csv_path = Path('logs') / "device_locations.csv"

def parse_iso_timestamp(ts_str):
    if not ts_str:
        return None

    s = str(ts_str).strip()
    if s.endswith("Z"):
        s = s[: -1] + "+00:00"

    try:
        return datetime.fromisoformat(s)

    except Exception:
        pass

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    )

    for f in formats:
        try:
            return datetime.strptime(s, f)
        except Exception:
            continue

    return None

def read_latest_for_device(device_id, path=csv_path):
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No such file or directory: {csv_path}")

    latest = None
    row_index = 0
    with csv_path.open(newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row_index += 1
            ts_str = row.get('timestamp') or row.get('timestamp_iso') or row.get('time') or row.get('ts')

            try:
                dev = (row.get('device_id') or row.get('device') or row.get('id')).strip()

            except Exception:
                dev = ""
            if dev != device_id:
                continue

            parsed_ts = parse_iso_timestamp(ts_str)

            if latest is None:
                latest = (parsed_ts, row_index, row)

            else:
                current_ts, current_idx, _ = latest
                if parsed_ts and current_ts:
                    if parsed_ts > current_ts:
                        latest = (parsed_ts, row_index, row)

                elif parsed_ts and current_ts:
                    latest = (parsed_ts, row_index, row)

                elif not parsed_ts and not current_ts:
                    if row_index > current_idx:
                        latest = (parsed_ts, row_index, row)

    if latest is None:
        return None

    parsed_ts, idx, rowdict = latest

    lat = rowdict.get("latitude") or rowdict.get("lat") or rowdict.get("lat_deg")
    lon = rowdict.get("longitude") or rowdict.get("lon") or rowdict.get("lng")
    acc = rowdict.get("accuracy") or rowdict.get("acc")
    return {"timestamp": parsed_ts, "latitude": lat, "longitude": lon, "accuracy": acc, "raw_row": rowdict}

SERVER_URL = "http://localhost:3000/api/detection"  # change if server is remote

def notify_server_http(device_id: str, severity: str, confidence: float, image_path: str, timestamp: str = None):
    payload = {
        "device_id": device_id,
        "severity": severity,
        "confidence": float(confidence),
        "image_path": image_path,
        "timestamp": timestamp or (datetime.now().isoformat() + "Z")
    }
    try:
        r = requests.post(SERVER_URL, json=payload, timeout=6)
        r.raise_for_status()
        return True, r.json() if r.headers.get('content-type','').startswith('application/json') else r.text
    except Exception as e:
        return False, str(e)
