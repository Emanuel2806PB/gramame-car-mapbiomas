from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS
from rasterio.features import geometry_mask, geometry_window
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
from shapely.geometry import mapping


@dataclass(frozen=True)
class RasterSummary:
    geometry_area_ha: float
    rasterized_area_ha: float
    valid_area_ha: float
    nodata_area_ha: float
    natural_area_ha: float
    non_natural_area_ha: float

    @property
    def convergence_percent(self) -> float:
        return 100.0 * self.natural_area_ha / self.valid_area_ha if self.valid_area_ha else float("nan")


def _target_vrt(source: rasterio.io.DatasetReader, target_crs: str, resolution: float) -> WarpedVRT:
    return WarpedVRT(
        source,
        crs=CRS.from_user_input(target_crs),
        resolution=resolution,
        resampling=Resampling.nearest,
        nodata=source.nodata,
    )


def summarize_classes_in_geometry(
    raster_path: str | Path,
    geometry_frame: gpd.GeoDataFrame,
    *,
    target_crs: str,
    resolution_m: float,
    natural_codes: Iterable[int],
    all_touched: bool = False,
) -> tuple[RasterSummary, pd.DataFrame]:
    raster_path = Path(raster_path)
    if not raster_path.exists():
        raise FileNotFoundError(f"Raster MapBiomas ausente: {raster_path}")
    if geometry_frame.empty or geometry_frame.geometry.iloc[0].is_empty:
        raise ValueError("A geometria usada no cruzamento raster está vazia.")

    metric = geometry_frame.to_crs(target_crs)
    geometry = metric.geometry.union_all(method="unary")
    shapes = [mapping(geometry)]
    codes = np.asarray(tuple(natural_codes), dtype=np.int64)

    with rasterio.open(raster_path) as source:
        with _target_vrt(source, target_crs, resolution_m) as raster:
            window = geometry_window(raster, shapes)
            data = raster.read(1, window=window, masked=True)
            transform = raster.window_transform(window)
            inside = geometry_mask(
                shapes,
                out_shape=data.shape,
                transform=transform,
                invert=True,
                all_touched=all_touched,
            )

            data_mask = np.ma.getmaskarray(data)
            valid = inside & ~data_mask
            nodata = inside & data_mask
            values = np.asarray(data.data)
            pixel_area_m2 = abs(transform.a * transform.e - transform.b * transform.d)

            class_values, class_counts = np.unique(values[valid], return_counts=True)
            class_table = pd.DataFrame(
                {
                    "class_code": class_values.astype(int),
                    "pixel_count": class_counts.astype(int),
                    "area_ha": class_counts * pixel_area_m2 / 10_000,
                    "is_natural": np.isin(class_values, codes),
                }
            ).sort_values("class_code", ignore_index=True)

            natural_pixels = int(np.count_nonzero(valid & np.isin(values, codes)))
            valid_pixels = int(np.count_nonzero(valid))
            inside_pixels = int(np.count_nonzero(inside))
            nodata_pixels = int(np.count_nonzero(nodata))
            summary = RasterSummary(
                geometry_area_ha=float(geometry.area / 10_000),
                rasterized_area_ha=inside_pixels * pixel_area_m2 / 10_000,
                valid_area_ha=valid_pixels * pixel_area_m2 / 10_000,
                nodata_area_ha=nodata_pixels * pixel_area_m2 / 10_000,
                natural_area_ha=natural_pixels * pixel_area_m2 / 10_000,
                non_natural_area_ha=(valid_pixels - natural_pixels) * pixel_area_m2 / 10_000,
            )
            return summary, class_table

