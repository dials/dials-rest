from __future__ import annotations

import io
import logging
from enum import Enum
from pathlib import Path
from typing import Annotated

import PIL.Image
import pydantic
from cctbx import sgtbx, uctbx
from dials.util import export_bitmaps
from dxtbx.model.experiment_list import ExperimentListFactory
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import Response

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
    fill: str = "red"


class IceRingsParams(pydantic.BaseModel):
    show: bool = False
    fontsize: pydantic.PositiveInt = 30
    fill: str = "blue"
    unit_cell: tuple[
        float, float, float, float, float, float
    ] = export_bitmaps.HEXAGONAL_ICE_UNIT_CELL.parameters()
    space_group: int | str = (
        export_bitmaps.HEXAGONAL_ICE_SPACE_GROUP.type().lookup_symbol()
    )

    @pydantic.validator("unit_cell", pre=True)
    def check_unit_cell(cls, v):
        if not v:
            return None
        orig_v = v
        if isinstance(v, str):
            v = v.replace(",", " ").split()
        v = [float(v) for v in v]
        try:
            uctbx.unit_cell(v)
        except Exception:
            raise ValueError(f"Invalid unit_cell {orig_v}")
        return v

    @pydantic.validator("space_group", pre=True)
    def check_space_group(cls, v):
        if not v:
            return None
        try:
            sgtbx.space_group_info(v)
        except Exception:
            raise ValueError(f"Invalid space group {v}")
        return v


class ExportBitmapParams(pydantic.BaseModel):
    filename: Path
    image_index: pydantic.PositiveInt = 1
    format: FormatEnum = FormatEnum.png
    binning: pydantic.PositiveInt = 1
    display: DisplayEnum = DisplayEnum.image
    colour_scheme: ColourSchemes = ColourSchemes.greyscale
    brightness: pydantic.NonNegativeFloat = 10
    resolution_rings: ResolutionRingsParams = ResolutionRingsParams()
    ice_rings: IceRingsParams = IceRingsParams()


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
    response_class=Response,
    responses={
        200: {
            "description": "Returns the image as a byte string",
            "content": {"image/png": {}},
        },
        404: {"description": "File not found"},
    },
)
async def image_as_bitmap(
    params: Annotated[ExportBitmapParams, Body(examples=image_as_bitmap_examples)]
) -> Response:
    try:
        if "#" in params.filename.stem:
            # A filename template e.g. image_#####.cbf
            expt = ExperimentListFactory.from_templates([params.filename])[0]
        elif params.filename.suffix in {".h5", ".nxs"}:
            # A multi-image NeXus file
            # Use load_models=False workaround to ensure that we only construct a
            # single experiment object for the specific image we're interested in
            expt = ExperimentListFactory.from_filenames(
                [params.filename], load_models=False
            )[0]
            expt.load_models(index=params.image_index - 1)
        else:
            # An individual image file e.g. image_00001.cbf
            expt = ExperimentListFactory.from_filenames([params.filename])[0]
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

    logger.info(f"Exporting bitmap with parameters:\n{params!r}")
    flex_img = next(
        export_bitmaps.imageset_as_flex_image(
            expt.imageset,
            images=[params.image_index],
            brightness=params.brightness,
            binning=params.binning,
            display=export_bitmaps.Display(params.display),
            colour_scheme=export_bitmaps.ColourScheme[params.colour_scheme.upper()],
        )
    )
    pil_img = PIL.Image.frombytes(
        "RGB", (flex_img.ex_size2(), flex_img.ex_size1()), flex_img.as_bytes()
    )

    if params.resolution_rings.show:
        export_bitmaps.draw_resolution_rings(
            expt.imageset,
            pil_img,
            flex_img,
            n_rings=params.resolution_rings.number,
            fill=params.resolution_rings.fill,
            fontsize=params.resolution_rings.fontsize,
            binning=params.binning,
        )
    if params.ice_rings.show:
        export_bitmaps.draw_ice_rings(
            expt.imageset,
            pil_img,
            flex_img,
            unit_cell=uctbx.unit_cell(params.ice_rings.unit_cell),
            space_group=sgtbx.space_group_info(params.ice_rings.space_group).group(),
            fill=params.ice_rings.fill,
            fontsize=params.ice_rings.fontsize,
            binning=params.binning,
        )

    img_bytes = io.BytesIO()
    pil_img.save(img_bytes, format=params.format.value)
    return Response(
        content=img_bytes.getvalue(), media_type=f"image/{params.format.value}"
    )
