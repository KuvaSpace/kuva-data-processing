"""Tests for reading of actual Hyperfield products.

NOTE: To limit data size, the test data used in the kuva-reader tests have been cropped,
and most of the bands have been removed. The original images are from a normal
acquisition."""

from pathlib import Path

import numpy as np
import pytest

from kuva_reader import Level1ABProduct, Level1CProduct, Level2AProduct, read_product

TEST_DATA_ROOT = Path(__file__).parent / "test_data"

L1B_RADIANCE_PATH = (
    TEST_DATA_ROOT / "hyperfield1b_L1B_20250909T061641_20251029T152430_radiance"
)
L1B_REFLECTANCE_PATH = (
    TEST_DATA_ROOT / "hyperfield1b_L1B_20250909T061641_20251028T095647_reflectance"
)

L1C_RADIANCE_PATH = TEST_DATA_ROOT / "hyperfield1a_L1C_20250310T142413_radiance"
L1C_REFLECTANCE_PATH = TEST_DATA_ROOT / "hyperfield1a_L1C_20250310T142413_reflectance"
L2A_PATH = TEST_DATA_ROOT / "hyperfield1a_L2A_20250310T142413"


@pytest.fixture
def l1b_product() -> Level1ABProduct:
    """Fetch test L1B product.

    NOTE: This is a cropped version of a Hyperfield-1A L1B cube with few bands (3)
    """
    return Level1ABProduct(L1B_REFLECTANCE_PATH)


@pytest.fixture
def l1c_product() -> Level1CProduct:
    """Fetch test L1C product.

    NOTE: This is a cropped version of a Hyperfield-1A L1C cube with few bands (5)
    """
    return Level1CProduct(L1C_RADIANCE_PATH)


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


def test_read_l1b(l1b_product: Level1ABProduct):
    """Product reading was successful based on image, metadata and tags"""
    # Check that image was loaded with correct number of bands
    assert l1b_product.image.read().shape[0] == 3
    # Check that metadata exists and has same shape as image
    assert len(l1b_product.metadata.image.bands) == 3
    # Check that tags exist
    assert l1b_product.data_tags.get("AREA_OR_POINT") is not None


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


def test_read_l1b_reflectance_with_conversions():
    """Test L1B (in reflectance) conversions"""
    # Both conversions should work
    l1b_product_a = Level1ABProduct(L1B_REFLECTANCE_PATH, convert_to_radiance=False)
    l1b_product_a = l1b_product_a.image.read()
    assert l1b_product_a.shape[0] == 3

    l1b_product_b = Level1ABProduct(L1B_REFLECTANCE_PATH, convert_to_radiance=True)
    l1b_product_b = l1b_product_b.image.read()
    assert l1b_product_b.shape[0] == 3


def test_read_l1b_radiance_with_conversions():
    """Test L1B (in radiance) conversions"""
    # Without conversion should work just fine
    l1b_product_a = Level1ABProduct(L1B_RADIANCE_PATH, convert_to_radiance=False)
    l1b_product_a = l1b_product_a.image.read()
    assert l1b_product_a.shape[0] == 3

    # If already in radiance, should raise an error
    with pytest.raises(ValueError):
        Level1ABProduct(L1B_RADIANCE_PATH, convert_to_radiance=True)


def test_read_l1c_reflectance_with_conversions():
    """Test L1C (in reflectance) conversions"""
    # Both conversions should work
    l1c_product = Level1CProduct(L1C_REFLECTANCE_PATH, convert_to_radiance=False)
    assert l1c_product.image.read().shape[0] == 5

    l1c_product = Level1CProduct(L1C_REFLECTANCE_PATH, convert_to_radiance=True)
    assert l1c_product.image.read().shape[0] == 5


def test_read_l1c_radiance_with_conversions():
    """Test L1C (in radiance) conversions"""
    # Without conversion should work just fine
    l1c_product = Level1CProduct(L1C_RADIANCE_PATH, convert_to_radiance=False)
    assert l1c_product.image.read().shape[0] == 5

    # If already in radiance, should raise an error
    with pytest.raises(ValueError):
        Level1CProduct(L1C_RADIANCE_PATH, convert_to_radiance=True)
