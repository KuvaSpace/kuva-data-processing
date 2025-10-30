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


def _create_in_memory_dataset(image, data):
    """Helper function to create an in-memory dataset with modified data."""
    new_dataset = MemoryFile().open(
        driver=image.driver,
        height=image.height,
        width=image.width,
        count=image.count,
        dtype=data.dtype,
        crs=image.crs,
        transform=image.transform,
        num_threads=NUM_THREADS,
    )
    new_dataset.write(data)

    # Validate the new dataset properties
    assert new_dataset.driver == image.driver
    assert new_dataset.count == image.count
    assert new_dataset.width == image.width
    assert new_dataset.height == image.height
    assert new_dataset.crs == image.crs
    assert new_dataset.transform == image.transform

    return new_dataset


def _validate_coefficients(coeffs, image_bands_count):
    """Validate that the coefficients array matches the number of image bands."""
    if coeffs.shape[0] != image_bands_count:
        raise ValueError(
            f"Mismatch between coefficients ({coeffs.shape[0]}) and image "
            f"bands ({image_bands_count})."
        )


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
        convert_to_reflectance: bool = True,
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

        if convert_to_reflectance:
            if self.data_tags.get("data_name") == "TOA_RADIANCE":
                coeffs = np.array(
                    [
                        band.toa_radiance_to_reflectance_factor
                        for band in self.metadata.image.bands
                    ]
                )
                _validate_coefficients(coeffs, self._image.count)

                data = self._image.read() * coeffs[:, np.newaxis, np.newaxis]
                self._image.close()
                self._image = _create_in_memory_dataset(self._image, data)

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
            raise RuntimeError("Images has been released.")
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
    ) -> None:
        super().__init__(image_path, metadata, target_ureg)

        self._image = cast(
            rio.DatasetReader,
            rio.open(self.image_path / "L1C.tif", num_threads=NUM_THREADS),
        )
        self.data_tags = self.image.tags()

        self.wavelengths = [
            b.wavelength.to("nm").magnitude for b in self.metadata.image.bands
        ]
        self.crs = self.image.crs

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
            raise RuntimeError("Images has been released.")
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
