import os
from pathlib import Path
import torch

Root = Path(__file__).resolve().parents[1]

data_dir = Path(os.getenv("Accident_data_Dir", "D:\Datasets\Accident_Detection"))

models_dir = Root / "models"
log_dir = Root / "logs"

model_path = os.getenv("model_path", str(models_dir / "best.pt"))
imgsz = int(os.getenv("imgsz", 640))
Device = "cuda" if torch.cuda.is_available() else "cpu"
conf_thres = float(os.getenv("conf_thres", 0.6))

sms_provider = os.getenv("sms_provider", "mock")
sms_to = os.getenv("sms_to", "+918087795032")
max_queue_size = int(os.getenv("max_queue_size", 32))

# Enter your twilio credentials
twilio_cfg = {
    'provider': 'twilio',
    'sid': '',
    'token': '',
    'from': ''
}

log_dir.mkdir(parents=True, exist_ok=True)
models_dir.mkdir(parents=True, exist_ok=True)
