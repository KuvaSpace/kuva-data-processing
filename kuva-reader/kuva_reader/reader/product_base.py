from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar, cast

import rioxarray as rx
from kuva_metadata.sections_common import MetadataBase
from pint import UnitRegistry
from pydantic import BaseModel
from xarray import Dataset

TMetadata = TypeVar("TMetadata", bound=BaseModel)


class ProductBase(Generic[TMetadata], metaclass=ABCMeta):
    """Base class for all Kuva product levels containing the image and all metadata

    Parameters
    ----------
    image_path
        Local path to the stored image
    metadata, optional
        Metadata if already read e.g. from a database. By default None, meaning
        automatic fetching from metadata sidecar file
    target_ureg, optional
        Pint Unit Registry to swap to. This is only relevant when parsing data from a
        JSON file, which by default uses the kuva-metadata ureg.

    Raises
    ------
    ValueError
        Providing Kuva image as something else than a folder
    Exception
        Any errors coming from the reading of the sidecar object
    """

    def __init__(
        self,
        image_path: Path,
        metadata: MetadataBase | None = None,
        target_ureg: UnitRegistry | None = None,
    ):
        self.image_path = Path(image_path)

        if not self.image_path.exists():
            e_ = f"Image path does not exist: {self.image_path}"
            raise ValueError(e_)

        if not self.image_path.is_dir():
            e_ = "Kuva images are folders."
            raise ValueError(e_)

        if metadata is None:
            sidecar_path = self.image_path / f"{self.image_path.name}.json"
            try:
                self.metadata = self._get_data_from_sidecar(sidecar_path, target_ureg)
            except Exception as e:
                e_ = f"Metadata could not be read from the sidecar: {sidecar_path}."
                raise Exception(e_).with_traceback(e.__traceback__)
        else:
            self.metadata = metadata

    @abstractmethod
    def _get_data_from_sidecar(
        self, sidecar_path: Path, target_ureg: UnitRegistry | None = None
    ) -> TMetadata:
        pass

    @staticmethod
    def _read_array(array_path: Path) -> Dataset:
        if array_path.exists():
            return cast(
                Dataset,
                rx.open_rasterio(array_path),
            )
        else:
            e_ = f"Product does not contain the array to be read at '{array_path}'"
            raise ValueError(e_)

    def get_bad_pixel_mask(self, camera: str | None = None) -> Dataset:
        """Get the bad pixel mask associated to the product.

        Parameters
        ----------
        camera
            The camera to fetch the mask for. Only valid for L0 products, and is ignored
            in any other level.

        Returns
        -------
            The bad pixel mask
        """
        if camera is not None:
            e_ = "Parameter `camera` is not supported in this product level."
            raise ValueError(e_)
        return self._read_array(self.image_path / "bad_pixel_mask_aggregated.tif")

    def get_cloud_mask(self, camera: str | None = None) -> Dataset:
        """Get the cloud mask associated to the product.

        Parameters
        ----------
        camera
            The camera to fetch the mask for. Only valid for L0 products, and is ignored
            in any other level.

        Returns
        -------
            The cloud mask
        """
        if camera is not None:
            e_ = "Parameter `camera` is not supported in this product level."
            raise ValueError(e_)
        return self._read_array(self.image_path / "cloud_mask.tif")

    def generate_metadata_file(self) -> None:
        """Write the sidecar files next to the product."""
        metadata_file_name = self.image_path.name + ".json"
        graph_json_file_name = self.image_path.name + "_graph.json"

        with (self.image_path / metadata_file_name).open("w") as fh:
            fh.write(
                self.metadata.model_dump_json(
                    indent=2,
                    context={
                        "image_path": self.image_path,
                        "graph_json_file_name": graph_json_file_name,
                    },
                )
            )
