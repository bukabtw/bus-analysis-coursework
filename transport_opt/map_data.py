from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, radians

import pandas as pd


Coordinate = tuple[float, float]

ROUTE_COLORS = [
    "#E53E3E",
    "#3182CE",
    "#38A169",
    "#D69E2E",
    "#805AD5",
    "#DD6B20",
    "#319795",
    "#D53F8C",
    "#4A5568",
    "#2B6CB0",
    "#ED8936",
    "#9F7AEA",
]

DEFAULT_NETWORK_BOUNDS = (55.614, 37.3798, 55.886, 37.9102)
PRIMARY_FRACTIONS = [0.0, 0.25, 0.5, 0.75, 1.0]
SECONDARY_FRACTIONS = [0.125, 0.375, 0.625, 0.875]
DEFAULT_STOPS_PER_ROUTE = 6
ROUTE_POINT_SPACING_KM = 0.28
TERMINAL_DWELL_HOURS = 0.12
DISPLAY_PADDING_RATIO = 0.12

ROUTE_TEMPLATE_SEQUENCE = [
    ("horizontal", 0, False),
    ("horizontal", 2, True),
    ("horizontal", 4, False),
    ("horizontal", 6, True),
    ("horizontal", 8, False),
    ("horizontal", 1, True),
    ("vertical", 0, False),
    ("vertical", 2, True),
    ("vertical", 4, False),
    ("vertical", 6, True),
    ("vertical", 8, False),
    ("vertical", 1, True),
    ("horizontal", 3, False),
    ("horizontal", 5, True),
    ("horizontal", 7, False),
    ("vertical", 3, True),
    ("vertical", 5, False),
    ("vertical", 7, True),
]


@dataclass(frozen=True)
class MapBounds:
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


@dataclass(frozen=True)
class DistrictShape:
    name: str
    polygon: list[Coordinate]
    fill_color: str
    border_color: str = "#B9C2CC"


@dataclass(frozen=True)
class RoadShape:
    name: str
    path: list[Coordinate]
    color: str = "#5B6775"


@dataclass(frozen=True)
class RouteShape:
    route_id: int
    name: str
    color: str
    path: list[Coordinate]
    stops: list["StopShape"] = field(default_factory=list)


@dataclass(frozen=True)
class StopShape:
    stop_id: int
    name: str
    route_id: int
    route_name: str
    district: str
    demand: int
    coord: Coordinate


@dataclass(frozen=True)
class BusMarker:
    bus_id: int
    route_id: int
    route_name: str
    coord: Coordinate
    color: str
    speed_kmh: float


