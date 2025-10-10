import threading
from queue import Queue
from TrainnEval.detector import DamageDetector
from messaging.composer import save_annotated_image
from Config import config
from messaging.send_latest_coords import notify_server_http
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
        while True:
            item = self.result_q.get()
            if item is None:
                break
            img_path, severity, conf, detections = item

            try:
                if severity == 'none' or conf < config.conf_thres:
                    continue

                device_id = ImagePipeline.extract_device_id_from_filename(img_path)
                if not device_id:
                    print(f"[WARN] No device_id found in filename {img_path}")
                    device_id = 'unknown'

                # should send annotated image instead of image_path in notify_server_http
                try:
                    annotated_img = save_annotated_image(img_path, detections)

                except Exception as e:
                    print('[WARN] could not save annotated image:', e)
                    annotated_img = None

                yes, info = notify_server_http(device_id=device_id, severity=severity, confidence=conf, image_path=img_path)
                if not yes:
                    print('[WARN] Notify server failed:', info)
                else:
                    print(f'[INFO] Server notified for {img_path}: {info}')

            except Exception as e:
                print('[Error] unexpected postprocess error for', img_path, e)


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

