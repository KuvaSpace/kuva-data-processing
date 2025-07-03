from pathlib import Path
from typing import cast

import numpy as np
import rasterio as rio
from kuva_metadata import MetadataLevel0
from pint import UnitRegistry
from shapely import Polygon

from kuva_reader import image_footprint

from .product_base import ProductBase


class Level0Product(ProductBase[MetadataLevel0]):
    """
    Level 0 products contain the raw data acquired from the sensor. They
    consist of one roughly georeferenced geotiff per camera and the associated
    metadata. Changes to them are only performed at the metadata level to avoid
    deteriorating them.

    At this processing level frames are not aligned, a natural consequence of
    satellite motion, and are therefore not very useful for any activity that
    require working with more than one band simultaneously. In that case you
    should look into using L1 products.

    The data in the image files is lazy loaded to make things snappier for end
    users but may lead to surprising behaviour if you are not aware of it


    Parameters
    ----------
    image_path
        Path to the folder containing the L0 product images
    metadata, optional
        Metadata if already read e.g. from a database. By default None, meaning
        automatic fetching from metadata sidecar file
    target_ureg, optional
        Pint Unit Registry to swap to. This is only relevant when parsing data from a
        JSON file, which by default uses the kuva-metadata ureg.

    Attributes
    ----------
    image_path: Path
        Path to the folder containing the images.
    metadata: MetadataLevel0
        The metadata associated with the images
    images: Dict[str, rasterio.DatasetReader]
        A dictionary that maps camera names to their respective Rasterio DatasetReader
        objects.
    data_tags: Dict[str, Any]
        Tags stored along with the data. These can be used e.g. to check the physical
        units of pixels or normalisation factors.
    """

    def __init__(
        self,
        image_path: Path,
        metadata: MetadataLevel0 | None = None,
        target_ureg: UnitRegistry | None = None,
    ) -> None:
        super().__init__(image_path, metadata, target_ureg)

        self.images = {
            camera: cast(
                rio.DatasetReader,
                rio.open(
                    self.image_path / (cube.camera.name + ".tif"),
                ),
            )
            for camera, cube in self.metadata.image.data_cubes.items()  # type: ignore
        }
        self.crs = self.images[list(self.images.keys())[0]].crs

        # Read tags for images and denormalize / renormalize if needed
        self.data_tags = {camera: src.tags() for camera, src in self.images.items()}

    def __repr__(self):
        """Pretty printing of the object with the most important info"""
        if self.images is not None and len(self.images):
            image_shapes = []
            for camera_name, image in self.images.items():
                shape_str = f"({image.count}, {image.height}, {image.width})"
                image_shapes.append(f"{camera_name.upper()} shape {shape_str}")

            shapes_description = " and ".join(image_shapes)

            return (
                f"{self.__class__.__name__} "
                f"with {shapes_description} and "
                f"CRS: '{self.crs}'. Loaded from: '{self.image_path}'."
            )
        else:
            return f"{self.__class__.__name__} loaded from '{self.image_path}'."

    def __getitem__(self, camera: str) -> rio.DatasetReader:
        """Return the datarray for the chosen camera."""
        return self.images[camera]

    def keys(self) -> list[str]:
        """Easy access to the camera keys."""
        return list(self.images.keys())

    def footprint(self, crs="") -> Polygon:
        """The product footprint as a Shapely polygon."""
        return image_footprint(self.images["vis"], crs)

    def _get_data_from_sidecar(
        self, sidecar_path: Path, target_ureg: UnitRegistry | None = None
    ) -> MetadataLevel0:
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
                metadata = MetadataLevel0.model_validate_json(
                    fh.read(),
                    context={
                        "image_path": sidecar_path.parent,
                    },
                )
            else:
                # The Image subclass in MetadataLevel0 has an alignment graph that
                # requires a specific context. Swapping UnitRegistries will also require
                # serialization, requiring the extra graph path context parameter.
                metadata = cast(
                    MetadataLevel0,
                    MetadataLevel0.model_validate_json_with_ureg(
                        fh.read(),
                        target_ureg,
                        context={
                            "image_path": sidecar_path.parent,
                            "graph_json_file_name": f"{sidecar_path.stem}_graph.json",
                        },
                    ),
                )

        return metadata

    def _calculate_band_offsets_and_frames(self, cube: str):
        bands_info = self.metadata.image.data_cubes[cube].bands

        band_n_frames = [band.n_frames for band in bands_info]
        band_offsets = np.cumsum(band_n_frames)

        # The first offset ie 0 is missing and the last is not an offset just the
        # length. Fix it.
        band_offsets = band_offsets[:-1].tolist()
        band_offsets.insert(0, 0)
        return band_offsets, band_n_frames

    def calculate_frame_offset(self, cube: str, band_id: int, frame_idx: int) -> int:
        """Find the offset at which a frame lives within a cube."""
        band_offsets, _ = self._calculate_band_offsets_and_frames(cube)
        frame_offset = band_offsets[band_id] + frame_idx

        return frame_offset

    def read_frame(self, cube: str, band_id: int, frame_idx: int) -> np.ndarray:
        """Extract a specific frame from a cube and band."""
        frame_offset = self.calculate_frame_offset(cube, band_id, frame_idx)

        # Rasterio index starts at 1
        frame_offset += 1

        return self[cube].read(frame_offset)

    def read_band(self, cube: str, band_id: int) -> np.ndarray:
        """Extract a specific band from a cube"""
        band_offsets, band_n_frames = self._calculate_band_offsets_and_frames(cube)

        # Calculate the final frame offset for this band and frame
        band_offset_ll = band_offsets[band_id]
        band_offset_ul = band_offset_ll + band_n_frames[band_id]

        # Rasterio index starts at 1
        band_offset_ll += 1
        band_offset_ul += 1

        return self[cube].read(list(np.arange(band_offset_ll, band_offset_ul)))

    def read_data_units(self) -> np.ndarray:
        """Read unit of product and validate they match between cameras"""
        units = [tags.get("data_unit") for tags in self.data_tags.values()]
        if all(product_unit == units[0] for product_unit in units):
            return units[0]
        else:
            # TODO: We should try conversion though
            e_ = "Cameras have different physical units stored to them."
            raise ValueError(e_)

    def get_bad_pixel_mask(self, camera: str | None = None) -> rio.DatasetReader:
        """Get the bad pixel mask associated to each camera of the L0 product

        Returns
        -------
            The bad pixel masks of the cameras
        """
        if camera is None:
            e_ = "The `camera` argument must be given for L0 product bad pixel masks."
            raise ValueError(e_)
        bad_pixel_filename = f"{camera}_per_frame_bad_pixel_mask.tif"
        return self._read_array(self.image_path / bad_pixel_filename)

    def get_cloud_mask(self, camera: str | None = None) -> rio.DatasetReader:
        """Get the cloud mask associated to the product.

        Returns
        -------
            The cloud mask
        """
        if camera is None:
            e_ = "The `camera` argument must be given for L0 product cloud masks."
            raise ValueError(e_)
        bad_pixel_filename = f"{camera}_per_frame_cloud_mask.tif"
        return self._read_array(self.image_path / bad_pixel_filename)

    def release_memory(self):
        """Explicitely closes the Rasterio DatasetReaders and releases the memory of
        the `images` variable.
        """
        for k in self.images.keys():
            self.images[k].close()

        del self.images
        self.images = None


def generate_level_0_metafile():
    """Example function for reading a product and generating a metadata file from the
    sidecar metadata objects.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("image_path")
    args = parser.parse_args()

    image_path = Path(args.image_path)

    product = Level0Product(image_path)
    product.generate_metadata_file()
