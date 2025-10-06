import csv
from datetime import datetime
from pathlib import Path
import sys
from messaging.sms import TwilioSmsClient, MockSmsClient
from messaging.composer import compose_sos
from Config import config

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

# def send_device_location_sms(device_id, severity, image_path, annotated_path,
#                              path=csv_path, sms_cfg=config.twilio_cfg):
#     csv_path = Path(path)
# 
#     try:
#         latest = read_latest_for_device(device_id, csv_path)
# 
#     except FileNotFoundError as e:
#         return False, f"csv not found: {e}"
# 
#     except Exception as e:
#         return False, f"Error reading csv: {e}"
# 
#     if not latest:
#         return False, f"No location record for this device: {device_id}"
# 
#     ts = latest['timestamp']
#     ts_str = ts.isoformat() if ts else None
#     lat = latest['latitude']
#     lon = latest['longitude']
# 
#     latlon = (lat, lon) if (lat is not None and lon is not None and str(lat).strip() and str(lon).strip()) else None
# 
#     message = compose_sos(ts_str, latlon, severity, image_path, sms_cfg)
# 
#     client = None
# 
#     if sms_cfg and sms_cfg.get("provider") == "twilio":
#         sid = sms_cfg.get("sid")
#         token = sms_cfg.get("token")
#         from_no = sms_cfg.get("from")
#         to_no = sms_cfg.get("to")
#         if not sid or not token or not from_no:
#             return False, "Twilio config incomplete (sid/token/from required)"
# 
#         try:
#             client = TwilioSmsClient(sid, token, from_no, to=to_no)
#         except Exception as e:
#             return False, f"Failed to create Twilio client: {e}"
# 
#     else:
#         # fallback to mock
#         client = MockSmsClient(to=sms_cfg.get("to") if sms_cfg else None)
# 
#     try:
#         client.send("\n".join(message) if isinstance(message, (list, tuple)) else str(message))
#         return True, "Message sent (or logged for mock)"
#     except Exception as e:
#         return False, f"Failed to send SMS: {e}"
