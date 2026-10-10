from __future__ import annotations

from dataclasses import dataclass
from math import floor, log10
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle
from matplotlib.ticker import FuncFormatter, MaxNLocator
from pyproj import CRS
from rasterio.features import geometry_mask, geometry_window
from rasterio.transform import array_bounds
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
from shapely.geometry import mapping


@dataclass(frozen=True)
class MapStyle:
    basin_fill: str = "#F4E7D3"
    property_fill: str = "#F2D2A2"
    property_edge: str = "#B8A58C"
    native_fill: str = "#6EAA78"
    agreement_fill: str = "#2E8B57"
    disagreement_fill: str = "#D9824B"
    natural_outside_fill: str = "#5B9DB8"
    boundary: str = "#263238"
    grid: str = "#D9DEE2"


STYLE = MapStyle()
ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


def _nice_scale_length(width_m: float) -> float:
    target = max(width_m / 5.0, 1.0)
    exponent = floor(log10(target))
    fraction = target / (10**exponent)
    nice_fraction = 1 if fraction < 1.5 else 2 if fraction < 3.5 else 5
    return nice_fraction * (10**exponent)


def _add_scale_bar(ax, bounds: tuple[float, float, float, float]) -> None:
    minx, _miny, maxx, _maxy = bounds
    width = maxx - minx
    length = _nice_scale_length(width)
    axes_width = ax.get_xlim()[1] - ax.get_xlim()[0]
    bar_width = length / axes_width
    x0, y0 = 0.035, 0.035
    height = 0.013
    segment_width = bar_width / 2

    background = FancyBboxPatch(
        (x0 - 0.012, y0 - 0.029),
        bar_width + 0.024,
        0.064,
        boxstyle="round,pad=0.004,rounding_size=0.006",
        transform=ax.transAxes,
        facecolor="white",
        edgecolor="#B7C0C5",
        linewidth=0.55,
        alpha=0.94,
        zorder=19,
    )
    ax.add_patch(background)
    for index, facecolor in enumerate((STYLE.boundary, "white")):
        ax.add_patch(
            Rectangle(
                (x0 + index * segment_width, y0),
                segment_width,
                height,
                transform=ax.transAxes,
                facecolor=facecolor,
                edgecolor=STYLE.boundary,
                linewidth=0.8,
                zorder=20,
            )
        )

    half = length / 2
    divisor = 1000 if length >= 1000 else 1
    unit = "km" if length >= 1000 else "m"
    labels = ("0", f"{half / divisor:g}", f"{length / divisor:g} {unit}")
    for position, label in zip((x0, x0 + segment_width, x0 + bar_width), labels, strict=True):
        ax.text(
            position,
            y0 - 0.008,
            label,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=6.7,
            color=STYLE.boundary,
            zorder=21,
        )


def _add_north_arrow(ax) -> None:
    icon_path = ASSETS_DIR / "wind_rose_005.png"
    icon = plt.imread(icon_path)
    image = OffsetImage(icon, zoom=0.10, interpolation="hanning")
    artist = AnnotationBbox(
        image,
        (0.958, 0.90),
        xycoords=ax.transAxes,
        frameon=False,
        box_alignment=(0.5, 0.5),
        pad=0,
        zorder=30,
    )
    ax.add_artist(artist)


def _setup_map(
    ax,
    bounds: tuple[float, float, float, float],
    *,
    title: str,
    source: str,
    legend_handles: list,
    legend_title: str,
) -> None:
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    pad_x = max((maxx - minx) * 0.05, 1.0)
    pad_y = max((maxy - miny) * 0.05, 1.0)
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11.5, weight="semibold", pad=12, fontfamily="DejaVu Serif")
    ax.set_xlabel("Coordenada E (km)", fontsize=9)
    ax.set_ylabel("Coordenada N (km)", fontsize=9)
    decimals = 2 if width < 1_000 else 1 if width < 10_000 else 0
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value / 1000:.{decimals}f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value / 1000:.{decimals}f}"))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.tick_params(labelsize=8, colors="#455A64")
    ax.grid(True, color=STYLE.grid, linewidth=0.55, alpha=0.75, zorder=0)
    for spine in ax.spines.values():
        spine.set_color("#7A858C")
        spine.set_linewidth(0.8)

    _add_north_arrow(ax)
    _add_scale_bar(ax, bounds)
    ax.legend(
        handles=legend_handles,
        title=legend_title,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=True,
        facecolor="white",
        edgecolor="#B0B7BC",
        fontsize=8,
        title_fontsize=8,
    )
    ax.text(
        0.99,
        0.012,
        source,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.5,
        color="#59636A",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.5},
        zorder=40,
    )


