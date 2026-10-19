import math
import re
from dataclasses import dataclass
from typing import Optional, Tuple
from fastapi import HTTPException
import shapely.wkt
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

# Canonical Cadastral Invariants for Lima Metropolitan Cadastre (ISO 19152 LADM)
CANONICAL_SRID = 32718  # WGS 84 / UTM Zone 18S (metric)
UTM_X_MIN, UTM_X_MAX = 260000.0, 310000.0
UTM_Y_MIN, UTM_Y_MAX = 8640000.0, 8700000.0

MAX_VERTEX_COUNT = 500
MIN_VERTEX_COUNT = 4
MAX_MBR_AREA_M2 = 250000.0       # Max viewport / query MBR area (25 ha)
REFERENCE_SECTOR_AREA_M2 = 50000.0
MAX_BUFFER_METERS = 100.0
MAX_QUAD_SEGS = 16
MAX_SNAP_TOLERANCE_M = 0.05      # Max topological grid snap tolerance (5 cm)
MAX_COMPUTATIONAL_COST = 5000.0  # Threshold tau_max for geometric cost estimator


@dataclass
class SpatialValidationResult:
    geometry: Optional[Polygon]
    srid: int
    vertex_count: int
    mbr_area_m2: float
    estimated_cost: float
    sanitized_wkt: Optional[str]


