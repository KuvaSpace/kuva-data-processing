---
title: Validations
---

The data that is allowed into a Kuva metadata object is thoroughly validated
and parsed into the most appropriate data types. Below is a summary of the
validations that are being applied.

## Custom JSON (de)serializers

Kuva metadata must allow for loss-less round trip conversions between in-memory
and JSON representation. However, JSON doesn't have support for many of the
types that we would like to store in it. This are supported via custom pydantic
(de)serialization routines.

### Quantity

Many of the fields stored within a Kuva metadata object have physical units
associated with them. For this reason whenever possible the field will be
stored as a `pint.Quantity` object. JSON serialization is enabled by storing
each value with physical units as a 2-tuple where the first element represents
the numerical value of the quantity and the second is a string representing the
relevant physical unit. Pint must be able to understand the provided string.

### CRSGeometry

GIS polygons should always be stored together with their associated CRS. When serializing
to JSON we represent them as a dictionary:

```json
{
    "geom": "<WKT string representation of the polygon>",
    "crs_epsg": "<epsg code of the relevant CRS>"
}
```

On the Python side they look like:

::: kuva-metadata.kuva_metadata.custom_types.CRSGeometry
    handler: python
    options:
      heading_level: 4

### quaternion

### Array

## L0 Metadata

### Header

- `creation_date`: When reading from a json sidecar the data must be supplied as
a string that can be understood by `dateutil.date_parser` and will always
_casted_ to UTC. When creating directly as a Python object data is expected to
be a `datetime.datetime` object with UTC timezone.

### Satellite

- `launch_date`: Same as `creation_date` for [Header](#Header)

### Weather

- `timestamp`: Same as `creation_date` for [Header](#Header)
- `temperature`: A [Quantity](#quantity-objects) with units of temperature, e.g. `K`.
- `pressure`: A [Quantity](#quantity-objects) with units of pressure, e.g. `mPa`.
- `humidity`: A fraction between 0 and 1.
- `wind_speed`: A [Quantity](#quantity-objects) with units of speed.
- `wind_dir`: A [Quantity](#quantity-objects) with units of angle.

### Alignment Parameters

- `frame_alignment_mode`: List of at least length 1.
- `band_alignment_mode`: List of at least length 1.
- `cube_alignment_mode`: List of at least length 1.
- `product_stitching_mode`: List of at least length 1.
- `frame_alignment_reference_position_percent`: Integer between 0 and 100.
- `band_alignment_reference_position_percent`: Integer between 0 and 100.
- `cube_alignment_reference_position_percent`: Integer between 0 and 100.
- `product_alignment_reference_position_percent`: Integer between 0 and 100.
- `band_alignment_reference_bands`: All values in the dict must be int >= 0.
- `cube_alignment_reference_bands`: All values in the dict must be int >= 0.
- `product_stitching_reference_band`: Integer >= 0.
- `product_stitching_cube_order`: List of at least length 1.

### Camera

- `passband_range`: The wavelength range units must be compatible with a
distance and they need to be well ordered.
- `n_rows`/`n_cols`: A strictly greater than 0 integer -Must be positive and
with units compatible with distance. `pixel_height`/`pixel_width`: A positive
[Quantity](#quantity-objects) with units of distance.
- `focal_distance`: A positive [Quantity](#quantity-objects) with units of
distance.


### Frame

- `index`
- `integration_time`
- `start/end_acquisition_date`

### Band

- `index`
- `wavelength`
- `start/end_acquisition_date`
- `reference_frame_index`

### Image

- `start/end_acquisition_date`
- `local_solar_{zenith, azimuth}_angle`