def _save_figure(fig, output_base: Path) -> list[Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    png = output_base.with_suffix(".png")
    svg = output_base.with_suffix(".svg")
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [png, svg]


def _plot_study_area(
    study_area: gpd.GeoDataFrame,
    properties: gpd.GeoDataFrame,
    output_base: Path,
) -> list[Path]:
    fig, ax = plt.subplots(figsize=(11.2, 7.0))
    study_area.plot(ax=ax, color=STYLE.basin_fill, edgecolor=STYLE.boundary, linewidth=1.2, zorder=1)
    properties.boundary.plot(ax=ax, color=STYLE.property_edge, linewidth=0.28, alpha=0.85, zorder=2)
    study_area.boundary.plot(ax=ax, color=STYLE.boundary, linewidth=1.25, zorder=3)
    handles = [
        Patch(facecolor=STYLE.basin_fill, edgecolor=STYLE.boundary, label="Bacia do rio Gramame"),
        Line2D([0], [0], color=STYLE.property_edge, linewidth=1.0, label="Imóveis rurais do CAR"),
    ]
    _setup_map(
        ax,
        tuple(study_area.total_bounds),
        title="Área de estudo e imóveis rurais na bacia do rio Gramame",
        source="Fonte: AESA e SICAR. Elaboração própria (2026).",
        legend_handles=handles,
        legend_title="Camadas",
    )
    fig.subplots_adjust(left=0.09, right=0.79, bottom=0.11, top=0.90)
    return _save_figure(fig, output_base)


def _plot_declared_native(
    study_area: gpd.GeoDataFrame,
    properties: gpd.GeoDataFrame,
    declared_native: gpd.GeoDataFrame,
    output_base: Path,
) -> list[Path]:
    fig, ax = plt.subplots(figsize=(11.2, 7.0))
    study_area.plot(ax=ax, color="#FAFAF7", edgecolor="none", zorder=1)
    properties.plot(
        ax=ax,
        color=STYLE.property_fill,
        edgecolor=STYLE.property_edge,
        linewidth=0.22,
        alpha=0.55,
        zorder=2,
    )
    declared_native.plot(ax=ax, color=STYLE.native_fill, edgecolor="#3F6F4B", linewidth=0.18, alpha=0.9, zorder=3)
    study_area.boundary.plot(ax=ax, color=STYLE.boundary, linewidth=1.2, zorder=4)
    handles = [
        Patch(facecolor=STYLE.property_fill, edgecolor=STYLE.property_edge, label="Imóveis rurais"),
        Patch(facecolor=STYLE.native_fill, edgecolor="#3F6F4B", label="Vegetação nativa declarada"),
    ]
    _setup_map(
        ax,
        tuple(study_area.total_bounds),
        title="Vegetação nativa declarada no Cadastro Ambiental Rural",
        source="Fonte: SICAR. Elaboração própria (2026).",
        legend_handles=handles,
        legend_title="Cadastro Ambiental Rural",
    )
    fig.subplots_adjust(left=0.09, right=0.79, bottom=0.11, top=0.90)
    return _save_figure(fig, output_base)


def _comparison_grid(
    raster_path: Path,
    study_area: gpd.GeoDataFrame,
    properties: gpd.GeoDataFrame,
    declared_native: gpd.GeoDataFrame,
    *,
    target_crs: str,
    resolution_m: float,
    natural_codes: Iterable[int],
    all_touched: bool,
) -> tuple[np.ma.MaskedArray, tuple[float, float, float, float], rasterio.Affine]:
    study = study_area.to_crs(target_crs).geometry.union_all(method="unary")
    property_geometry = properties.to_crs(target_crs).geometry.union_all(method="unary")
    declared_geometry = declared_native.to_crs(target_crs).geometry.union_all(method="unary")
    study_shapes = [mapping(study)]
    codes = np.asarray(tuple(natural_codes), dtype=np.int64)

    with rasterio.open(raster_path) as source:
        with WarpedVRT(
            source,
            crs=CRS.from_user_input(target_crs),
            resolution=resolution_m,
            resampling=Resampling.nearest,
            nodata=source.nodata,
        ) as raster:
            window = geometry_window(raster, study_shapes)
            values = raster.read(1, window=window, masked=True)
            transform = raster.window_transform(window)
            shape = values.shape
            inside_study = geometry_mask(study_shapes, shape, transform, invert=True, all_touched=all_touched)
            inside_properties = geometry_mask(
                [mapping(property_geometry)], shape, transform, invert=True, all_touched=all_touched
            )
            inside_declared = geometry_mask(
                [mapping(declared_geometry)], shape, transform, invert=True, all_touched=all_touched
            )
            valid = inside_study & ~np.ma.getmaskarray(values)
            natural = np.isin(np.asarray(values.data), codes)
            categories = np.zeros(shape, dtype=np.uint8)
            categories[valid & inside_declared & natural] = 1
            categories[valid & inside_declared & ~natural] = 2
            categories[valid & inside_properties & ~inside_declared & natural] = 3
            masked = np.ma.masked_where(categories == 0, categories)
            west, south, east, north = array_bounds(shape[0], shape[1], transform)
            return masked, (west, east, south, north), transform


def export_comparison_raster(
    *,
    output_path: Path,
    raster_path: Path,
    study_area: gpd.GeoDataFrame,
    properties: gpd.GeoDataFrame,
    declared_native: gpd.GeoDataFrame,
    target_crs: str,
    resolution_m: float,
    natural_codes: Iterable[int],
    all_touched: bool,
) -> Path:
    """Exporta as três classes da comparação como GeoTIFF para uso no QGIS."""
    categories, _extent, transform = _comparison_grid(
        raster_path,
        study_area,
        properties,
        declared_native,
        target_crs=target_crs,
        resolution_m=resolution_m,
        natural_codes=natural_codes,
        all_touched=all_touched,
    )
    data = categories.filled(0).astype(np.uint8)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        width=data.shape[1],
        height=data.shape[0],
        count=1,
        dtype="uint8",
        crs=target_crs,
        transform=transform,
        nodata=0,
        compress="deflate",
        tiled=True,
    ) as dataset:
        dataset.write(data, 1)
        dataset.set_band_description(1, "Convergência CAR × MapBiomas 2025")
        dataset.update_tags(
            classe_1="Declarada e natural no MapBiomas",
            classe_2="Declarada sem classe natural",
            classe_3="Natural no imóvel fora da declaração",
        )
    return output_path