@dataclass(frozen=True)
class MapStaticData:
    bounds: MapBounds
    districts: list[DistrictShape]
    roads: list[RoadShape]
    routes: list[RouteShape]
    stops: list[StopShape]
    route_lookup: dict[int, list[Coordinate]] = field(default_factory=dict)
    route_colors: dict[int, str] = field(default_factory=dict)
    route_names: dict[int, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteTemplate:
    orientation: str
    line_index: int
    reverse: bool
    reuse_index: int = 0


def enrich_stops_with_coords(stops: pd.DataFrame, routes: pd.DataFrame, bounds: MapBounds) -> pd.DataFrame:
    normalized_stops = _normalize_stops_frame(stops, routes)
    if normalized_stops.empty:
        return pd.DataFrame(columns=["id", "name", "route_id", "lat", "lon"])

    route_ids = sorted(normalized_stops["route_id"].astype(int).unique().tolist())
    route_paths = _build_route_paths(route_ids, bounds)

    enriched_groups: list[pd.DataFrame] = []
    for route_id, group in normalized_stops.groupby("route_id", sort=True):
        ordered = group.sort_values("id").copy()
        path = route_paths[int(route_id)]
        sampled_points = _sample_points_along_path(path, len(ordered))
        ordered["lat"] = [lat for lat, _ in sampled_points]
        ordered["lon"] = [lon for _, lon in sampled_points]
        enriched_groups.append(ordered)

    return (
        pd.concat(enriched_groups, ignore_index=True)
        .sort_values(["route_id", "id"])
        .reset_index(drop=True)
    )


def build_map_static(routes: pd.DataFrame, stops: pd.DataFrame, flow: pd.DataFrame) -> MapStaticData:
    network_bounds = _default_network_bounds()
    display_bounds = _expand_bounds(network_bounds, DISPLAY_PADDING_RATIO)

    if routes.empty:
        return MapStaticData(
            bounds=display_bounds,
            districts=_build_districts(network_bounds),
            roads=_build_roads_improved(network_bounds),
            routes=[],
            stops=[],
            route_lookup={},
            route_colors={},
            route_names={},
        )

    route_names = {
        int(row["id"]): str(row["name"])
        for _, row in routes.sort_values("id").iterrows()
    }
    route_ids = sorted(route_names)
    route_colors = {
        route_id: ROUTE_COLORS[index % len(ROUTE_COLORS)]
        for index, route_id in enumerate(route_ids)
    }

    enriched_stops = enrich_stops_with_coords(stops, routes, network_bounds)
    route_paths = _build_route_paths(route_ids, network_bounds)
    districts = _build_districts(network_bounds)
    roads = _build_roads_improved(network_bounds)

    demand_by_stop: dict[int, int] = {}
    if not flow.empty and {"stop_id", "count"}.issubset(flow.columns):
        demand_by_stop = flow.groupby("stop_id")["count"].sum().astype(int).to_dict()

    route_lookup: dict[int, list[Coordinate]] = {}
    route_shapes: list[RouteShape] = []
    all_stops: list[StopShape] = []

    for route_id in route_ids:
        dense_path = _densify_polyline(route_paths[route_id], ROUTE_POINT_SPACING_KM)
        route_lookup[route_id] = dense_path

        group = enriched_stops[enriched_stops["route_id"] == route_id].sort_values("id")
        route_stops: list[StopShape] = []
        for _, row in group.iterrows():
            coord = (float(row["lat"]), float(row["lon"]))
            stop = StopShape(
                stop_id=int(row["id"]),
                name=str(row["name"]),
                route_id=route_id,
                route_name=route_names.get(route_id, f"Route {route_id}"),
                district=_district_for_point(coord[0], coord[1], districts),
                demand=int(demand_by_stop.get(int(row["id"]), 0)),
                coord=coord,
            )
            route_stops.append(stop)
            all_stops.append(stop)

        route_shapes.append(
            RouteShape(
                route_id=route_id,
                name=route_names.get(route_id, f"Route {route_id}"),
                color=route_colors[route_id],
                path=dense_path,
                stops=route_stops,
            )
        )

    return MapStaticData(
        bounds=display_bounds,
        districts=districts,
        roads=roads,
        routes=route_shapes,
        stops=all_stops,
        route_lookup=route_lookup,
        route_colors=route_colors,
        route_names=route_names,
    )


def simulate_bus_positions(
    buses: pd.DataFrame,
    route_lookup: dict[int, list[Coordinate]],
    route_colors: dict[int, str],
    route_names: dict[int, str],
    hour: float,
) -> list[BusMarker]:
    normalized_hour = float(hour) % 24.0
    fallback_path = next(iter(route_lookup.values()), [(55.75, 37.61)])
    markers: list[BusMarker] = []

    for _, row in buses.sort_values("id").iterrows():
        bus_id = int(row["id"])
        route_id = int(row.get("route_id", 1) or 1)
        path = route_lookup.get(route_id, fallback_path)
        speed_kmh = float(19 + ((route_id * 11 + bus_id * 5) % 16))
        coord = _round_trip_position(path, normalized_hour, route_id, bus_id, speed_kmh)
        markers.append(
            BusMarker(
                bus_id=bus_id,
                route_id=route_id,
                route_name=route_names.get(route_id, f"Route {route_id}"),
                coord=coord,
                color=route_colors.get(route_id, ROUTE_COLORS[0]),
                speed_kmh=speed_kmh,
            )
        )

    return markers


def _default_network_bounds() -> MapBounds:
    min_lat, min_lon, max_lat, max_lon = DEFAULT_NETWORK_BOUNDS
    return MapBounds(min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon)


def _expand_bounds(bounds: MapBounds, padding_ratio: float) -> MapBounds:
    lat_pad = (bounds.max_lat - bounds.min_lat) * padding_ratio
    lon_pad = (bounds.max_lon - bounds.min_lon) * padding_ratio
    return MapBounds(
        min_lat=bounds.min_lat - lat_pad,
        min_lon=bounds.min_lon - lon_pad,
        max_lat=bounds.max_lat + lat_pad,
        max_lon=bounds.max_lon + lon_pad,
    )


def _normalize_stops_frame(stops: pd.DataFrame, routes: pd.DataFrame) -> pd.DataFrame:
    route_ids = sorted(routes["id"].astype(int).unique().tolist()) if not routes.empty else []
    columns = ["id", "name", "route_id"]

    normalized = pd.DataFrame(columns=columns)
    if not stops.empty and set(columns).issubset(stops.columns):
        normalized = stops[columns].copy()
        normalized["id"] = normalized["id"].astype(int)
        normalized["route_id"] = normalized["route_id"].astype(int)
        normalized["name"] = normalized["name"].astype(str)

    generated_rows: list[dict[str, object]] = []
    existing_route_ids = set(normalized["route_id"].astype(int).tolist()) if not normalized.empty else set()
    for route_id in route_ids:
        if route_id in existing_route_ids:
            continue
        for stop_index in range(DEFAULT_STOPS_PER_ROUTE):
            generated_rows.append(
                {
                    "id": route_id * 100 + stop_index + 1,
                    "name": f"Route {route_id} Stop {stop_index + 1}",
                    "route_id": route_id,
                }
            )

    if generated_rows:
        normalized = pd.concat(
            [normalized, pd.DataFrame(generated_rows, columns=columns)],
            ignore_index=True,
        )

    return normalized.sort_values(["route_id", "id"]).reset_index(drop=True)


def _build_route_paths(route_ids: list[int], bounds: MapBounds) -> dict[int, list[Coordinate]]:
    horizontal_lines, vertical_lines = _grid_lines(bounds)
    route_paths: dict[int, list[Coordinate]] = {}

    for route_id in route_ids:
        template = _route_template(route_id)
        if template.orientation == "horizontal":
            lat = _apply_lane_offset(
                horizontal_lines[template.line_index],
                bounds.max_lat - bounds.min_lat,
                template.reuse_index,
            )
            path = [(lat, bounds.min_lon), (lat, bounds.max_lon)]
        else:
            lon = _apply_lane_offset(
                vertical_lines[template.line_index],
                bounds.max_lon - bounds.min_lon,
                template.reuse_index,
            )
            path = [(bounds.min_lat, lon), (bounds.max_lat, lon)]

        if template.reverse:
            path = list(reversed(path))
        route_paths[route_id] = path

    return route_paths


def _grid_lines(bounds: MapBounds) -> tuple[list[float], list[float]]:
    horizontal_lines = [
        bounds.min_lat + (bounds.max_lat - bounds.min_lat) * fraction
        for fraction in _combined_fractions()
    ]
    vertical_lines = [
        bounds.min_lon + (bounds.max_lon - bounds.min_lon) * fraction
        for fraction in _combined_fractions()
    ]
    return horizontal_lines, vertical_lines


def _combined_fractions() -> list[float]:
    return sorted(PRIMARY_FRACTIONS + SECONDARY_FRACTIONS)


def _route_template(route_id: int) -> RouteTemplate:
    sequence_index = max(route_id - 1, 0)
    template_index = sequence_index % len(ROUTE_TEMPLATE_SEQUENCE)
    reuse_index = sequence_index // len(ROUTE_TEMPLATE_SEQUENCE)
    orientation, line_index, reverse = ROUTE_TEMPLATE_SEQUENCE[template_index]
    return RouteTemplate(
        orientation=orientation,
        line_index=line_index,
        reverse=reverse,
        reuse_index=reuse_index,
    )


def _apply_lane_offset(base_value: float, span: float, reuse_index: int) -> float:
    if reuse_index == 0:
        return base_value

    tier = (reuse_index + 1) // 2
    direction = 1 if reuse_index % 2 else -1
    return base_value + direction * span * 0.01 * tier


def _sample_points_along_path(path: list[Coordinate], count: int) -> list[Coordinate]:
    if count <= 0 or not path:
        return []
    if len(path) == 1:
        return [path[0]] * count
    if count == 1:
        return [_interpolate(path, 0.5)]

    cumulative = _cumulative_distances(path)
    total_length = cumulative[-1]
    if total_length <= 0:
        return [path[0]] * count

    sampled: list[Coordinate] = []
    for index in range(count):
        target = total_length * index / (count - 1)
        sampled.append(_coordinate_at_distance(path, cumulative, target))
    return sampled


def _densify_polyline(path: list[Coordinate], spacing_km: float) -> list[Coordinate]:
    if len(path) < 2:
        return path[:]

    dense_path: list[Coordinate] = [path[0]]
    for start, end in zip(path, path[1:]):
        segment_length = max(_segment_distance_km(start, end), spacing_km)
        steps = max(int(segment_length / spacing_km), 1)
        for step in range(1, steps + 1):
            fraction = step / steps
            dense_path.append(
                (
                    start[0] + (end[0] - start[0]) * fraction,
                    start[1] + (end[1] - start[1]) * fraction,
                )
            )
    return dense_path


def _cumulative_distances(path: list[Coordinate]) -> list[float]:
    cumulative = [0.0]
    total = 0.0
    for start, end in zip(path, path[1:]):
        total += _segment_distance_km(start, end)
        cumulative.append(total)
    return cumulative


def _coordinate_at_distance(
    path: list[Coordinate],
    cumulative: list[float],
    target_distance: float,
) -> Coordinate:
    if target_distance <= 0:
        return path[0]
    if target_distance >= cumulative[-1]:
        return path[-1]

    for index in range(len(cumulative) - 1):
        start_distance = cumulative[index]
        end_distance = cumulative[index + 1]
        if target_distance > end_distance:
            continue

        segment_length = max(end_distance - start_distance, 1e-9)
        fraction = (target_distance - start_distance) / segment_length
        start = path[index]
        end = path[index + 1]
        return (
            start[0] + (end[0] - start[0]) * fraction,
            start[1] + (end[1] - start[1]) * fraction,
        )

    return path[-1]


def _round_trip_position(
    path: list[Coordinate],
    hour: float,
    route_id: int,
    bus_id: int,
    speed_kmh: float,
) -> Coordinate:
    if not path:
        return 55.75, 37.61
    if len(path) == 1:
        return path[0]

    route_length_km = max(_polyline_length_km(path), 0.5)
    travel_hours = max(route_length_km / max(speed_kmh, 1.0), 0.4)
    cycle_hours = travel_hours * 2 + TERMINAL_DWELL_HOURS * 2
    phase_shift = ((route_id * 0.19) + (bus_id * 0.37)) % 1.0
    time_in_cycle = (hour + phase_shift * cycle_hours) % cycle_hours

    if time_in_cycle <= TERMINAL_DWELL_HOURS:
        return path[0]

    if time_in_cycle <= TERMINAL_DWELL_HOURS + travel_hours:
        progress = (time_in_cycle - TERMINAL_DWELL_HOURS) / travel_hours
        return _interpolate(path, progress)

    if time_in_cycle <= TERMINAL_DWELL_HOURS * 2 + travel_hours:
        return path[-1]

    backward_progress = (
        time_in_cycle - (TERMINAL_DWELL_HOURS * 2 + travel_hours)
    ) / travel_hours
    return _interpolate(path, 1.0 - backward_progress)


def _polyline_length_km(path: list[Coordinate]) -> float:
    return sum(_segment_distance_km(start, end) for start, end in zip(path, path[1:]))


def _segment_distance_km(start: Coordinate, end: Coordinate) -> float:
    avg_lat = radians((start[0] + end[0]) / 2.0)
    lat_km = (end[0] - start[0]) * 111.32
    lon_km = (end[1] - start[1]) * 111.32 * cos(avg_lat)
    return (lat_km * lat_km + lon_km * lon_km) ** 0.5


def _build_districts(bounds: MapBounds) -> list[DistrictShape]:
    width = bounds.max_lon - bounds.min_lon
    height = bounds.max_lat - bounds.min_lat

    x_edges = [bounds.min_lon + width * (index * 0.25) for index in range(5)]
    y_edges = [bounds.min_lat + height * (index * 0.25) for index in range(5)]

    names_matrix = [
        ["1. Академгородок", "2. Речной порт", "3. Старый парк", "4. Студгородок"],
        ["5. Дипломатический", "6. Центр Сити", "7. Деловой квартал", "8. Набережная"],
        ["9. Спальный район", "10. Центральный парк", "11. Экспо-центр", "12. Промзона А"],
        ["13. Малоэтажки", "14. Спортивный кластер", "15. Технопарк", "16. Южный узел"]
    ]

    colors_matrix = [
        ["#2C5F8A", "#1F4E5F", "#4A6A3B", "#3D6B8F"],
        ["#203A43", "#324B4B", "#2C5364", "#3D5A3E"],
        ["#4E6A4A", "#5A7B4A", "#4E7A5A", "#4A3945"],
        ["#5A4955", "#2E4057", "#4A5568", "#5A4A55"],
    ]

    districts: list[DistrictShape] = []
    for row_index in range(4):
        for column_index in range(4):
            x1 = x_edges[column_index]
            x2 = x_edges[column_index + 1]
            y1 = y_edges[row_index]
            y2 = y_edges[row_index + 1]
            districts.append(
                DistrictShape(
                    name=names_matrix[row_index][column_index],
                    polygon=_rect_to_polygon(x1, y1, x2, y2),
                    fill_color=colors_matrix[row_index][column_index],
                )
            )

    return districts


def _build_roads_improved(bounds: MapBounds) -> list[RoadShape]:
    roads: list[RoadShape] = []
    combined = _combined_fractions()

    for index, fraction in enumerate(combined, start=1):
        lat = bounds.min_lat + (bounds.max_lat - bounds.min_lat) * fraction
        road_color = "#7C8B9A" if fraction in PRIMARY_FRACTIONS else "#9CA3AF"
        roads.append(
            RoadShape(
                name=f"East-West {index}",
                path=[(lat, bounds.min_lon), (lat, bounds.max_lon)],
                color=road_color,
            )
        )

    for index, fraction in enumerate(combined, start=1):
        lon = bounds.min_lon + (bounds.max_lon - bounds.min_lon) * fraction
        road_color = "#7C8B9A" if fraction in PRIMARY_FRACTIONS else "#9CA3AF"
        roads.append(
            RoadShape(
                name=f"North-South {index}",
                path=[(bounds.min_lat, lon), (bounds.max_lat, lon)],
                color=road_color,
            )
        )

    return roads


def _district_for_point(lat: float, lon: float, districts: list[DistrictShape]) -> str:
    for district in districts:
        lats = [coord[0] for coord in district.polygon]
        lons = [coord[1] for coord in district.polygon]
        if min(lats) <= lat <= max(lats) and min(lons) <= lon <= max(lons):
            return district.name

    nearest_name = districts[0].name
    nearest_distance = float("inf")
    for district in districts:
        center_lat = sum(coord[0] for coord in district.polygon[:-1]) / 4
        center_lon = sum(coord[1] for coord in district.polygon[:-1]) / 4
        distance = ((lat - center_lat) ** 2 + (lon - center_lon) ** 2) ** 0.5
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_name = district.name
    return nearest_name


def _rect_to_polygon(x1: float, y1: float, x2: float, y2: float) -> list[Coordinate]:
    return [(y1, x1), (y2, x1), (y2, x2), (y1, x2), (y1, x1)]


def _interpolate(path: list[Coordinate], progress: float) -> Coordinate:
    if not path:
        return 55.75, 37.61
    if len(path) == 1:
        return path[0]

    clamped_progress = max(0.0, min(1.0, progress))
    segment_position = clamped_progress * (len(path) - 1)
    segment_index = min(int(segment_position), len(path) - 2)
    fraction = segment_position - segment_index

    lat1, lon1 = path[segment_index]
    lat2, lon2 = path[segment_index + 1]
    return lat1 + (lat2 - lat1) * fraction, lon1 + (lon2 - lon1) * fraction

