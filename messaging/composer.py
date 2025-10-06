from PIL import Image, ImageDraw
import os
from pathlib import Path

def compose_sos(timestamp, latlon, severity,
                image_path, annotated_path=None):
    lines = []
    lines.append('Accident Alert')
    lines.append(f'Time: {timestamp}')
    if latlon:
        lines.append(f'Location: {latlon[0]}, {latlon[1]}')
    else:
        lines.append('Location: Unknown')
    lines.append(f'Severity: {severity}')
    lines.append(f'Evidence: {image_path}')
    if annotated_path:
        lines.append(f'Annotated Path: {annotated_path}')

    return lines

def save_annotated_image(image_path, detections, out_path=None):
    img = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    for d in detections:
        if d.get('box'):
            x1, y1, x2, y2 = d['box']
            draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
    if out_path is None:
        out_path = str(Path('logs') / (Path(image_path).stem + '_annot.jpg'))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path
