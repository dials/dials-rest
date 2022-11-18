import time
from enum import Enum
from pathlib import Path

import pydantic
from dials.command_line import export_bitmaps
from dxtbx.model.experiment_list import ExperimentListFactory
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/export_bitmap",
    tags=["image"],
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


class ExportBitmapParams(pydantic.BaseModel):
    filename: Path
    image_index: pydantic.PositiveInt | None = 1
    format: FormatEnum = FormatEnum.png
    binning: pydantic.PositiveInt = 1
    display: DisplayEnum = DisplayEnum.image
    colour_scheme: ColourSchemes = ColourSchemes.greyscale
    brightness: pydantic.NonNegativeFloat = 10


@router.get("/")
async def image_as_bitmap(params: ExportBitmapParams):
    expts = ExperimentListFactory.from_filenames([params.filename])
    imageset = expts.imagesets()[0]

    if params.filename.suffix in {".h5", ".nxs"}:
        image = imageset[params.image_index - 1 : params.image_index]
    else:
        b0 = imageset.get_scan().get_batch_offset()
        image = imageset[b0 : b0 + 1]

    phil_params = export_bitmaps.phil_scope.extract()
    phil_params.format = params.format
    phil_params.binning = params.binning
    phil_params.brightness = params.brightness
    phil_params.colour_scheme = params.colour_scheme
    phil_params.display = params.display
    phil_params.output.directory = "/tmp"
    phil_params.output.prefix = str(time.time())
    phil_params.imageset_index = 0

    filenames = export_bitmaps.imageset_as_bitmaps(image, phil_params)

    return FileResponse(filenames[0])
