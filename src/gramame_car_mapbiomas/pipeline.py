from __future__ import annotations

import json
import logging
import platform
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
import shapely

from . import __version__
from .cartography import export_comparison_raster, generate_maps
from .config import PipelineConfig, load_config
from .raster import RasterSummary, summarize_classes_in_geometry
from .vector import (
    clean_vector,
    clip_to_study_area,
    dissolve_study_area,
    geometry_union,
    read_vector,
    vector_indicators,
)


LOGGER = logging.getLogger("gramame_car_mapbiomas")


def _write_layer(frame: gpd.GeoDataFrame, path: Path, layer: str) -> None:
    frame.to_file(path, layer=layer, driver="GPKG")


def _exclude_registration_statuses(
    frame: gpd.GeoDataFrame, field: str | None, excluded: tuple[str, ...], name: str
) -> gpd.GeoDataFrame:
    if not field or not excluded:
        return frame
    if field not in frame.columns:
        raise KeyError(f"Campo de situação cadastral ausente em {name}: {field}")
    status = frame[field].fillna("").astype(str).str.upper()
    result = frame.loc[~status.isin(excluded)].copy()
    LOGGER.info("%s: %d feições excluídas por situação cadastral %s", name, len(frame) - len(result), excluded)
    return result


def run_pipeline(config_or_path: PipelineConfig | str | Path) -> Path:
    config = load_config(config_or_path) if not isinstance(config_or_path, PipelineConfig) else config_or_path
    output_dir = config.project.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    log_path = output_dir / "execucao.log"
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOGGER.handlers.clear()
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)

    LOGGER.info("Iniciando projeto %s", config.project.name)
    LOGGER.info("Configuração: %s", config.source_path)

    raw_study = read_vector(config.study_area, "area_estudo")
    raw_properties = read_vector(config.properties, "imoveis")
    raw_declared = read_vector(config.declared_native, "vegetacao_declarada")
    raw_properties = _exclude_registration_statuses(
        raw_properties,
        config.properties.status_field,
        config.analysis.excluded_status_codes,
        "imoveis",
    )
    raw_declared = _exclude_registration_statuses(
        raw_declared,
        config.declared_native.status_field,
        config.analysis.excluded_status_codes,
        "vegetacao_declarada",
    )

    study, qc_study = clean_vector(
        raw_study,
        name="area_estudo",
        target_crs=config.project.target_crs,
        minimum_area_m2=config.analysis.minimum_geometry_area_m2,
    )
    study = dissolve_study_area(study)
    properties, qc_properties = clean_vector(
        raw_properties,
        name="imoveis",
        target_crs=config.project.target_crs,
        minimum_area_m2=config.analysis.minimum_geometry_area_m2,
        id_field=config.properties.id_field,
    )
    declared, qc_declared = clean_vector(
        raw_declared,
        name="vegetacao_declarada",
        target_crs=config.project.target_crs,
        minimum_area_m2=config.analysis.minimum_geometry_area_m2,
        id_field=config.declared_native.id_field,
    )

    properties_clip = clip_to_study_area(properties, study)
    declared_clip = clip_to_study_area(declared, study)
    if properties_clip.empty:
        raise ValueError("Nenhum imóvel intersecta a área de estudo.")
    if declared_clip.empty:
        raise ValueError("Nenhuma vegetação declarada intersecta a área de estudo.")

    declared_union = geometry_union(declared_clip, "vegetacao_declarada_uniao")
    properties_union = geometry_union(properties_clip, "imoveis_uniao")
    outside_declared_geom = properties_union.geometry.iloc[0].difference(declared_union.geometry.iloc[0])
    properties_without_declared = gpd.GeoDataFrame(
        {"camada": ["imoveis_sem_vegetacao_declarada"]},
        geometry=[outside_declared_geom],
        crs=properties_clip.crs,
    )

    indicators = vector_indicators(properties_clip, declared_clip, declared_union)
    declared_raster, class_table = summarize_classes_in_geometry(
        config.mapbiomas.path,
        declared_union,
        target_crs=config.project.target_crs,
        resolution_m=config.analysis.raster_resolution_m,
        natural_codes=config.analysis.natural_class_codes,
        all_touched=config.analysis.all_touched,
    )
    if outside_declared_geom.is_empty:
        outside_raster = RasterSummary(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    else:
        outside_raster, _ = summarize_classes_in_geometry(
            config.mapbiomas.path,
            properties_without_declared,
            target_crs=config.project.target_crs,
            resolution_m=config.analysis.raster_resolution_m,
            natural_codes=config.analysis.natural_class_codes,
            all_touched=config.analysis.all_touched,
        )

    indicators.update(
        {
            "mapbiomas_area_valida_na_vegetacao_declarada_ha": declared_raster.valid_area_ha,
            "mapbiomas_area_natural_coincidente_ha": declared_raster.natural_area_ha,
            "mapbiomas_area_nao_natural_na_declarada_ha": declared_raster.non_natural_area_ha,
            "indice_convergencia_car_mapbiomas_percentual": declared_raster.convergence_percent,
            "mapbiomas_area_natural_nos_imoveis_fora_declaracao_ha": outside_raster.natural_area_ha,
            "mapbiomas_nodata_na_vegetacao_declarada_ha": declared_raster.nodata_area_ha,
        }
    )

    gpkg_path = output_dir / "gramame_car_mapbiomas.gpkg"
    if gpkg_path.exists():
        gpkg_path.unlink()
    _write_layer(study, gpkg_path, "area_estudo")
    _write_layer(properties_clip, gpkg_path, "imoveis_recorte")
    _write_layer(declared_clip, gpkg_path, "vegetacao_declarada_recorte")
    _write_layer(declared_union, gpkg_path, "vegetacao_declarada_uniao")

    pd.DataFrame([indicators]).to_csv(output_dir / "indicadores_gerais.csv", index=False, encoding="utf-8-sig")
    class_table.to_csv(output_dir / "classes_mapbiomas_na_vegetacao_declarada.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [qc_study.as_record(), qc_properties.as_record(), qc_declared.as_record()]
    ).to_csv(output_dir / "controle_qualidade.csv", index=False, encoding="utf-8-sig")

    comparison_raster = export_comparison_raster(
        output_path=output_dir / "convergencia_car_mapbiomas_2025.tif",
        raster_path=config.mapbiomas.path,
        study_area=study,
        properties=properties_clip,
        declared_native=declared_clip,
        target_crs=config.project.target_crs,
        resolution_m=config.analysis.raster_resolution_m,
        natural_codes=config.analysis.natural_class_codes,
        all_touched=config.analysis.all_touched,
    )

    map_paths = generate_maps(
        output_dir=output_dir,
        study_area=study,
        properties=properties_clip,
        declared_native=declared_clip,
        mapbiomas_path=config.mapbiomas.path,
        target_crs=config.project.target_crs,
        resolution_m=config.analysis.raster_resolution_m,
        natural_codes=config.analysis.natural_class_codes,
        all_touched=config.analysis.all_touched,
    )

    metadata = {
        "pipeline_version": __version__,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": str(config.source_path),
        "target_crs": config.project.target_crs,
        "mapbiomas_year": config.mapbiomas.year,
        "natural_class_codes": list(config.analysis.natural_class_codes),
        "excluded_status_codes": list(config.analysis.excluded_status_codes),
        "raster_resolution_m": config.analysis.raster_resolution_m,
        "all_touched": config.analysis.all_touched,
        "python": platform.python_version(),
        "geopandas": gpd.__version__,
        "rasterio": rasterio.__version__,
        "shapely": shapely.__version__,
        "inputs": {
            "study_area": str(config.study_area.path),
            "properties": str(config.properties.path),
            "declared_native": str(config.declared_native.path),
            "mapbiomas": str(config.mapbiomas.path),
        },
        "maps": [str(path) for path in map_paths],
        "comparison_raster": str(comparison_raster),
        "raster_summary_declared": asdict(declared_raster),
        "raster_summary_properties_outside_declared": asdict(outside_raster),
    }
    with (output_dir / "metadados_execucao.json").open("w", encoding="utf-8") as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2)

    LOGGER.info("Execução concluída. GeoPackage: %s", gpkg_path)
    return output_dir
