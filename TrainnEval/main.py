from ultralytics import YOLO
from TrainnEval.pipeline import ImagePipeline
from Config import config

model = YOLO('yolov8s.pt')
model.train(data='set.yaml', epochs=30, imgsz=640,
            batch=4, project='runs/detect',
            name='accident_detection')

def main():
    image = ["data/test/img-1.jpg"]  # hardcoded
    pl = ImagePipeline(model_path=config.model_path, sms_config=config.twilio_cfg)
    pl.start(image)

if __name__ == "__main__":
    main()
