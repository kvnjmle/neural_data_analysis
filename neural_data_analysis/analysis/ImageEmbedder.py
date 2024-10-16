#!/usr/bin/env python3
"""
This module contains functions to embed images using different models.

Functions:
    None

Classes:


Examples:

"""
from abc import ABC, abstractmethod
import numpy as np
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms
from torchvision.models import (
    resnet50,
    ResNet50_Weights,
    vit_b_16,
    ViT_B_16_Weights,
    vgg16,
    VGG16_Weights,
)
from tqdm import tqdm
from transformers import (
    AutoImageProcessor,
    AutoModel,
    AutoModelForObjectDetection,
    AutoProcessor,
    Blip2ForConditionalGeneration,
    Blip2Processor,
    BlipForConditionalGeneration,
    CLIPModel,
)


class ImageEmbedder(ABC, nn.Module):
    """
    Embeds input images by an encoding model.

    Attributes:
        config (dict): Configuration dictionary.
        device (torch.device): Device to use for embedding.

    Methods:
        preprocess(self, images: torch.Tensor) -> torch.Tensor
        embed(self, images: torch.Tensor) -> np.ndarray

    """

    def __init__(
        self,
        config: dict,
        device: torch.device,
    ):
        nn.Module.__init__(self)
        self.config = config
        self.device = device
        self.batch_size = config.get("batch_size", 64)
        self.encoder = None
        self.embedding_name = config.get("embedding_name", "ImageEmbedder")

    @abstractmethod
    def preprocess(self, images: torch.Tensor) -> torch.Tensor:
        pass

    @torch.no_grad()
    def embed(self, images: torch.Tensor) -> np.ndarray:
        """
        Embeds the input images using the encoder.

        Args:
            images (torch.Tensor): Tensor of shape (n_samples, n_channels, height, width).

        Returns:
            np.ndarray: Embedded features.
        """
        results = []
        print(f"Embedding with {self.embedding_name}...")
        for i in tqdm(range(0, images.shape[0], self.batch_size)):
            batch = images[i : i + self.batch_size]
            batch = self.preprocess(batch).to(self.device)
            batch = self.encoder(batch)
            results.append(batch)
        results = torch.cat(results, dim=0).cpu().numpy()
        return results


class VGG16Embedder(ImageEmbedder, nn.Module):
    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        nn.Module.__init__(self)
        self.encoder = vgg16(weights=VGG16_Weights.IMAGENET1K_V1)
        self.encoder.classifier = nn.Sequential(
            *list(self.encoder.classifier.children())[:-3]
        )
        self.encoder.to(device)
        self.encoder.eval()
        self.processor = VGG16_Weights.IMAGENET1K_V1.transforms()

    def preprocess(self, images: torch.Tensor) -> torch.Tensor:
        images = _check_image_tensor_dimensions(images)
        images = self.processor(images)
        return images


class ResNet50Embedder(ImageEmbedder, nn.Module):
    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        nn.Module.__init__(self)
        self.encoder = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        self.encoder.fc = nn.Identity()
        self.encoder.to(device)
        self.encoder.eval()
        self.processor = ResNet50_Weights.IMAGENET1K_V2.transforms()

    def preprocess(self, images: torch.Tensor) -> torch.Tensor:
        images = _check_image_tensor_dimensions(images)
        images = self.processor(images)
        return images


class CLIPEmbedder(ImageEmbedder, nn.Module):
    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        nn.Module.__init__(self)
        self.encoder = CLIPModel.from_pretrained(config["model"])
        self.encoder.to(device)
        self.encoder.eval()
        self.processor = AutoProcessor.from_pretrained(config["processor"])

    def preprocess(self, images: torch.Tensor) -> dict:
        if "numpy" in str(type(images)):
            images = torch.from_numpy(images)
        # to PIL image
        images = _check_image_tensor_dimensions(images)
        images = [torchvision.transforms.ToPILImage()(img) for img in images]
        images = self.processor(
            # TODO: change the text from "a" to ""
            # text=["a"] * len(images),
            images=images,
            return_tensors="pt",
            padding=True,
        ).to(self.device)
        return images

    # noinspection PyPep8
    @torch.no_grad()
    def embed(self, images: torch.Tensor) -> np.ndarray:
        results = []
        print("Embedding with CLIP...")
        for i in tqdm(range(0, images.shape[0], self.batch_size)):
            batch = images[i : i + self.batch_size]
            batch = self.preprocess(batch)  # returns a dict-like object
            batch = self.encoder.get_image_features(**batch)
            results.append(batch)
            # results.append(batch["image_embeds"])
        results = torch.cat(results, dim=0).cpu().numpy()
        return results


