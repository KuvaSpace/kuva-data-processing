from pathlib import Path
from typing import cast

import numpy as np
import rasterio as rio
from kuva_metadata import MetadataLevel1AB, MetadataLevel1C
from pint import UnitRegistry
from rasterio.io import MemoryFile
from shapely import Polygon

from kuva_reader import image_footprint

from .product_base import NUM_THREADS, ProductBase


def _convert_to_radiance(
    ds: rio.DatasetReader, metadata: MetadataLevel1AB | MetadataLevel1C
):
    if metadata.image.measured_quantity_name == "TOA_REFLECTANCE":
        image_dtype = ds.profile["dtype"]
        coeffs = np.array(
            [band.toa_radiance_to_reflectance_factor for band in metadata.image.bands]
        ).astype(np.float32)
        _validate_coefficients(coeffs, ds.count)

        data = (ds.read() / coeffs[:, np.newaxis, np.newaxis]).astype(image_dtype)
        ds.close()
        return _create_in_memory_dataset(ds, data)
    else:
        e_ = (
            "Can only convert `TOA_REFLECTANCE` to `TOA_RADIANCE`. The measured"
            f" unit is `{metadata.image.measured_quantity_name}`."
        )
        raise ValueError(e_)


def _validate_in_memory_dataset(original_ds, new_ds):
    """Validate the properties of the new in-memory dataset against the original
    image."""
    errors = []
    if new_ds.driver != original_ds.driver:
        errors.append(f"Driver mismatch: {new_ds.driver} != {original_ds.driver}")
    if new_ds.count != original_ds.count:
        errors.append(f"Band count mismatch: {new_ds.count} != {original_ds.count}")
    if new_ds.width != original_ds.width:
        errors.append(f"Width mismatch: {new_ds.width} != {original_ds.width}")
    if new_ds.height != original_ds.height:
        errors.append(f"Height mismatch: {new_ds.height} != {original_ds.height}")
    if new_ds.crs != original_ds.crs:
        errors.append(f"CRS mismatch: {new_ds.crs} != {original_ds.crs}")
    if new_ds.transform != original_ds.transform:
        errors.append(
            f"Transform mismatch: {new_ds.transform} != {original_ds.transform}"
        )
    if errors:
        raise ValueError("In-memory dataset validation failed:\n" + "\n".join(errors))


def _create_in_memory_dataset(original_ds, data):
    """Helper function to create an in-memory dataset with modified data."""
    new_dataset = MemoryFile().open(
        driver=original_ds.driver,
        height=original_ds.height,
        width=original_ds.width,
        count=original_ds.count,
        dtype=data.dtype,
        crs=original_ds.crs,
        transform=original_ds.transform,
        num_threads=NUM_THREADS,
    )
    new_dataset.write(data)

    # Probably redundant, but doesn't hurt to check anyway
    _validate_in_memory_dataset(original_ds, new_dataset)

    return new_dataset


def _validate_coefficients(coeffs, image_bands_count):
    """Validate that the coefficients array matches the number of image bands and
    contains no zero values."""
    if coeffs.shape[0] != image_bands_count:
        raise ValueError(
            f"Mismatch between coefficients ({coeffs.shape[0]}) and image "
            f"bands ({image_bands_count})."
        )
    if np.any(coeffs == 0):
        e_ = "Coefficients contain zero values, which are not allowed."
        raise ValueError(e_)


