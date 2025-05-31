from smolagents import Tool
from transformers import pipeline


class ObjectDetectorTool(Tool):
    name: str = "object_detector_tool"
    description: str = "This tool detects objects in an image and returns their bounding boxes and labels."
    inputs = {
        "image_path": {
            "type": "string",
            "description": "The path to the image file in which to detect objects.",
        },
    }
    output_type = "array"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint = "google/owlv2-base-patch16-ensemble"
        self.candidate_labels = [
            "playing card",
            "not a playing card",
        ]
        self.detector = pipeline(
            model=self.checkpoint, task="zero-shot-object-detection", use_fast=True
        )
        self.confidence_threshold = 0.3

    def forward(self, image_path: str) -> list[dict]:
        """
        Detects objects in the provided image and returns their bounding boxes and labels.

        Args:
            image_path (str): The path to the image file.

        Returns:
            list: A list of dictionaries containing detected objects with their labels and bounding boxes.
        """
        results: list[dict] = self.detector(
            image_path, candidate_labels=self.candidate_labels
        )
        # Filter results based on confidence threshold
        results = [
            result
            for result in results
            if result["score"] >= self.confidence_threshold
            and result["label"] == "playing card"
        ]
        return results
