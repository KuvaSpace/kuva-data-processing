"""
This library defines the metadata format used by the sidecar files that accompany
the images produced by Hyperfield satellites.

The core library used is pydantic which among other nice things allows us to
(de)serialize (from)to JSON .

If you are interested on reading from the Hyperfield metadata database into such
objects then you want to look at the `hyperfield-db` project.
"""

from .sections_common import MetadataBase
from .sections_l0 import MetadataLevel0
from .sections_l1 import MetadataLevel1AB, MetadataLevel1C
from .sections_l2 import MetadataLevel2A

__all__ = [
    "MetadataBase",
    "MetadataLevel0",
    "MetadataLevel1AB",
    "MetadataLevel1C",
    "MetadataLevel2A",
]
