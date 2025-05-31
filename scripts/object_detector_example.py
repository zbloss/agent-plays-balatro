from balatro_agent.tools.object_detector import ObjectDetectorTool
import os
from PIL import Image, ImageDraw

print(os.getcwd())

image_path = "./images/sample.jpg"
output_path = "./images/sample_with_boxes.jpg"

object_detector_tool = ObjectDetectorTool()
out = object_detector_tool.forward(image_path)
print("Detected Objects:")
print(len(out))

# Overlay bounding boxes and save new image
image = Image.open(image_path)
draw = ImageDraw.Draw(image)

for idx, obj in enumerate(out):
    if idx == 0:
        print("First detected object:", obj)
    # Example obj: {'score': 0.55, 'label': 'playing card', 'box': {'xmin': 1435, 'ymin': 420, 'xmax': 1614, 'ymax': 670}}
    box = obj.get("box")
    if box:
        bbox = [box["xmin"], box["ymin"], box["xmax"], box["ymax"]]
        draw.rectangle(bbox, outline="red", width=3)
        # Optionally, draw label and score
        label = obj.get("label", "")
        score = obj.get("score", 0)
        text = f"{label} ({score:.2f})"
        draw.text((box["xmin"], box["ymin"] - 10), text, fill="red")

image.save(output_path)
print(f"Image with bounding boxes saved to {output_path}")
