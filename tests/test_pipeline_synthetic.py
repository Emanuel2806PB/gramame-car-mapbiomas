from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import yaml
from rasterio.transform import from_origin
from shapely.geometry import Polygon, box

from gramame_car_mapbiomas.pipeline import run_pipeline


CRS = "EPSG:31985"


def _write_vector(path: Path, layer: str, rows: dict, geometries: list[Polygon]) -> None:
    frame = gpd.GeoDataFrame(rows, geometry=geometries, crs=CRS)
    frame.to_file(path, layer=layer, driver="GPKG")


def test_pipeline_computes_union_and_raster_convergence(tmp_path: Path) -> None:
    data_dir = tmp_path / "dados"
    data_dir.mkdir()
    study_path = data_dir / "area.gpkg"
    properties_path = data_dir / "car.gpkg"
    raster_path = data_dir / "mapbiomas.tif"

    study = box(0, 0, 120, 120)
    _write_vector(study_path, "bacia", {"nome": ["teste"]}, [study])
    _write_vector(
        properties_path,
        "imoveis",
        {"cod_imovel": ["A", "B"]},
        [box(0, 0, 60, 120), box(60, 0, 120, 120)],
    )
    # Dois polígonos parcialmente sobrepostos: soma 9.000 m², união 7.200 m².
    _write_vector(
        properties_path,
        "vegetacao",
        {"cod_imovel": ["A", "B"]},
        [box(0, 0, 60, 90), box(30, 30, 90, 90)],
    )

    values = np.array(
        [
            [3, 3, 15, 15],
            [3, 3, 15, 15],
            [3, 3, 15, 15],
            [3, 3, 15, 15],
        ],
        dtype=np.uint8,
    )
    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        width=4,
        height=4,
        count=1,
        dtype=values.dtype,
        crs=CRS,
        transform=from_origin(0, 120, 30, 30),
        nodata=0,
    ) as dataset:
        dataset.write(values, 1)

    config_path = tmp_path / "config.yaml"
    output_dir = tmp_path / "saida"
    config = {
        "project": {"name": "teste", "output_dir": str(output_dir), "target_crs": CRS},
        "inputs": {
            "study_area": {"path": str(study_path), "layer": "bacia"},
            "properties": {"path": str(properties_path), "layer": "imoveis", "id_field": "cod_imovel"},
            "declared_native": {"path": str(properties_path), "layer": "vegetacao", "id_field": "cod_imovel"},
            "mapbiomas": {"path": str(raster_path), "year": 2025},
        },
        "analysis": {
            "natural_class_codes": [3],
            "raster_resolution_m": 30,
            "all_touched": False,
            "minimum_geometry_area_m2": 1,
        },
    }
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")

    result = run_pipeline(config_path)
    indicators = pd.read_csv(result / "indicadores_gerais.csv")
    row = indicators.iloc[0]
    assert row["area_declarada_soma_ha"] == 0.9
    assert row["area_declarada_uniao_ha"] == 0.72
    assert row["sobreposicao_declarada_ha"] == 0.18
    assert row["area_declarada_fora_imoveis_ha"] == 0
    assert row["indice_convergencia_car_mapbiomas_percentual"] == 75
    assert (result / "gramame_car_mapbiomas.gpkg").exists()
    assert (result / "controle_qualidade.csv").exists()
    assert (result / "figuras" / "mapa_01_area_estudo.png").exists()
    assert (result / "figuras" / "mapa_02_vegetacao_declarada.png").exists()
    assert (result / "figuras" / "mapa_03_convergencia_car_mapbiomas.png").exists()
