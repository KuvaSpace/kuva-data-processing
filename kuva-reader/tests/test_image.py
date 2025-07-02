"""Tests for the image processing tools."""

import numpy as np

from kuva_reader import image_to_original_range, image_to_uint16_range


def test_normalisation():
    """Check that normalisation function works back and forth."""

    img_size = 100
    img = np.random.uniform(0, 10000, size=[img_size, img_size])  # A 2x3 array

    # Usual uint16 conversion
    normalised, offset, scale = image_to_uint16_range(img)
    assert (np.min(normalised) == 0) and (np.max(normalised) == 65535)

    # Check that conversion back to original dtype works as intended
    back_to_img = image_to_original_range(normalised, offset, scale) + 1
    assert np.allclose(img, back_to_img, atol=1)