class DETREmbedder(ImageEmbedder):
    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        self.obj_detection_threshold = config["detection_threshold"]
        self.encoder = AutoModelForObjectDetection.from_pretrained(config["processor"])
        self.encoder.to(device)
        self.processor = AutoImageProcessor.from_pretrained(config["processor"])

    def preprocess(self, images: list) -> dict:
        images = self.processor(images, return_tensors="pt").to(self.device)
        return images

    @torch.no_grad()
    def embed(self, images: torch.Tensor) -> dict:
        """
        Args:
            images (torch.Tensor): (n_samples, n_channels, height, width)

        """
        images = _check_image_tensor_dimensions(images)

        # target sizes should be (height, width) and used to rescale the object detection predictions to the original
        # image size; passing in images as (n_channels, height, width) so we use .shape[1] and .shape[2] to get the
        # height and width
        target_sizes = [[img.shape[1], img.shape[2]] for img in images]
        try:
            target_sizes = [
                torch.tensor([img.shape[1], img.shape[2]]) for img in images
            ]
        except ValueError:
            print("Video must be a list of tensors.")

        # PIL images are (width, height)
        images = [transforms.ToPILImage()(img) for img in images]

        result_obj_ids = []
        result_obj_names = []
        result_obj_boxes = []
        result_obj_scores = []
        print("Embedding with DETR...")
        for i in tqdm(range(0, len(images), self.batch_size)):
            batch = images[i : i + self.batch_size]
            batch_target_sizes = target_sizes[i : i + self.batch_size]
            inputs = self.preprocess(batch)
            outputs = self.encoder(**inputs)
            result = self.processor.post_process_object_detection(
                outputs,
                threshold=self.obj_detection_threshold,
                target_sizes=batch_target_sizes,
            )
            result_ids = [res["labels"] for res in result]
            result_names = [
                [self.encoder.config.id2label[id_i.item()] for id_i in ids]
                for ids in result_ids
            ]
            result_scores = [res["scores"] for res in result]
            result_boxes = [res["boxes"] for res in result]
            result_obj_ids.extend(result_ids)
            result_obj_names.extend(result_names)
            result_obj_scores.extend(result_scores)
            result_obj_boxes.extend(result_boxes)
        result_obj_ids = [ids.cpu().numpy() for ids in result_obj_ids]
        result_obj_names = [np.array(names) for names in result_obj_names]
        result_obj_boxes = [boxes.cpu().numpy() for boxes in result_obj_boxes]
        result_obj_scores = [scores.cpu().numpy() for scores in result_obj_scores]
        results = {
            "ids": result_obj_ids,
            "labels": result_obj_names,
            "boxes": result_obj_boxes,
            "scores": result_obj_scores,
        }
        return results


