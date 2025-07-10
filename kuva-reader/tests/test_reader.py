"""Tests for reading of actual Hyperfield products.

NOTE: To limit data size, the test data used in the kuva-reader tests have been cropped,
and most of the bands have been removed. The original images are from a normal
acquisition."""

from pathlib import Path

import pytest

from kuva_reader import Level1CProduct, Level2AProduct, read_product

TEST_DATA_ROOT = Path(__file__).parent / "test_data"
L1C_PATH = TEST_DATA_ROOT / "hyperfield1a_L1C_20250310T142413"
L2A_PATH = TEST_DATA_ROOT / "hyperfield1a_L2A_20250310T142413"


@pytest.fixture
def l1c_product() -> Level1CProduct:
    """Fetch test L1C product.

    NOTE: This is a cropped version of a Hyperfield-1A L1C cube with few bands (5)
    """
    return Level1CProduct(L1C_PATH)


@pytest.fixture
def l2a_product() -> Level2AProduct:
    """Fetch test L2A product.

    NOTE: This is a cropped version of a Hyperfield-1A L2A cube with few bands (5)
    """
    return Level2AProduct(L2A_PATH)


def test_product_reader():
    """Read the correct products with product reader function"""
    with pytest.raises(ValueError):
        read_product(L2A_PATH.parent)

    product = read_product(L2A_PATH)
    assert product.__class__ == Level2AProduct


def test_read_l1c(l1c_product: Level1CProduct):
    """Product reading was successful based on image, metadata and tags"""
    # Check that image was loaded with correct number of bands
    assert l1c_product.image.read().shape[0] == 5
    # Check that metadata exists and has same shape as image
    assert len(l1c_product.metadata.image.bands) == 5
    # Check that tags exist
    assert l1c_product.data_tags.get("AREA_OR_POINT") is not None


def test_read_l2a(l2a_product: Level2AProduct):
    """Product reading was successful based on image, metadata and tags"""
    # Check that image was loaded with correct number of bands
    assert l2a_product.image.read().shape[0] == 5
    # Check that metadata exists and has same shape as image
    assert len(l2a_product.metadata.image.bands) == 5
    # Check that tags exist
    assert l2a_product.data_tags.get("AREA_OR_POINT") is not None


def test_read_bad_pixel_mask_l1c(l1c_product: Level1CProduct):
    """Bad pixel mask is correctly loaded and is same shape as product"""
    bad_pixel_mask = l1c_product.get_bad_pixel_mask().read()
    assert bad_pixel_mask.shape[1:] == l1c_product.image.shape


def test_read_bad_pixel_mask_l2a(l2a_product: Level2AProduct):
    """Bad pixel mask is correctly loaded and is same shape as product"""
    bad_pixel_mask = l2a_product.get_bad_pixel_mask().read()
    assert bad_pixel_mask.shape[1:] == l2a_product.image.shape
