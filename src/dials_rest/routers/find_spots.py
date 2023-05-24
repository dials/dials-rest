import logging
import time
from enum import Enum
from pathlib import Path
from typing import Annotated

import pydantic
from cctbx import uctbx
from dials.algorithms.spot_finding import per_image_analysis
from dials.array_family import flex
from dials.command_line.find_spots import phil_scope as find_spots_phil_scope
from dials.util import phil
from dxtbx.model.experiment_list import ExperimentListFactory
from fastapi import APIRouter, Body, Depends

from ..auth import JWTBearer

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/find_spots",
    tags=["spotfinding"],
    dependencies=[Depends(JWTBearer())],
    responses={404: {"description": "Not found"}},
)


class ThresholdAlgorithm(Enum):
    DISPERSION = "dispersion"


class PerImageAnalysisParameters(pydantic.BaseModel):
    filename: Path
    d_min: pydantic.PositiveFloat | None = None
    d_max: pydantic.PositiveFloat | None = 40
    threshold_algorithm: ThresholdAlgorithm = ThresholdAlgorithm.DISPERSION
    disable_parallax_correction: bool = True
    scan_range: tuple[int, int] | None = None
    filter_ice: bool = True
    ice_rings_width: pydantic.NonNegativeFloat = 0.004

    @pydantic.validator("scan_range", pre=True)
    def str_to_tuple(cls, v):
        if isinstance(v, str):
            return tuple(int(i) for i in v.split(","))
        elif v:
            return tuple(v)
        return None


class PerImageAnalysisResults(pydantic.BaseModel):
    n_spots_4A: pydantic.NonNegativeInt
    n_spots_no_ice: pydantic.NonNegativeInt
    n_spots_total: pydantic.NonNegativeInt
    total_intensity: pydantic.NonNegativeFloat
    d_min_distl_method_1: float | None = None
    d_min_distl_method_2: float | None = None
    estimated_d_min: float | None = None
    noisiness_method_1: float | None = None
    noisiness_method_2: float | None = None

    class Config:
        schema_extra = {
            "example": {
                "n_spots_4A": 36,
                "n_spots_no_ice": 44,
                "n_spots_total": 49,
                "total_intensity": 56848.0,
                "d_min_distl_method_1": 4.234420130210043,
                "d_min_distl_method_2": 4.053322019536269,
                "estimated_d_min": 3.517157644985513,
                "noisiness_method_1": 0.15019762845849802,
                "noisiness_method_2": 0.46842105263157896,
            }
        }


find_spots_examples = {
    "Single image example": {
        "description": "Perform spotfinding on a single image with a high resolution cutoff of 3.5 Å",
        "value": {
            "filename": "/path/to/image_00001.cbf",
            "d_min": 3.5,
        },
    },
    "Image template example": {
        "description": "Perform spotfinding on the second image matching the given filename template",
        "value": {
            "filename": "/path/to/image_#####.cbf",
            "scan_range": [1, 1],
        },
    },
    "Multi-image format example": {
        "description": "Perform spotfinding on the fifth image of a NeXus file, filtering out spots at ice ring resolutions",
        "value": {
            "filename": "/path/to/master.h5",
            "scan_range": [4, 4],
            "filter_ice": True,
        },
    },
}


@router.post("/")
async def find_spots(
    params: Annotated[PerImageAnalysisParameters, Body(examples=find_spots_examples)]
) -> PerImageAnalysisResults:
    if "#" in params.filename.stem:
        experiments = ExperimentListFactory.from_templates([params.filename])
    else:
        experiments = ExperimentListFactory.from_filenames([params.filename])
    if params.scan_range and len(experiments) > 1:
        # This means we've imported a sequence of still image: select
        # only the experiment, i.e. image, we're interested in
        start, end = params.scan_range
        experiments = experiments[start - 1 : end]

    phil_params = find_spots_phil_scope.fetch(source=phil.parse("")).extract()
    phil_params.spotfinder.scan_range = (params.scan_range,)
    phil_params.spotfinder.threshold.algorithm = params.threshold_algorithm.value
    phil_params.spotfinder.filter.disable_parallax_correction = (
        params.disable_parallax_correction
    )

    t0 = time.perf_counter()
    reflections = flex.reflection_table.from_observations(experiments, phil_params)

    if params.d_min or params.d_max:
        reflections = _filter_by_resolution(
            experiments, reflections, d_min=params.d_min, d_max=params.d_max
        )

    t1 = time.perf_counter()
    logger.info("Spotfinding took %.2f seconds", t1 - t0)

    reflections.centroid_px_to_mm(experiments)
    reflections.map_centroids_to_reciprocal_space(experiments)
    stats = per_image_analysis.stats_for_reflection_table(
        reflections,
        filter_ice=params.filter_ice,
        ice_rings_width=params.ice_rings_width,
    )._asdict()
    t2 = time.perf_counter()
    logger.info("Resolution analysis took %.2f seconds", t2 - t1)
    logger.info(stats)
    return PerImageAnalysisResults(**stats)


def _filter_by_resolution(experiments, reflections, d_min=None, d_max=None):
    reflections.centroid_px_to_mm(experiments)
    reflections.map_centroids_to_reciprocal_space(experiments)
    d_star_sq = flex.pow2(reflections["rlp"].norms())
    reflections["d"] = uctbx.d_star_sq_as_d(d_star_sq)
    # Filter based on resolution
    if d_min is not None:
        selection = reflections["d"] >= d_min
        reflections = reflections.select(selection)
        logger.debug(f"Selected {len(reflections)} reflections with d >= {d_min:f}")

    # Filter based on resolution
    if d_max is not None:
        selection = reflections["d"] <= d_max
        reflections = reflections.select(selection)
        logger.debug(f"Selected {len(reflections)} reflections with d <= {d_max:f}")
    return reflections
