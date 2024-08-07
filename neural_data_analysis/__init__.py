from .analysis import (
    average_across_iterations,
    embedder_config,
    embedder_from_spec,
    append_model_scores,
    calc_firing_rates,
    CLIPEmbedder,
    create_image_embeddings,
    dataframe_from_cells,
    DINOEmbedder,
    Electrode,
    evaluate_model_performance,
    Event,
    LinearModelWrapper,
    MLPModelWrapper,
    Neuron,
    calculate_model_performance,
    ResNet50Embedder,
    subset_cells,
    t_test,
    TextEmbedder,
    SGPTEmbedder,
    brain_area_dict,
    get_stem,
    get_synonyms_wordnet,
    create_word_groups,
    reduce_word_list_synonyms,
    create_excluded_words,
)

from .plotting import (
    model_performance_by_brain_area,
    model_performance_by_time,
    plot_pairwise_distance_heatmap,
    plot_confusion_matrix,
    plot_ecdf,
    plot_model_predictions,
    plot_object_detection_result,
    plot_scatter_with_images,
    plot_tsne_projections,
    plot_variance_explained,
    plot_raster_psth,
    compute_psth,
    compute_psth_per_category,
    plot_gantt_bar_chart,
    create_rose_plot,
    plot_binary_matrix_heatmap,
)
from .utils import (
    correct_filepath,
    create_order_index,
    get_brain_area_abbreviation,
    get_nwb_files,
    recursive_dict_update,
    remove_lateralization,
    setup_logger,
    setup_default_logger,
)

__author__ = "Kevin J. M. Le"
__email__ = "kvnjmle@caltech.edu"
__version__ = "0.0.1"
__all__ = [f for f in dir() if not f.startswith("_")]
