"""Metadata specification for L2 products"""

from pydantic import ConfigDict

# Unused imports are kept so that common objects are available with one import
from kuva_metadata.sections_common import (  # noqa # pylint: disable=unused-import
    Header,
    MetadataBase,
    Radiometry,
    RPCoefficients,
    Satellite,
)
from kuva_metadata.sections_l1 import (  # noqa # pylint: disable=unused-import
    Band,
    Image,
)


class MetadataLevel2A(MetadataBase):
    """Metadata for Level-2A products

    Attributes
    ----------
    MetadataBase attributes
        All attributes included in parent MetadataBase
    rpcs
        Rational polynomial function coefficients for product orthorectification
    """

    image: Image

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
