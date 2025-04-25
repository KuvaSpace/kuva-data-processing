from pathlib import Path

from kuva_reader import Level0Product, Level1ABProduct, Level1CProduct, Level2AProduct


def read_product(
    product_path: Path,
) -> Level0Product | Level1ABProduct | Level1CProduct | Level2AProduct:
    """Helper function for reading any product level based on folder name or TIF name.

    Parameters
    ----------
    product_path
        Path to the product to load

    Returns
    -------
        The product of the correct processing level

    Raises
    ------
    ValueError
        Folder not existing or files are renamed so that processing level isn't visible
    """

    product_map = {
        "L0": Level0Product,
        "L1AB": Level1ABProduct,
        "L1C": Level1CProduct,
        "L2A": Level2AProduct,
    }

    product_path = Path(product_path)  # Might be a string, typing not enforced
    if not product_path.is_dir():
        e_ = f"Given product path is not a folder: '{product_path}'"
        raise ValueError(e_)

    # First check if top level filepath matches
    for product_level, product_class in product_map.items():
        if product_level in product_path.name:
            return product_class(product_path)

    # In case folder is renamed, check if tif file product level matches.
    # Folder should contain one 'LXX.tif' file.
    for tif_path in product_path.glob("L*.tif"):
        if tif_path.stem in product_map:
            return product_map[tif_path.stem](product_path)

    # Folder and filenames don't match expected format
    e_ = (
        f"Product folder '{product_path}' does not contain the processing level "
        "information. Check that you have a correct folder or consider using the "
        "correct reader (L0, L1AB, L1C, L2A)."
    )
    raise ValueError(e_)