class BLIPEmbedder(ImageEmbedder):
    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        self.encoder = BlipForConditionalGeneration.from_pretrained(
            self.config["model"]
        ).to(self.device)
        self.processor = AutoProcessor.from_pretrained(self.config["processor"])
        self.text_prompt = "A picture of "

    def preprocess(self, images: torch.Tensor) -> dict:
        images = _check_image_tensor_dimensions(images)
        images = self.processor(
            images=images,
            return_tensors="pt",
            padding=True,
        ).to(self.device)
        return images

    def embed(self, images: torch.Tensor):
        result_text = []
        result_ids = []
        print("Embedding with BLIP...")
        with torch.no_grad():
            for i in tqdm(range(0, len(images), self.batch_size)):
                batch = images[i : i + self.batch_size]
                batch = batch.to(self.device)
                batch = self.processor(
                    text=[self.text_prompt] * len(batch),
                    images=[batch[j] for j in range(batch.shape[0])],
                    return_tensors="pt",
                    padding=True,
                ).to(self.device)
                # ids = self.encoder.generate(**batch)
                text = self.processor.batch_decode(batch, skip_special_tokens=True)
                result_text.append(text)
                result_ids.append(batch)
        # flatten the list
        result_text = [item for sublist in result_text for item in sublist]
        result_ids = [item.cpu().numpy() for sublist in result_ids for item in sublist]
        results = {
            "embeddings": result_ids,
            "captions": result_text,
        }
        return results


class BLIP2Embedder(ImageEmbedder):
    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        self.processor = Blip2Processor.from_pretrained(self.config["processor"])
        self.encoder = Blip2ForConditionalGeneration.from_pretrained(
            self.config["model"],
            torch_dtype=torch.float16,
            device_map="auto",
        )
        # if torch.cuda.device_count() > 1:
        #     print(f"Let's use {torch.cuda.device_count()} GPUs!")
        #     # Wrap the model for multi-GPU usage
        #     self.encoder = nn.DataParallel(self.encoder).to(self.device)
        # else:
        #     self.encoder.to(self.device)
        # self.text_prompt = "A picture of "

    def preprocess(self, images: torch.Tensor) -> dict:
        """Preprocess images for pretrained BLIP2Embedder

        Parameters:
            images (torch.Tensor): tensor of images in shape (n_images, n_channels, height, width)

        Returns:
            images (dict): processed images are stored in key "pixel_values", each image shape is (3, 224, 224)
        """
        # images = _check_image_tensor_dimensions(images)
        images = [torchvision.transforms.ToPILImage()(img) for img in images]
        images = self.processor(
            images=images,
            return_tensors="pt",
            # padding=True,
        ).to(self.device, torch.float16)
        return images

    def embed(self, images: torch.Tensor):
        result_text = []
        result_ids = []
        image_ids = []
        current_image_id = 0
        print("Embedding with BLIP2...")
        with torch.no_grad():
            for i in tqdm(range(0, len(images), self.batch_size)):
                # ------- debugging code start ------------
                ###### do the input images make sense? ####
                # batch = images[100:101]
                # image_tensor = batch.squeeze(0)
                # image_np = image_tensor.numpy().transpose(1,2,0)
                # import matplotlib.pyplot as plt
                # plt.imshow(image_np)
                # plt.show()
                # ------- debugging code end -------------

                batch = images[i : i + self.batch_size]
                # batch = batch.to(self.device)
                batch = self.preprocess(batch)

                # ------- debugging code start ------------
                ######## is the preprocessing introducing any bugs? ######
                # batch = images[100:101]
                # batch_PIL = [torchvision.transforms.ToPILImage()(img) for img in batch]
                # import matplotlib.pyplot as plt
                # plt.imshow(np.asarray(batch_PIL[0]))
                # plt.show()
                #
                #
                # import requests
                # img_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/demo.jpg'
                # raw_image = Image.open(requests.get(img_url, stream=True).raw).convert('RGB')
                # inputs = self.processor(images=raw_image, return_tensors="pt")
                # out = self.encoder.generate(**inputs)
                # self.processor.decode(out[0], skip_special_tokens=True)
                #
                # batch_processed = self.processor(
                #     images=batch_PIL,
                #     return_tensors="pt",
                # )
                # print(batch_processed["pixel_values"].dtype)
                # test_image = batch_processed["pixel_values"]
                # test_image = test_image.squeeze(0)
                # test_image = test_image.numpy()
                # test_image = test_image.transpose(1,2,0)
                # plt.imshow(test_image)
                # plt.show()
                #
                # batch_processed = self.processor(
                #     images=batch_PIL,
                #     return_tensors="pt",
                #     # padding=True,
                # )
                # print(batch_processed["pixel_values"].dtype)
                # batch_processed = batch_processed.to(self.device)
                # image_tensor = batch_processed["pixel_values"] # assuming 1 image
                # image_tensor = image_tensor.squeeze(0)  # Now the shape is [3, 224, 224]
                # image_np = image_tensor.cpu().numpy()
                # image_np = image_np.transpose(1,2,0)
                # plt.imshow(image_np)
                # plt.show()
                #
                # ids = self.encoder.generate(**batch_processed)
                # text = self.processor.batch_decode(ids, skip_special_tokens=True)
                # ------- debugging code end --------------

                if isinstance(self.encoder, torch.nn.DataParallel):
                    ids = self.encoder.module.generate(**batch)
                else:
                    ids = self.encoder.generate(**batch)
                text = self.processor.batch_decode(ids, skip_special_tokens=True)
                result_ids.append(ids)
                result_text.append(text)
                for el in range(len(text)):
                    # print(f"Image {current_image_id}: {text[el]}")
                    image_ids.append(current_image_id)
                    current_image_id += 1
        # flatten the list
        result_ids = [item.cpu().numpy() for sublist in result_ids for item in sublist]
        result_text = [item for sublist in result_text for item in sublist]
        # results = {
        #     "ids": result_ids,
        #     "text": result_text,
        #     "image_ids": image_ids,
        # }
        return result_text