class Level1ABProduct(ProductBase[MetadataLevel1AB]):
    """
    Level 1AB products combine multiple L0 products into a band aligned product.

    Changes to them are only performed at the metadata level where results may be
    cached for further use.

    Parameters
    ----------
    image_path
        Path to the folder containing the L1A or L1B product
    metadata, optional
        Metadata if already read e.g. from a database. By default None, meaning
        automatic fetching from metadata sidecar file
    target_ureg, optional
        Pint Unit Registry to swap to. This is only relevant when parsing data from a
        JSON file, which by default uses the kuva-metadata ureg.

    Attributes
    ----------
    image_path: Path
        Path to the folder containing the image.
    metadata: MetadataLevel1AB
        The metadata associated with the images
    image: rasterio.DatasetReader
        The Rasterio DatasetReader to open the image and other metadata with.
    data_tags: dict
        Tags saved along with the product. The tag "data_unit" shows what the unit of
        the product actually is.
    """

    def __init__(
        self,
        image_path: Path,
        metadata: MetadataLevel1AB | None = None,
        target_ureg: UnitRegistry | None = None,
        convert_to_radiance: bool = False,
    ) -> None:
        super().__init__(image_path, metadata, target_ureg)

        self._image = cast(
            rio.DatasetReader,
            rio.open(self.image_path / "L1B.tif", num_threads=NUM_THREADS),
        )
        self.crs = self._image.crs
        self.data_tags = self._image.tags()

        self.wavelengths = [
            b.wavelength.to("nm").magnitude for b in self.metadata.image.bands
        ]

        if convert_to_radiance:
            self._image = _convert_to_radiance(self._image, self.metadata)

    def __repr__(self):
        """Pretty printing of the object with the most important info"""
        if self.image is not None:
            shape_str = f"({self.image.count}, {self.image.height}, {self.image.width})"
            return (
                f"{self.__class__.__name__} with shape {shape_str} "
                f"and wavelengths {self.wavelengths} (CRS: '{self.crs}'). "
                f"Loaded from: '{self.image_path}'."
            )
        else:
            return f"{self.__class__.__name__} loaded from '{self.image_path}'"

    @property
    def image(self) -> rio.DatasetReader:
        if self._image is None:
            e_ = "Image has been released. Re-open the product to access it again."
            raise RuntimeError(e_)
        return self._image

    def footprint(self, crs="") -> Polygon:
        """The product footprint as a Shapely polygon."""
        return image_footprint(self.image, crs)

    def _get_data_from_sidecar(
        self, sidecar_path: Path, target_ureg: UnitRegistry | None = None
    ) -> MetadataLevel1AB:
        """Read product metadata from the sidecar file attached with the product

        Parameters
        ----------
        sidecar_path
            Path to sidecar JSON
        target_ureg, optional
            Unit registry to change to when validating JSON, by default None
            (kuva-metadata ureg)

        Returns
        -------
            The metadata object
        """
        with (sidecar_path).open("r") as fh:
            if target_ureg is None:
                metadata = MetadataLevel1AB.model_validate_json(fh.read())
            else:
                metadata = cast(
                    MetadataLevel1AB,
                    MetadataLevel1AB.model_validate_json_with_ureg(
                        fh.read(), target_ureg
                    ),
                )

        return metadata

    def get_bad_pixel_mask(
        self, camera: str | None = None, per_band: bool = False
    ) -> rio.DatasetReader:
        """Get the bad pixel mask associated to each camera of the L0 product
        Returns
        -------
            The bad pixel masks of the cameras
        """
        if camera is not None:
            e_ = "Parameter `camera` is not supported in this product level."
            raise ValueError(e_)

        if per_band:
            bad_pixel_filename = self.image_path / "bad_pixel_mask_per_band.tif"
        else:
            bad_pixel_filename = self.image_path / "bad_pixel_mask_aggregated.tif"

        return self._read_array(self.image_path / bad_pixel_filename)

    def get_viewing_angles(self) -> rio.DatasetReader:
        """Get the viewing angles associated with each band

        Returns
        -------
            Per band viewing angles masks of the products
        """

        angles_filename = self.image_path / "viewing_angles.tif"

        return self._read_array(self.image_path / angles_filename)

    def release_memory(self):
        """Explicitely closes the Rasterio DatasetReader and releases the memory of
        the `image` variable.
        """
        if self._image is not None:
            self._image.close()
            del self._image
            self._image = None

    def generate_metadata_file(self) -> None:
        """Write the sidecar files next to the product."""
        metadata_file_name = self.image_path.name + ".json"

        with rio.open(self.image_path / "L1B.tif") as src:
            shape = (src.height, src.width)
            crs_epsg = src.crs.to_epsg()
            geotransform = src.transform
            gsd_w, gsd_h = src.res

        with (self.image_path / metadata_file_name).open("w") as fh:
            fh.write(
                self.metadata.model_dump_json(
                    indent=2,
                    context={
                        "shape": shape,
                        "epsg": crs_epsg,
                        "transform": geotransform,
                        "gsd_w": gsd_w,
                        "gsd_h": gsd_h,
                    },
                )
            )


