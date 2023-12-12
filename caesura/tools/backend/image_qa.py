from contextlib import ExitStack
import requests
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering


class VisualQA():
    def __init__(self):
        self.model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")

    def extract(self, image_paths: str, query: str, batch_size:int = 10):
        """Retrieves images from the database."""
        results = []
        for i in range(0, len(image_paths), batch_size):
            with ExitStack() as stack:
                images = [stack.enter_context(Image.open(image_path)) for image_path in image_paths[i: i + batch_size]]
                inputs = self.processor(images=images, text=query, return_tensors="pt", padding=True)
                outputs = self.model.generate(**inputs, max_length=20)

                results.extend([self.processor.decode(o, skip_special_tokens=True) for o in outputs])
        return results