def _plot_comparison(
    study_area: gpd.GeoDataFrame,
    properties: gpd.GeoDataFrame,
    declared_native: gpd.GeoDataFrame,
    raster_path: Path,
    output_base: Path,
    *,
    target_crs: str,
    resolution_m: float,
    natural_codes: Iterable[int],
    all_touched: bool,
) -> list[Path]:
    categories, extent, _transform = _comparison_grid(
        raster_path,
        study_area,
        properties,
        declared_native,
        target_crs=target_crs,
        resolution_m=resolution_m,
        natural_codes=natural_codes,
        all_touched=all_touched,
    )
    fig, ax = plt.subplots(figsize=(11.2, 7.0))
    study_area.plot(ax=ax, color="#FAFAF7", edgecolor="none", zorder=1)
    cmap = ListedColormap([STYLE.agreement_fill, STYLE.disagreement_fill, STYLE.natural_outside_fill])
    norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)
    ax.imshow(categories, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest", zorder=2)
    properties.boundary.plot(ax=ax, color="#C1C8CC", linewidth=0.16, alpha=0.6, zorder=3)
    study_area.boundary.plot(ax=ax, color=STYLE.boundary, linewidth=1.2, zorder=4)
    handles = [
        Patch(facecolor=STYLE.agreement_fill, label="Declarada e natural no MapBiomas"),
        Patch(facecolor=STYLE.disagreement_fill, label="Declarada sem classe natural"),
        Patch(facecolor=STYLE.natural_outside_fill, label="Natural no imóvel fora da declaração"),
    ]
    _setup_map(
        ax,
        tuple(study_area.total_bounds),
        title="Convergência espacial entre CAR e MapBiomas 2025",
        source="Fonte: SICAR e MapBiomas Coleção 11. Elaboração própria (2026).",
        legend_handles=handles,
        legend_title="Classes de análise",
    )
    fig.subplots_adjust(left=0.09, right=0.76, bottom=0.11, top=0.90)
    return _save_figure(fig, output_base)


def generate_maps(
    *,
    output_dir: Path,
    study_area: gpd.GeoDataFrame,
    properties: gpd.GeoDataFrame,
    declared_native: gpd.GeoDataFrame,
    mapbiomas_path: Path,
    target_crs: str,
    resolution_m: float,
    natural_codes: Iterable[int],
    all_touched: bool,
) -> list[Path]:
    figures_dir = output_dir / "figuras"
    outputs: list[Path] = []
    outputs.extend(_plot_study_area(study_area, properties, figures_dir / "mapa_01_area_estudo"))
    outputs.extend(
        _plot_declared_native(study_area, properties, declared_native, figures_dir / "mapa_02_vegetacao_declarada")
    )
    outputs.extend(
        _plot_comparison(
            study_area,
            properties,
            declared_native,
            mapbiomas_path,
            figures_dir / "mapa_03_convergencia_car_mapbiomas",
            target_crs=target_crs,
            resolution_m=resolution_m,
            natural_codes=natural_codes,
            all_touched=all_touched,
        )
    )
    return outputs
