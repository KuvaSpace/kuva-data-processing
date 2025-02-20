import os
from pathlib import Path

import rasterio


def db_conn_str():
    "Prepare a connection string to connect to the DB"
    test_db_params = {
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_DB": "hyperfield",
        "POSTGRES_PORT": "5432",
    }

    def query_param(param):
        return os.environ[param] if param in os.environ else test_db_params[param]

    username = query_param("POSTGRES_USER")
    password = query_param("POSTGRES_PASSWORD")
    host = query_param("POSTGRES_HOST")
    name = query_param("POSTGRES_DB")
    port = query_param("POSTGRES_PORT")

    conn_str = f"postgres://{username}:{password}@{host}:{port}/{name}?sslmode=disable"

    return conn_str


def retrieve_folder_product_id(image_path: Path, product_level: str) -> str:
    tif_files = Path(image_path).glob("*.tif")

    potential_ids = set()
    for tif in tif_files:
        ds = rasterio.open(tif)
        tags = ds.tags()

        if "_KUVA_PRODUCT_LEVEL" in tags and "_KUVA_PRODUCT_ID" in tags:
            if tags["_KUVA_PRODUCT_LEVEL"] == product_level:
                # This are files of interest
                potential_ids.add(tags["_KUVA_PRODUCT_ID"])

    if len(potential_ids) == 0:
        raise ValueError(f"The folder contains no KUVA L{product_level} products.")
    elif len(potential_ids) > 1:
        raise ValueError(
            f"The folder contains more than one KUVA L{product_level} product."
        )
    else:
        return list(potential_ids)[0]