class SpatialCostAndInvariantGuard:
    """
    Intrinsically spatial defense mechanism (SCIG) enforcing:
    1. Coordinate Reference System (CRS) pinning and metric domain bounding.
    2. DE-9IM geometry type invariant (strict 2D simple Polygon) and MBR area cap.
    3. Deterministic geometric computational cost estimation (C_geom <= tau_max).
    """

    EWKT_SRID_PATTERN = re.compile(r"^\s*SRID\s*=\s*(\d+)\s*;\s*(.+)$", re.IGNORECASE | re.DOTALL)

    @classmethod
    def validate_crs_and_point(cls, x: float, y: float, srid: int = CANONICAL_SRID) -> Tuple[float, float, int]:
        if srid != CANONICAL_SRID:
            raise HTTPException(
                status_code=422,
                detail=f"CRS Confusion Guard: SRID {srid} rejected. Canonical metric SRID {CANONICAL_SRID} required."
            )
        if not (math.isfinite(x) and math.isfinite(y)):
            raise HTTPException(status_code=422, detail="Invalid non-finite coordinate values.")
        if not (UTM_X_MIN <= x <= UTM_X_MAX and UTM_Y_MIN <= y <= UTM_Y_MAX):
            raise HTTPException(
                status_code=422,
                detail=f"Coordinate ({x}, {y}) outside municipal UTM 18S domain envelope."
            )
        return x, y, CANONICAL_SRID

    @classmethod
    def validate_envelope(cls, xmin: float, ymin: float, xmax: float, ymax: float, srid: int = CANONICAL_SRID) -> float:
        cls.validate_crs_and_point(xmin, ymin, srid)
        cls.validate_crs_and_point(xmax, ymax, srid)
        dx = xmax - xmin
        dy = ymax - ymin
        if dx <= 0 or dy <= 0:
            raise HTTPException(status_code=422, detail="Degenerate or inverted bounding box coordinates.")
        mbr_area = dx * dy
        if mbr_area > MAX_MBR_AREA_M2:
            raise HTTPException(
                status_code=422,
                detail=f"MBR Poisoning Guard: Envelope area ({mbr_area:.1f} m2) exceeds limit ({MAX_MBR_AREA_M2:.1f} m2)."
            )
        return mbr_area

    @classmethod
    def estimate_geometric_cost(
        cls,
        vertex_count: int,
        buffer_radius_m: float = 0.0,
        quad_segs: int = 8,
        mbr_area_m2: float = 1000.0,
        candidate_features: int = 1
    ) -> float:
        """
        Computes deterministic geometric computational cost:
        C_geom = N_cand * V(g) * (1 + 4 * q_eff) * (1 + Area(MBR(g, r)) / A_sector)
        """
        if buffer_radius_m < 0 or buffer_radius_m > MAX_BUFFER_METERS:
            raise HTTPException(
                status_code=422,
                detail=f"Buffer radius ({buffer_radius_m} m) exceeds operational bound ({MAX_BUFFER_METERS} m)."
            )
        if quad_segs < 1 or quad_segs > MAX_QUAD_SEGS:
            raise HTTPException(
                status_code=422,
                detail=f"Quadrant segment density ({quad_segs}) exceeds complexity bound ({MAX_QUAD_SEGS})."
            )
        q_factor = (1 + 4 * quad_segs) if buffer_radius_m > 0 else 1
        expanded_area = mbr_area_m2 + (math.pi * (buffer_radius_m ** 2))
        area_factor = 1.0 + (expanded_area / REFERENCE_SECTOR_AREA_M2)
        cost = float(candidate_features) * float(vertex_count) * float(q_factor) * area_factor
        if cost > MAX_COMPUTATIONAL_COST:
            raise HTTPException(
                status_code=422,
                detail=f"Geometric Cost Guard: Estimated cost ({cost:.1f}) exceeds budget ({MAX_COMPUTATIONAL_COST})."
            )
        return cost

    @classmethod
    def validate_wkt_polygon(
        cls,
        raw_wkt: str,
        buffer_radius_m: float = 0.0,
        quad_segs: int = 8
    ) -> SpatialValidationResult:
        if not raw_wkt or len(raw_wkt) > 5000:
            raise HTTPException(status_code=422, detail="WKT payload length invalid.")

        srid = CANONICAL_SRID
        clean_wkt = raw_wkt.strip()

        # Detect EWKT SRID prefix (e.g., SRID=4326;POLYGON(...))
        match = cls.EWKT_SRID_PATTERN.match(clean_wkt)
        if match:
            srid = int(match.group(1))
            clean_wkt = match.group(2).strip()
            if srid != CANONICAL_SRID:
                raise HTTPException(
                    status_code=422,
                    detail=f"CRS Confusion Guard: Embedded EWKT SRID={srid} rejected; expected {CANONICAL_SRID}."
                )

        try:
            geom: BaseGeometry = shapely.wkt.loads(clean_wkt)
        except Exception:
            raise HTTPException(status_code=422, detail="Malformed WKT syntax rejected prior to database parse.")

        # Enforce strict 2D Polygon type (prevents GEOMETRYCOLLECTION / MULTIPOLYGON coercion)
        if type(geom) is not Polygon or geom.geom_type != "Polygon":
            raise HTTPException(
                status_code=422,
                detail=f"Geometry Type Coercion Guard: Type '{geom.geom_type}' rejected; strict POLYGON required."
            )

        if geom.has_z:
            raise HTTPException(status_code=422, detail="Dimensionality Guard: 3D/Z coordinates rejected.")

        if geom.is_empty or not geom.is_valid or not geom.is_simple:
            raise HTTPException(
                status_code=422,
                detail="Topological Invariant Guard: Non-simple, self-intersecting, or invalid ring topology."
            )

        # Count vertices across exterior and interior rings
        v_count = len(geom.exterior.coords) + sum(len(ring.coords) for ring in geom.interiors)
        if v_count < MIN_VERTEX_COUNT or v_count > MAX_VERTEX_COUNT:
            raise HTTPException(
                status_code=422,
                detail=f"Vertex Count Guard: {v_count} vertices outside allowed range [{MIN_VERTEX_COUNT}, {MAX_VERTEX_COUNT}]."
            )

        # Validate MBR coordinates and envelope area
        xmin, ymin, xmax, ymax = geom.bounds
        mbr_area = cls.validate_envelope(xmin, ymin, xmax, ymax, srid)

        if geom.area <= 0.1:
            raise HTTPException(status_code=422, detail="Degenerate sliver polygon rejected (area <= 0.1 m2).")

        cost = cls.estimate_geometric_cost(
            vertex_count=v_count,
            buffer_radius_m=buffer_radius_m,
            quad_segs=quad_segs,
            mbr_area_m2=mbr_area
        )

        return SpatialValidationResult(
            geometry=geom,
            srid=srid,
            vertex_count=v_count,
            mbr_area_m2=mbr_area,
            estimated_cost=cost,
            sanitized_wkt=geom.wkt
        )
