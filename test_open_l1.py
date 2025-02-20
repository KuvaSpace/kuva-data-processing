""" Minimal example script: reading an L1 product.

This assumes that the `kuva_reader` project has been installed in your environment.
"""

from pathlib import Path

from kuva_reader import Level1ABProduct

DATA_ROOT = Path("data")
product_path = DATA_ROOT / "hyperfield1a_L1B_20250105T092548/"

product = Level1ABProduct(product_path)
print(product.image.shape)
