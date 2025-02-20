"""Utilities to process images related to product processing."""

from typing import cast, overload

import numpy as np
import xarray

# Helper type for image processing purposes. The same operations work both for EO
# DataArrays and Numpy arrays.
ImageArray_ = np.ndarray | xarray.DataArray


@overload
def image_to_dtype_range(
    img: np.ndarray,
    dtype: np.dtype,
    offset: float | None = None,
    scale: float | None = None,
) -> tuple[xarray.DataArray, float, float]: ...


@overload
def image_to_dtype_range(
    img: xarray.DataArray,
    dtype: np.dtype,
    offset: float | None = None,
    scale: float | None = None,
) -> tuple[xarray.DataArray, float, float]: ...


def image_to_dtype_range(
    img: ImageArray_,
    dtype: np.dtype,
    offset: float | None = None,
    scale: float | None = None,
) -> tuple[ImageArray_, float, float]:
    """Normalize an image to the bounds of whatever numpy datatype. E.g. np.uint16
    results in a np.uint16 image with values between entire range [0, 65535]

    Parameters
    ----------
    img
        Image to normalize
    dtype
        Target data type, only integer subtypes currently sensible and are supported
    offset, optional
        Offset if that was already precomputed. If not, it will be calculated from `arr`
    scale, optional
        Scale if that was already precomputed. If not, it will be calculated from `arr`

    Returns
    -------
        The normalized image along casted to given data type, along with the offset and
        scale used to normalize it

    Raises
    ------
    ValueError
        Unsupported data type
    """
    if np.issubdtype(dtype, np.integer):
        type_info = np.iinfo(dtype)
    else:
        e_ = f"Unsupported dtype {dtype} for normalization"
        raise ValueError(e_)

    dtype_min = type_info.min
    dtype_max = type_info.max

    if offset is None or scale is None:
        offset_ = cast(float, np.min(img))
        scale_ = cast(float, np.max(img) - offset_)
    else:
        offset_ = offset
        scale_ = scale

    normed_to_0_1 = (img - offset_) / scale_

    normalized_image = normed_to_0_1 * (dtype_max - dtype_min) + dtype_min
    normalized_image = normalized_image.astype(dtype)

    return normalized_image, offset_, scale_


@overload
def image_to_uint16_range(img: np.ndarray) -> tuple[np.ndarray, float, float]: ...


@overload
def image_to_uint16_range(
    img: xarray.DataArray,
) -> tuple[xarray.DataArray, float, float]: ...


def image_to_uint16_range(img: ImageArray_) -> tuple[ImageArray_, float, float]:
    """Normalise image to bounds of uint16, see above function for details

    Parameters
    ----------
    img
        Image to normalize

    Returns
    -------
        The normalized image along casted to given data type, along with the offset and
        scale used to normalize it
    """
    return image_to_dtype_range(img, np.dtype(np.uint16))


@overload
def image_to_original_range(
    img: np.ndarray,
    offset: float,
    scale: float,
    dtype: np.dtype | None = None,
) -> xarray.DataArray: ...


@overload
def image_to_original_range(
    img: xarray.DataArray,
    offset: float,
    scale: float,
    dtype: np.dtype | None = None,
) -> xarray.DataArray: ...


def image_to_original_range(
    img: ImageArray_,
    offset: float,
    scale: float,
    dtype: np.dtype | None = None,
) -> ImageArray_:
    """Revert normalisation applied to an image. The image 'arr' must have the same
    data type as the result from normalization, or it must be given separately

    Parameters
    ----------
    arr
        Image to revert back to original values
    offset
        Offset that was applied to the image
    scale
        Scale that was applied to the image
    dtype, optional
        The data type that the image was casted to during normalization, by default None
        where the data type of `arr` will be assumed to be correct.

    Returns
    -------
        Image that is back in original range of values before normalization

    Raises
    ------
    ValueError
        Unsupported data type
    """
    if not dtype:
        dtype = img.dtype

    # Check real bounds from numpy data types
    if np.issubdtype(dtype, np.integer) and isinstance(dtype, np.dtype):
        type_info = np.iinfo(dtype)
    else:
        e_ = f"Unsupported dtype {dtype} for normalization"
        raise ValueError(e_)

    dtype_min = type_info.min
    dtype_max = type_info.max

    # Reverse the normalization
    denormed_to_0_1 = (img - dtype_min) / (dtype_max - dtype_min)
    original_image = denormed_to_0_1 * scale + offset

    return original_image
