import os
import cv2

class DemoLoader:
    def __init__(self, demo_dir='data/demo'):
        self.demo_dir = demo_dir

    def get_demo_image(self, category):
        """Returns the appropriate demo image for a category."""
        if category in ['edge', 'features', 'matching']:
            path = os.path.join(self.demo_dir, 'cityscape.png')
        elif category in ['segmentation', 'detection']:
            path = os.path.join(self.demo_dir, 'fruit.png')
        else:
            path = os.path.join(self.demo_dir, 'cityscape.png')
        
        if os.path.exists(path):
            return cv2.imread(path)
        return None

demo_loader = DemoLoader()
