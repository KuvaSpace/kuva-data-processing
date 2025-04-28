from pathlib import Path
from typing import cast

import rioxarray as rx
import xarray
from kuva_metadata import MetadataLevel1AB, MetadataLevel1C
from pint import UnitRegistry
from xarray import Dataset

from .product_base import ProductBase


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
    image: xarray.DataArray
        The arrays with the actual data. This have the rioxarray extension activated on
        them so lots of GIS functionality are available on them. For example, the GCPs
        if any could be retrieved like so: `ds.rio.get_gcps()`
    data_tags: dict
        Tags saved along with the product. The tag "data_unit" shows what the unit of
        the product actually is.
    """

    def __init__(
        self,
        image_path: Path,
        metadata: MetadataLevel1AB | None = None,
        target_ureg: UnitRegistry | None = None,
    ) -> None:
        super().__init__(image_path, metadata, target_ureg)

        self.image = cast(
            Dataset,
            rx.open_rasterio(self.image_path / "L1B.tif"),
        )
        self.data_tags = self.image.attrs

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
    ) -> xarray.Dataset:
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
        """Explicitely releases the memory of the `image` variable.

        NOTE: this function is implemented because of a memory leak inside the Rioxarray
        library that doesn't release memory properly. Only use it when the image data is
        not needed anymore.
        """
        del self.image
        self.image = None


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
    image: xarray.DataArray
        The arrays with the actual data. This have the rioxarray extension activated on
        them so lots of GIS functionality are available on them. For example, the GCPs
        if any could be retrieved like so: `ds.rio.get_gcps()`
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

        self.image = cast(
            Dataset,
            rx.open_rasterio(self.image_path / "L1C.tif"),
        )
        self.data_tags = self.image.attrs
        self.wavelengths = [
            b.wavelength.to("nm").magnitude for b in self.metadata.image.bands
        ]

    def __repr__(self):
        """Pretty printing of the object with the most important info"""
        if self.image is not None:
            return (
                f"{self.__class__.__name__} with shape {self.image.shape} "
                f"and wavelengths {self.wavelengths} (CRS: '{self.image.rio.crs}'). "
                f"Loaded from: '{self.image_path}'."
            )
        else:
            return f"{self.__class__.__name__} loaded from '{self.image_path}'"

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
        """Explicitely releases the memory of the `image` variable.

        NOTE: this function is implemented because of a memory leak inside the Rioxarray
        library that doesn't release memory properly. Only use it when the image data is
        not needed anymore.
        """
        del self.image
        self.image = None


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
