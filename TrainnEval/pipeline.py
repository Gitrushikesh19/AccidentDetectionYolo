import threading
from queue import Queue
import time
from TrainnEval.detector import DamageDetector
from messaging.sms import get_sms_client
from messaging.composer import compose_sos, save_annotated_image
from Config import config
from messaging.send_latest_coords import parse_iso_timestamp, read_latest_for_device
from pathlib import Path

class ImagePipeline:
    def __init__(self, model_path=config.model_path, imgsz=config.imgsz, device=config.Device, sms_config=None):
        self.input_q = Queue(maxsize=config.max_queue_size)
        self.result_q = Queue()
        self.model_path = model_path
        self.imgsz = imgsz
        self.device = device
        self.metadata = None
        self.sms_config = sms_config

    def enqueue(self, image_path):
        self.input_q.put(image_path)

    def stop(self):
        self.input_q.put(None)

    def inference_worker(self):
        detector = DamageDetector(model_path=self.model_path, device=self.device)
        while True:
            p = self.input_q.get()
            if p is None:
                self.result_q.put(None)
                break
            try:
                detections = detector.predict(p)
                severity, conf = detector.compute_image_severity(detections)
                self.result_q.put((p, severity, conf, detections))

            except Exception as e:
                print('Inference error for:', p, e)

    @staticmethod
    def extract_device_id_from_filename(image_path):
        try:
            name = Path(image_path).stem
            for token in name.split("_"):
                device_id = token.strip()
                if device_id.lower().startswith("DELL") or device_id.lower().startswith("device"):
                    return device_id
        except Exception:
            pass
        return None

    def postprocess_worker(self):
        sms = get_sms_client(self.sms_config)
        device_csv_path = Path("logs") / "device_locations.csv"
        while True:
            item = self.result_q.get()
            if item is None:
                break
            img_path, severity, conf, detections = item

            try:
                if severity == 'none' and conf < config.conf_thres:
                    print(f"[INFO] skip SMS for {img_path}: severity={severity}, confidence={conf:.3f}")
                    continue

                device_id = ImagePipeline.extract_device_id_from_filename(img_path)
                latlon = None
                ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

                if device_id:
                    latest = None
                    try:
                        latest = read_latest_for_device(device_id, path=device_csv_path)

                    except Exception as e:
                        print("[WARN] Could not read device locations CSV:", e)

                    if latest and latest.get("latitude") and latest.get("longitude"):
                        lat = latest["latitude"]
                        lon = latest["longitude"]
                        latlon = (lat, lon)
                        if latest.get("timestamp"):
                            ts_parsed = latest["timestamp"]
                            ts_str = ts_parsed.isoformat() if hasattr(ts_parsed, "isoformat") else str(ts_parsed)

                try:
                    annotated = save_annotated_image(img_path, detections)
                except Exception as e:
                    print("[WARN] Could not save annotated image:", e)
                    annotated = None

                try:
                    msg_lines = compose_sos(ts_str, latlon, severity, img_path, annotated)
                    # compose_sos returns a list in your composer; join to a string
                    payload = "\n".join(map(str, msg_lines))
                    # send in a short background thread to avoid blocking loop
                    threading.Thread(target=sms.send, args=(payload,), daemon=True).start()
                    print(f"[INFO] SMS dispatched (or logged) for {img_path}")
                except Exception as e:
                    print("[ERROR] Failed composing/sending SMS for", img_path, e)

            except Exception as e:
                print("[ERROR] Unexpected error in postprocessing for", img_path, e)

    def start(self, image):
        t_inf = threading.Thread(target=self.inference_worker, daemon=True)
        t_post = threading.Thread(target=self.postprocess_worker, daemon=True)
        t_inf.start()
        t_post.start()
        for img in image:
            self.enqueue(img)
        self.stop()
        t_inf.join()
        self.result_q.put(None)
        t_post.join()

