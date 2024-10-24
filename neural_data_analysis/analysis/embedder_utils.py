import torch

from neural_data_analysis.analysis.ImageEmbedder import (
    VGG16Embedder,
    ResNet50Embedder,
    CLIPEmbedder,
    DETREmbedder,
    DINOEmbedder,
    BLIPEmbedder,
    BLIP2Embedder,
    ViTEmbedder,
)
from neural_data_analysis.analysis.TextEmbedder import SGPTEmbedder
import yaml
import numpy as np
from moviepy.editor import VideoFileClip
from ..constants import embedder_configs


# noinspection PyShadowingNames
def embedder_from_spec(
    embedder_name: str, embedder_configs=None, device: str = None
) -> (
    VGG16Embedder
    | ResNet50Embedder
    | CLIPEmbedder
    | DETREmbedder
    | DINOEmbedder
    | BLIPEmbedder
    | BLIP2Embedder
    | ViTEmbedder
    | SGPTEmbedder
):
    """
    Create an embedder from a specification dictionary.

    Args:
        embedder_configs (dict): dictionary of embedder specifications
        embedder_name (str): name of Embedder to create
        device (str): device to use for embedding (cpu or cuda)

    Returns:
        embedder (ImageEmbedder): model to embed images
    """
    if embedder_configs is None:
        embedder_configs = embedder_configs

    if device is None:
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
    else:
        device = device
    if embedder_name == "VGG16Embedder":
        spec = embedder_configs[embedder_name]
        return VGG16Embedder(spec, device)
    elif embedder_name == "ResNet50Embedder":
        spec = embedder_configs[embedder_name]
        return ResNet50Embedder(spec, device)
    elif embedder_name == "CLIPEmbedder":
        spec = embedder_configs[embedder_name]
        return CLIPEmbedder(spec, device)
    elif embedder_name == "DETREmbedder":
        spec = embedder_configs[embedder_name]
        return DETREmbedder(spec, device)
    elif embedder_name == "DINOEmbedder":
        spec = embedder_configs[embedder_name]
        return DINOEmbedder(spec, device)
    elif embedder_name == "BLIPEmbedder":
        spec = embedder_configs[embedder_name]
        return BLIPEmbedder(spec, device)
    elif embedder_name == "BLIP2Embedder":
        spec = embedder_configs[embedder_name]
        return BLIP2Embedder(spec, device)
    elif embedder_name == "ViT_B_16Embedder":
        spec = embedder_configs[embedder_name]
        return ViTEmbedder(spec, device)
    elif embedder_name == "SGPTEmbedder":
        spec = embedder_configs[embedder_name]
        return SGPTEmbedder(spec, device)
    else:
        raise NotImplementedError(f"Embedder {embedder_name} not implemented.")


# NOT USED
# noinspection PyShadowingNames
def create_image_embeddings(
    images: torch.Tensor,
    embedder_list: list[str],
    embedder_config: dict,
) -> dict[str, torch.Tensor]:
    """
    Create embeddings for a list of images using a list of embedders.

    Args:
        images (torch.Tensor): images to embed
        embedder_list (list): list of embedder names
        embedder_config (dict): dictionary of embedder specifications

    Returns:
        embeddings (dict): dictionary of embeddings
    """
    embeddings = {}
    for embedder_name in embedder_list:
        print(f"Model {embedder_name}")
        image_embedder = embedder_from_spec(embedder_name, embedder_configs)
        embedding = image_embedder.embed(images)
        embeddings[embedder_config[embedder_name]["embedding_name"]] = embedding
    return embeddings


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--embedder", type=str, default="ResNet50Embedder")
    parser.add_argument("--device", type=str, default="cuda")
    args = parser.parse_args()
    # args.embedder = "BLIP2Embedder"
    # args.embedder = "VGG16Embedder"
    args.embedder = "SGPTEmbedder"
    args.device = "cuda"

    print("Embedder:", args.embedder)
    embedder = embedder_from_spec(embedder_name=args.embedder, device=args.device)
    print(embedder)
    # images = torch.rand(32, 3, 224, 224)
    with open("config.yaml", "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # load video,
    video_path = "./data/stimulus/short_downsampled.avi"
    clip = VideoFileClip(video_path)
    frames = clip.iter_frames()
    images = np.array([frame for frame in frames])
    audio = clip.audio

    # images to tensor
    images = torch.from_numpy(images)

    results = embedder.embed(images)
    # save results as text in csv files via pandas
    import pandas as pd

    dataframe = pd.DataFrame(results)
    dataframe.to_csv("./annotations/blip_results.csv")
