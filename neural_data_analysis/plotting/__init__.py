from .firing_rate_over_time import plot_neuron_firing_rate

from .model_results import (
    model_performance_by_brain_area,
    model_performance_by_time,
    plot_confusion_matrix,
    plot_model_predictions,
    plot_object_detection_result,
)
from .plotting import (
    plot_heatmap_pairwise_distance,
    plot_ecdf,
    plot_scatter_with_images,
    plot_scatter,
    plot_tsne_projections,
    plot_variance_explained,
    plot_histogram,
    create_polar_plot_tuning_curve,
    plot_heatmap_binary_matrix,
    plot_heatmap_matrix,
)
from .raster_psth import (
    plot_raster_psth,
    compute_psth,
    plot_gantt_bar_chart,
    compute_psth_per_category,
)

__version__ = "0.0.1"
__description__ = "A package for plotting functions."
__all__ = [f for f in dir() if not f.startswith("_")]
