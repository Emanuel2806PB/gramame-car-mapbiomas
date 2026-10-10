from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class VectorInput:
    path: Path
    layer: str | None = None
    id_field: str | None = None
    status_field: str | None = None


@dataclass(frozen=True)
class RasterInput:
    path: Path
    year: int | None = None


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    output_dir: Path
    target_crs: str


@dataclass(frozen=True)
class AnalysisConfig:
    natural_class_codes: tuple[int, ...]
    excluded_status_codes: tuple[str, ...] = ()
    raster_resolution_m: float = 30.0
    all_touched: bool = False
    minimum_geometry_area_m2: float = 1.0


@dataclass(frozen=True)
class PipelineConfig:
    source_path: Path
    project: ProjectConfig
    study_area: VectorInput
    properties: VectorInput
    declared_native: VectorInput
    mapbiomas: RasterInput
    analysis: AnalysisConfig


def _resolve(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def _vector_input(raw: dict[str, Any], base: Path) -> VectorInput:
    return VectorInput(
        path=_resolve(base, raw["path"]),
        layer=raw.get("layer"),
        id_field=raw.get("id_field"),
        status_field=raw.get("status_field"),
    )


def load_config(path: str | Path) -> PipelineConfig:
    source = Path(path).resolve()
    with source.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    if not isinstance(raw, dict):
        raise ValueError("O arquivo de configuração deve conter um objeto YAML.")

    base = source.parent.parent if source.parent.name == "config" else source.parent
    project = raw["project"]
    inputs = raw["inputs"]
    analysis = raw.get("analysis", {})
    codes = tuple(int(value) for value in analysis.get("natural_class_codes", ()))
    if not codes:
        raise ValueError("analysis.natural_class_codes não pode ser vazio.")

    return PipelineConfig(
        source_path=source,
        project=ProjectConfig(
            name=str(project["name"]),
            output_dir=_resolve(base, project["output_dir"]),
            target_crs=str(project.get("target_crs", "EPSG:31985")),
        ),
        study_area=_vector_input(inputs["study_area"], base),
        properties=_vector_input(inputs["properties"], base),
        declared_native=_vector_input(inputs["declared_native"], base),
        mapbiomas=RasterInput(
            path=_resolve(base, inputs["mapbiomas"]["path"]),
            year=inputs["mapbiomas"].get("year"),
        ),
        analysis=AnalysisConfig(
            natural_class_codes=codes,
            excluded_status_codes=tuple(
                str(value).upper() for value in analysis.get("excluded_status_codes", ())
            ),
            raster_resolution_m=float(analysis.get("raster_resolution_m", 30.0)),
            all_touched=bool(analysis.get("all_touched", False)),
            minimum_geometry_area_m2=float(analysis.get("minimum_geometry_area_m2", 1.0)),
        ),
    )
