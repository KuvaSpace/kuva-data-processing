from pathlib import Path
from typing import cast

import rasterio as rio
from kuva_metadata import MetadataLevel2A
from pint import UnitRegistry
from shapely import Polygon

from kuva_reader import image_footprint

from .product_base import ProductBase


class Level2AProduct(ProductBase[MetadataLevel2A]):
    """
    Level 2A products contain the atmospherically corrected BOA reflectance values.

    Parameters
    ----------
    image_path
        Path to the folder containing the L2A product
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
    metadata: MetadataLevel2A
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
        metadata: MetadataLevel2A | None = None,
        target_ureg: UnitRegistry | None = None,
    ) -> None:
        super().__init__(image_path, metadata, target_ureg)

        self.image = cast(
            rio.DatasetReader,
            rio.open(self.image_path / "L2A.tif"),
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

    def footprint(self, crs="") -> Polygon:
        """The product footprint as a Shapely polygon."""
        return image_footprint(self.image, crs)

    def _get_data_from_sidecar(
        self, sidecar_path: Path, target_ureg: UnitRegistry | None = None
    ) -> MetadataLevel2A:
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
                metadata = MetadataLevel2A.model_validate_json(fh.read())
            else:
                metadata = cast(
                    MetadataLevel2A,
                    MetadataLevel2A.model_validate_json_with_ureg(
                        fh.read(), target_ureg
                    ),
                )

        return metadata

    def release_memory(self):
        """Explicitely closes the Rasterio DatasetReader and releases the memory of
        the `image` variable.
        """
        self.image.close()
        del self.image
        self.image = None


def generate_level_2_metafile():
    """Example function for reading a product and generating a metadata file from the
    sidecar metadata objects.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("image_path")
    args = parser.parse_args()

    image_path = Path(args.image_path)

    product = Level2AProduct(image_path)
    product.generate_metadata_file()