class Level1CProduct(ProductBase[MetadataLevel1C]):
    """
    Level 1C products are georeferenced and orthorectified L1AB products.

    Parameters
    ----------
    image_path
        Path to the folder containing the L1C product
    metadata, optional
        Metadata if already read e.g. from a database. By default None, meaning
        automatic fetching from metadata sidecar file
    target_ureg, optional
        Pint Unit Registry to swap to. This is only relevant when parsing data from a
        JSON file, which by default uses the kuva-metadata ureg.

    Attributes
    ----------
    image_path: Path
        Path to the folder containing the image.
    metadata: MetadataLevel1C
        The metadata associated with the images
    image: rio.DatasetReader
        The Rasterio DatasetReader to open the image and other metadata with.
    data_tags: dict
        Tags saved along with the product. The tag "data_unit" shows what the unit of
        the product actually is.
    """

    def __init__(
        self,
        image_path: Path,
        metadata: MetadataLevel1C | None = None,
        target_ureg: UnitRegistry | None = None,
        convert_to_radiance: bool = False,
    ) -> None:
        super().__init__(image_path, metadata, target_ureg)

        self._image = cast(
            rio.DatasetReader,
            rio.open(self.image_path / "L1C.tif", num_threads=NUM_THREADS),
        )
        self.data_tags = self._image.tags()
        self.crs = self._image.crs

        self.wavelengths = [
            b.wavelength.to("nm").magnitude for b in self.metadata.image.bands
        ]

        if convert_to_radiance:
            self._image = _convert_to_radiance(self._image, self.metadata)

    def __repr__(self):
        """Pretty printing of the object with the most important info"""
        if self.image is not None:
            shape_str = f"({self.image.count}, {self.image.height}, {self.image.width})"
            return (
                f"{self.__class__.__name__} with shape {shape_str} "
                f"and wavelengths {self.wavelengths} (CRS: '{self.crs}'). "
                f"Loaded from: '{self.image_path}'."
            )
        else:
            return f"{self.__class__.__name__} loaded from '{self.image_path}'"

    @property
    def image(self) -> rio.DatasetReader:
        if self._image is None:
            e_ = "Image has been released. Re-open the product to access it again."
            raise RuntimeError(e_)
        return self._image

    def footprint(self, crs="") -> Polygon:
        """The product footprint as a Shapely polygon."""
        return image_footprint(self.image, crs)

    def _get_data_from_sidecar(
        self, sidecar_path: Path, target_ureg: UnitRegistry | None = None
    ) -> MetadataLevel1C:
        """Read product metadata from the sidecar file attached with the product

        Parameters
        ----------
        sidecar_path
            Path to sidecar JSON
        target_ureg, optional
            Unit registry to change to when validating JSON, by default None
            (kuva-metadata ureg)

        Returns
        -------
            The metadata object
        """
        with (sidecar_path).open("r") as fh:
            if target_ureg is None:
                metadata = MetadataLevel1C.model_validate_json(fh.read())
            else:
                metadata = cast(
                    MetadataLevel1C,
                    MetadataLevel1C.model_validate_json_with_ureg(
                        fh.read(), target_ureg
                    ),
                )

        return metadata

    def get_viewing_angles(self) -> rio.DatasetReader:
        """Get the viewing angles mask associated with each band

        Returns
        -------
            Per band viewing angles masks of the products
        """

        angles_filename = self.image_path / "viewing_angles.tif"

        return self._read_array(self.image_path / angles_filename)

    def release_memory(self):
        """Explicitely closes the Rasterio DatasetReader and releases the memory of
        the `image` variable.
        """
        if self._image is not None:
            self._image.close()
            del self._image
            self._image = None

    def generate_metadata_file(self) -> None:
        """Write the sidecar files next to the product."""
        metadata_file_name = self.image_path.name + ".json"

        with rio.open(self.image_path / "L1C.tif") as src:
            shape = (src.height, src.width)
            crs_epsg = src.crs.to_epsg()
            geotransform = src.transform
            gsd_w, gsd_h = src.res

        with (self.image_path / metadata_file_name).open("w") as fh:
            fh.write(
                self.metadata.model_dump_json(
                    indent=2,
                    context={
                        "shape": shape,
                        "epsg": crs_epsg,
                        "transform": geotransform,
                        "gsd_w": gsd_w,
                        "gsd_h": gsd_h,
                    },
                )
            )


def generate_level_1_metafile():
    """Example function for reading a product and generating a metadata file from the
    sidecar metadata objects.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("image_path")
    args = parser.parse_args()

    image_path = Path(args.image_path)

    product = Level1ABProduct(image_path)
    product.generate_metadata_file()