class DINOEmbedder(ImageEmbedder, nn.Module):
    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        nn.Module.__init__(self)
        self.encoder = AutoModel.from_pretrained(config["model"])
        self.encoder.to(device)
        # self.encoder.eval()
        self.processor = AutoImageProcessor.from_pretrained(config["processor"])

    def preprocess(self, images: torch.Tensor) -> dict:
        images = _check_image_tensor_dimensions(images)
        images = [torchvision.transforms.ToPILImage()(img) for img in images]
        images = self.processor(images, return_tensors="pt").to(self.device)
        return images

    # noinspection PyPep8
    @torch.no_grad()
    def embed(self, images: torch.Tensor) -> np.ndarray:
        results = []
        print("Embedding with DINO...")
        for i in tqdm(range(0, images.shape[0], self.batch_size)):
            batch = images[i : i + self.batch_size]
            batch = self.preprocess(batch)
            batch = self.encoder(**batch)
            batch = batch.last_hidden_state
            batch = batch.mean(dim=1)
            batch = batch / batch.norm(dim=1, keepdim=True)
            # below gives the same result as above for normalizing the embeddings
            # batch_norm = torch.linalg.norm(batch, dim=1, keepdim=True)  # Compute the norm along the dimension of each item
            # batch = batch / batch_norm
            results.append(batch)
            # results.append(batch["image_embeds"])
        results = torch.cat(results, dim=0).cpu().numpy()
        return results


class ViTEmbedder(ImageEmbedder):
    # TODO: finish implementing ViT

    def __init__(self, config: dict, device: torch.device) -> None:
        super().__init__(config, device)
        self.encoder = vit_b_16(weights=ViT_B_16_Weights)
        self.encoder.to(self.device)
        self.processor = ViT_B_16_Weights.transforms
        self.encoder.to(device)
        self.encoder.eval()

    def preprocess(self, images: torch.Tensor) -> dict:
        pass

    def embed(self, images: torch.Tensor) -> np.ndarray:
        pass


def _check_image_tensor_dimensions(images: torch.Tensor):
    """
    Check if image tensor is in (n_samples, n_channels, height, width) format.
    If not, convert it to that format.

    Args:
        images (torch.Tensor): (n_samples, n_channels, height, width)

    Returns:
        images (torch.Tensor): (n_samples, n_channels, height, width)
    """
    try:
        assert images.shape[1] == 3
    except AssertionError:
        print("Images must be in (n_samples, n_channels, height, width) format.")
        if images.shape[3] == 3:
            images = images.permute(0, 3, 1, 2)
        else:
            raise ValueError(
                "Cannot interpret the dimensions of this image tensor."
                "Check if the shape is (n_samples, n_channels, height, width)."
            )
    return images
