import logging
import time
from enum import Enum
from pathlib import Path

import pydantic
from dials.command_line import export_bitmaps
from dxtbx.model.experiment_list import ExperimentListFactory
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from ..auth import JWTBearer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/export_bitmap",
    tags=["image"],
    dependencies=[Depends(JWTBearer())],
    responses={404: {"description": "Not found"}},
)


class FormatEnum(str, Enum):
    jpeg = "jpeg"
    tiff = "tiff"
    png = "png"


class ColourSchemes(str, Enum):
    greyscale = "greyscale"
    rainbow = "rainbow"
    heatmap = "heatmap"
    inverse_greyscale = "inverse_greyscale"


class DisplayEnum(str, Enum):
    image = "image"
    mean = "mean"
    variance = "variance"
    dispersion = "dispersion"
    sigma_b = "sigma_b"
    sigma_s = "sigma_s"
    threshold = "threshold"
    global_threshold = "global_threshold"


class ResolutionRingsParams(pydantic.BaseModel):
    show: bool = False
    number: pydantic.PositiveInt = 5
    fontsize: pydantic.PositiveInt = 30


class ExportBitmapParams(pydantic.BaseModel):
    filename: Path
    image_index: pydantic.PositiveInt | None = 1
    format: FormatEnum = FormatEnum.png
    binning: pydantic.PositiveInt = 1
    display: DisplayEnum = DisplayEnum.image
    colour_scheme: ColourSchemes = ColourSchemes.greyscale
    brightness: pydantic.NonNegativeFloat = 10
    resolution_rings: ResolutionRingsParams = ResolutionRingsParams()


@router.post("/")
async def image_as_bitmap(params: ExportBitmapParams):
    if "#" in params.filename.stem:
        # A filename template e.g. image_#####.cbf
        expts = ExperimentListFactory.from_templates([params.filename])
        imageset = expts[0].imageset[params.image_index - 1 : params.image_index]
    elif params.filename.suffix in {".h5", ".nxs"}:
        # A multi-image NeXus file
        # Use load_models=False workaround to ensure that we only construct a
        # single experiment object for the specific image we're interested in
        expt = ExperimentListFactory.from_filenames(
            [params.filename], load_models=False
        )[0]
        expt.load_models(index=params.image_index - 1)
        imageset = expt.imageset[params.image_index - 1 : params.image_index]
    else:
        # An individual image file e.g. image_00001.cbf
        expts = ExperimentListFactory.from_filenames([params.filename])
        imageset = expts.imagesets()[0]
        b0 = imageset.get_scan().get_batch_offset()
        imageset = imageset[b0 : b0 + 1]

    phil_params = export_bitmaps.phil_scope.extract()
    phil_params.format = params.format
    phil_params.binning = params.binning
    phil_params.brightness = params.brightness
    phil_params.colour_scheme = params.colour_scheme
    phil_params.display = params.display
    phil_params.output.directory = "/tmp"
    phil_params.output.prefix = str(time.time())
    phil_params.imageset_index = 0
    phil_params.resolution_rings.show = params.resolution_rings.show
    phil_params.resolution_rings.number = params.resolution_rings.number
    phil_params.resolution_rings.fontsize = params.resolution_rings.fontsize

    logger.info(f"Exporting bitmap with parameters:\n{params!r}")
    filenames = export_bitmaps.imageset_as_bitmaps(imageset, phil_params)

    return FileResponse(filenames[0])
