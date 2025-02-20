from pathlib import Path
from typing import cast

import rioxarray as rx
from kuva_metadata import MetadataLevel2A
from pint import UnitRegistry
from xarray import Dataset

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
        metadata: MetadataLevel2A | None = None,
        target_ureg: UnitRegistry | None = None,
    ) -> None:
        super().__init__(image_path, metadata, target_ureg)

        self.image = cast(
            Dataset,
            rx.open_rasterio(self.image_path / "L2A.tif"),
        )
        self.data_tags = self.image.attrs

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
