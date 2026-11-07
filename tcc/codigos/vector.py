from __future__ import annotations

from dataclasses import asdict, dataclass
import geopandas as gpd
import pandas as pd
from shapely import normalize

from .config import VectorInput


@dataclass
class VectorQuality:
    dataset: str
    input_features: int
    missing_geometry: int
    empty_geometry: int
    invalid_geometry: int
    repaired_geometry: int
    duplicate_geometry: int
    removed_tiny_geometry: int
    output_features: int

    def as_record(self) -> dict[str, int | str]:
        return asdict(self)


def read_vector(spec: VectorInput, name: str) -> gpd.GeoDataFrame:
    if not spec.path.exists():
        raise FileNotFoundError(f"Entrada vetorial ausente ({name}): {spec.path}")
    kwargs = {"layer": spec.layer} if spec.layer else {}
    frame = gpd.read_file(spec.path, **kwargs)
    if frame.crs is None:
        raise ValueError(f"A camada {name} não possui sistema de referência espacial.")
    if frame.empty:
        raise ValueError(f"A camada {name} está vazia.")
    return frame


def _geometry_fingerprint(series: gpd.GeoSeries) -> pd.Series:
    return series.map(lambda geom: normalize(geom).wkb_hex if geom is not None and not geom.is_empty else None)


def clean_vector(
    frame: gpd.GeoDataFrame,
    *,
    name: str,
    target_crs: str,
    minimum_area_m2: float,
    id_field: str | None = None,
) -> tuple[gpd.GeoDataFrame, VectorQuality]:
    if id_field and id_field not in frame.columns:
        raise KeyError(f"Campo identificador ausente em {name}: {id_field}")

    result = frame.copy()
    input_features = len(result)
    missing = int(result.geometry.isna().sum())
    empty = int(result.geometry.is_empty.fillna(False).sum())
    valid_mask = result.geometry.notna() & ~result.geometry.is_empty.fillna(True)
    result = result.loc[valid_mask].copy()

    invalid_before = ~result.geometry.is_valid
    invalid = int(invalid_before.sum())
    if invalid:
        result.loc[invalid_before, result.geometry.name] = result.loc[invalid_before].geometry.make_valid()
    repaired = int((invalid_before & result.geometry.is_valid).sum())

    result = result.to_crs(target_crs)
    polygon_mask = result.geom_type.isin(["Polygon", "MultiPolygon"])
    result = result.loc[polygon_mask].copy()

    tiny_mask = result.geometry.area < minimum_area_m2
    tiny = int(tiny_mask.sum())
    result = result.loc[~tiny_mask].copy()

    fingerprints = _geometry_fingerprint(result.geometry)
    duplicates = int(fingerprints.duplicated(keep=False).sum())
    result["_geom_duplicate"] = fingerprints.duplicated(keep=False)
    result["_source_index"] = result.index.astype(str)
    result = result.reset_index(drop=True)

    quality = VectorQuality(
        dataset=name,
        input_features=input_features,
        missing_geometry=missing,
        empty_geometry=empty,
        invalid_geometry=invalid,
        repaired_geometry=repaired,
        duplicate_geometry=duplicates,
        removed_tiny_geometry=tiny,
        output_features=len(result),
    )
    return result, quality


def dissolve_study_area(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    geom = frame.geometry.union_all(method="unary")
    return gpd.GeoDataFrame({"area_estudo": ["bacia_gramame"]}, geometry=[geom], crs=frame.crs)


def clip_to_study_area(frame: gpd.GeoDataFrame, study_area: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    mask = study_area.geometry.iloc[0]
    candidates = frame.loc[frame.geometry.intersects(mask)].copy()
    if candidates.empty:
        return candidates
    candidates.geometry = candidates.geometry.intersection(mask)
    candidates = candidates.loc[~candidates.geometry.is_empty].copy()
    return candidates.reset_index(drop=True)


def geometry_union(frame: gpd.GeoDataFrame, name: str) -> gpd.GeoDataFrame:
    geom = frame.geometry.union_all(method="unary")
    return gpd.GeoDataFrame({"camada": [name]}, geometry=[geom], crs=frame.crs)


def vector_indicators(
    properties: gpd.GeoDataFrame,
    declared_native: gpd.GeoDataFrame,
    declared_union: gpd.GeoDataFrame,
) -> dict[str, float | int]:
    property_union = properties.geometry.union_all(method="unary")
    declared_geometry = declared_union.geometry.iloc[0]
    declared_sum_m2 = float(declared_native.geometry.area.sum())
    declared_union_m2 = float(declared_geometry.area)
    declared_inside_properties_m2 = float(declared_geometry.intersection(property_union).area)
    declared_outside_properties_m2 = float(declared_geometry.difference(property_union).area)
    return {
        "n_imoveis_recortados": int(len(properties)),
        "n_poligonos_vegetacao_declarada": int(len(declared_native)),
        "area_imoveis_uniao_ha": float(property_union.area / 10_000),
        "area_declarada_soma_ha": declared_sum_m2 / 10_000,
        "area_declarada_uniao_ha": declared_union_m2 / 10_000,
        "sobreposicao_declarada_ha": max(0.0, declared_sum_m2 - declared_union_m2) / 10_000,
        "area_declarada_dentro_imoveis_ha": declared_inside_properties_m2 / 10_000,
        "area_declarada_fora_imoveis_ha": declared_outside_properties_m2 / 10_000,
        "area_declarada_dentro_imoveis_percentual": (
            100.0 * declared_inside_properties_m2 / declared_union_m2 if declared_union_m2 else 0.0
        ),
        "fragmento_area_media_ha": float(declared_native.geometry.area.mean() / 10_000),
        "fragmento_area_mediana_ha": float(declared_native.geometry.area.median() / 10_000),
        "densidade_fragmentos_por_100_km2": float(len(declared_native) / (declared_union_m2 / 100_000_000)) if declared_union_m2 else 0.0,
    }
