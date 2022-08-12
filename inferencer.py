# Imports
from pollen_id.detector.ml_bundle import MLBundle
from pollen_id.detector.trainer import Trainer
# import torch
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor
from pollen_id.detector.predictor import Predictor
from pollen_id.image import SVGImage
from detectron2.utils.visualizer import Visualizer, ColorMode
import glob
import os
import random
import cv2
from matplotlib import pyplot as plt
from matplotlib.pyplot import figure
from PIL import Image
import numpy as np
import json

class Inferencer():
    def __init__(self, bundle_name):
        self._bundle_name = bundle_name
        self._bundle = MLBundle(self._bundle_name)
        self._dataset = self._bundle.dataset
        self._dataset.prepare()
        self._cfg = self._bundle.config
        self._predictor = DefaultPredictor(self._cfg)
        self._out_dir = self._bundle._output_dir

    def save_json(self, predictions, name):
        """
        Takes the list of predictions (outputs from predictor)
        name of the file
        """
        out_dir = self._out_dir
        # out_dir = "pollen_id/detector/output"
        filename = out_dir + name + ".json"
        with open(filename, "w") as f:
            json.dump(predictions, f)
        return "Done"
    
    def generate_train_test_split(self, inference_dir=None):
        if inference_dir is None:
            inference_dir = self._bundle._data_dir
        # print(inference_dir)
        # assert os.path.dirname(inference_dir)
        ins = sorted(glob.glob(os.path.join(inference_dir, "*.svg")))

        # randomly split the inputs used in model fitting to train and test
        train = set(random.sample(ins, int(0.75*len(ins))))
        test = set(ins) - train
        return list(train), list(test)

    def make_predictions(self, dataset=None):
        predictor = self._predictor
        # Instantiate array to store results
        predictions = []
        for path in dataset:
            # Loads evert path of valid set to SVGImage
            to_pred = SVGImage(path=path, foreign=True)
            # Use detectron2's default predictor to make detect instances on numpy array of the SVGImage
            predicted = predictor(to_pred.read())
            # Append results of predictions to an array
            predictions.append(predicted)
        return predictions

    # Loads image by reading it
    def visualize_with_plt(self, dataset, opt):
        prefix = "pollen-id-detector_"
        subset = prefix + opt
        predictor = self._predictor
        for path in dataset:
            img = SVGImage(path=path, foreign=True).read()
            metadata = MetadataCatalog.get(subset)
            output = predictor(img)
            v = Visualizer(img[:, :, ::-1],
                           metadata=metadata,
                           scale=1#,
                           # instance_mode=ColorMode.IMAGE_BW
                          )
            out = v.draw_instance_predictions(output["instances"].to("cpu"))
            arr = out.get_image()[:,:,::-1]
            plt.imshow(arr, interpolation='nearest')
            plt.title(path)
            plt.show() 
        return 0

    def get_array_from_visualizer(self, svg_path):
        predictor = self._predictor
        img = SVGImage(path=svg_path, foreign=True).read()
        metadata = MetadataCatalog.get("pollen-id-detector_train")
        output = predictor(img)
        v = Visualizer(img[:, :, ::-1],
                       metadata=metadata,
                       scale=1#,
                       # instance_mode=ColorMode.IMAGE_BW
                      )
        out = v.draw_instance_predictions(output["instances"].to("cpu"))
        array = out.get_image()[:,:,::-1]
        return array

    def render_PIL(self, array):
        pil_image = Image.fromarray(np.uint8(array)).convert('RGB')
        return pil_image
    
    def save_predictions_jpg(self, dataset):
        # Make predictions and get their array
        out_dir = self._out_dir
        for path in dataset:
            filename_without_ext = os.path.splitext(path)[0].split("\\")[2]
            array = self.get_array_from_visualizer(path)
            img = self.render_PIL(array)
            img.save(out_dir + filename_without_ext + ".jpg")
        return "Done"