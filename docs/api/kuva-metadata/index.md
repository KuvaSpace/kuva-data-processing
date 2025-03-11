---
title: Kuva Metadata
---

# Kuva Metadata

Images taken from a satellite are complicated beasts with lot of metadata associated
to them. This repository contains the metadata definitions for the Hyperfield products. 
This metadata along with the acquired GeoTIFF images form the Kuva Space products in its 
various processing levels.

With the metadata and images, we may process products to the 
next processing levels, or do more precise processing than just with a GeoTIFF. 

## Processing levels

Currently there are metadata definitions for the following processing levels of Kuva products:

- **L0**: Radiometrically corrected frames as TOA radiance
- **L1AB**: Band-aligned product formed from multiple L0 products
- **L1C**: Georeferences and orthorectified L1 product
- **L2A**: Atmospherically corrected product as BOA reflectance

## Architecture

All the metadata are defined as Pydantic models, this has several advantages:

- A very rich set of validations that are applied before data object construction
- The ability to easily (de)serialize (from)to JSON
