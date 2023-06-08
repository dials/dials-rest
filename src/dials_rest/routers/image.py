import logging
import time
from enum import Enum
from pathlib import Path
from typing import Annotated

import pydantic
from dials.command_line import export_bitmaps
from dxtbx.model.experiment_list import ExperimentListFactory
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import FileResponse

from ..auth import JWTBearer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/export_bitmap",
    tags=["images"],
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
    image_index: pydantic.PositiveInt = 1
    format: FormatEnum = FormatEnum.png
    binning: pydantic.PositiveInt = 1
    display: DisplayEnum = DisplayEnum.image
    colour_scheme: ColourSchemes = ColourSchemes.greyscale
    brightness: pydantic.NonNegativeFloat = 10
    resolution_rings: ResolutionRingsParams = ResolutionRingsParams()


image_as_bitmap_examples = {
    "Single image example": {
        "description": "Convert a cbf image to a png with binning of pixel to reduce overall image size",
        "value": {
            "filename": "/path/to/image_00001.cbf",
            "binning": 4,
        },
    },
    "Image template example": {
        "description": "Generate a png for the second image matching the given filename template",
        "value": {
            "filename": "/path/to/image_#####.cbf",
            "image_index": 2,
            "binning": 4,
        },
    },
    "Multi-image format example": {
        "description": "Generate a png for the fifth image of a NeXus file, modifying the default colour scheme",
        "value": {
            "filename": "/path/to/master.h5",
            "image_index": 5,
            "binning": 4,
            "colour_scheme": "inverse_greyscale",
        },
    },
    "Resolution rings": {
        "description": "Generate a png with resolution ring overlays",
        "value": {
            "filename": "/path/to/image_00001.cbf",
            "binning": 2,
            "resolution_rings": {"show": True, "number": 10},
        },
    },
}


@router.post(
    "/",
    status_code=200,
    response_class=FileResponse,
    responses={
        200: {"description": "Asynchronously streams the file as the response"},
        404: {"description": "File not found"},
    },
)
async def image_as_bitmap(
    params: Annotated[ExportBitmapParams, Body(examples=image_as_bitmap_examples)]
) -> FileResponse:
    try:
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
    except FileNotFoundError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        logger.exception(e)
        msg = str(e)
        if "does not match any files" in msg:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=msg,
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

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
