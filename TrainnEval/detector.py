from ultralytics import YOLO

class DamageDetector:
    def __init__(self, model_path, device=0, imgsz=640):
        self.device = device
        self.model = YOLO(model_path)
        self.imgsz = imgsz

    def predict(self, image_path):
        result = self.model.predict(source=str(image_path), imgsz=self.imgsz, device=self.device, verbose=False)[0]
        boxes = []
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy.numpy().tolist()
            conf = float(box.conf)
            cls = int(box.cls)
            boxes.append({
                "class_id": cls, "class": self.model.names[cls], "conf": conf, "box": (x1, y1, x2, y2)
            })
        return boxes

    @ staticmethod
    def compute_image_severity(detections):
        if len(detections) == 0:
            return "none", 0.0

        max_severity = max(d['class_id'] for d in detections)
        max_conf = max([d for d in detections if d['class_id']==max_severity], key=lambda x: x['conf'])
        severity_label = {0:"minor", 1:"moderate", 2:"severe"}[max_conf['class_id']]

        return severity_label, max_conf['conf']

