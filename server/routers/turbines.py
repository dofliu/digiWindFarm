from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from server.models import TurbineReading, FarmStatus

router = APIRouter(prefix="/api/turbines", tags=["turbines"])


def get_broker():
    from server.app import broker
    return broker


@router.get("", response_model=List[TurbineReading])
async def list_turbines():
    """List all turbines with latest data."""
    return get_broker().get_all_turbines()


@router.get("/farm-status", response_model=FarmStatus)
async def farm_status():
    """Get farm-level KPIs."""
    return get_broker().get_farm_status()


@router.get("/farm-trend")
async def farm_trend(
    time_range: str = Query("5m", alias="range", description="Time range: 5m, 1h, 12h, 1d"),
    points: int = Query(150, ge=10, le=500, description="Target data points"),
):
    """Get farm-wide aggregated trend data (total power, avg wind speed).

    For short ranges (5m, 1h): uses in-memory simulator buffer.
    For longer ranges (12h, 1d): queries SQLite with downsampling.
    """
    broker = get_broker()

    range_map = {"5m": 300, "1h": 3600, "12h": 43200, "1d": 86400}
    seconds = range_map.get(time_range, 300)

    # Short ranges: use in-memory buffer (fast)
    if seconds <= 3600 and broker.simulator:
        all_ids = broker.turbine_ids
        if not all_ids:
            return {"range": time_range, "count": 0, "data": []}

        limit = min(seconds, 3600)
        ref_history = broker.simulator.get_history(all_ids[0], limit=limit)
        if not ref_history:
            return {"range": time_range, "count": 0, "data": []}

        # Gather all turbines' histories
        all_histories = {}
        for tid in all_ids:
            all_histories[tid] = broker.simulator.get_history(tid, limit=limit)

        # Build aggregated series with downsampling
        ref_len = len(ref_history)
        step = max(1, ref_len // points)
        series = []
        for i in range(0, ref_len, step):
            ts = ref_history[i].get("timestamp", "")
            total_power = 0.0
            total_wind = 0.0
            count = 0
            for tid in all_ids:
                h = all_histories.get(tid, [])
                if i < len(h):
                    scada = h[i].get("scada", {})
                    pw = scada.get("WTUR_TotPwrAt")
                    ws = scada.get("WMET_WSpeedNac")
                    if pw is not None:
                        total_power += pw / 1_000_000  # W -> MW
                    if ws is not None:
                        total_wind += ws
                    count += 1
            series.append({
                "timestamp": ts,
                "totalPower": round(total_power, 2),
                "avgWindSpeed": round(total_wind / max(count, 1), 1),
            })

        return {"range": time_range, "count": len(series), "data": series}

    # Longer ranges: query SQLite with downsampling
    storage = broker.storage
    now = datetime.now()
    start = (now - timedelta(seconds=seconds)).isoformat()
    end = now.isoformat()

    conn = storage._get_conn()
    bucket_seconds = max(seconds // points, 1)

    rows = conn.execute("""
        SELECT
            MIN(timestamp) as bucket_time,
            SUM(power_output) as total_power,
            AVG(wind_speed) as avg_wind
        FROM turbine_data
        WHERE timestamp >= ? AND timestamp <= ?
        GROUP BY
            CAST(strftime('%%s', timestamp) AS INTEGER) / ?
        ORDER BY bucket_time ASC
        LIMIT ?
    """, (start, end, bucket_seconds, points)).fetchall()

    series = []
    for row in rows:
        d = dict(row)
        series.append({
            "timestamp": d["bucket_time"],
            "totalPower": round(d["total_power"] or 0, 2),
            "avgWindSpeed": round(d["avg_wind"] or 0, 1),
        })

    return {"range": time_range, "count": len(series), "data": series}


@router.get("/{turbine_id}", response_model=TurbineReading)
async def get_turbine(turbine_id: str):
    """Get single turbine current data."""
    reading = get_broker().get_turbine(turbine_id)
    if not reading:
        raise HTTPException(status_code=404, detail=f"Turbine {turbine_id} not found")
    return reading


@router.get("/{turbine_id}/history")
async def get_turbine_history(
    turbine_id: str,
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    limit: int = Query(500, ge=1, le=10000),
):
    """Get turbine historical data (from SQLite)."""
    broker = get_broker()
    rows = broker.get_history(turbine_id, start, end, limit)
    events = broker.get_history_events(turbine_id, start, end, min(limit, 1000))
    return {"turbineId": turbine_id, "count": len(rows), "data": rows, "events": events}


@router.get("/{turbine_id}/trend")
async def get_turbine_trend(
    turbine_id: str,
    tags: str = Query("WTUR_TotPwrAt,WMET_WSpeedNac", description="Comma-separated SCADA tag IDs"),
    limit: int = Query(120, ge=1, le=3600, description="Max data points"),
):
    """Get in-memory trend data for specific SCADA tags.

    Returns time-series arrays for each requested tag from the simulator's
    in-memory history buffer (up to 3600 points at 1Hz = 1 hour).
    Ideal for real-time trend charts.

    Example: /api/turbines/WT001/trend?tags=WTUR_TotPwrAt,WGEN_GnBrgTmp1,WNAC_VibMsNacXDir&limit=120
    """
    b = get_broker()
    if not b.simulator:
        raise HTTPException(400, "Simulator not running")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    history = b.simulator.get_history(turbine_id, limit=limit)

    if not history:
        raise HTTPException(404, f"No history for {turbine_id}")

    # Build time-series: [{timestamp, tag1, tag2, ...}, ...]
    series = []
    for point in history:
        scada = point.get("scada", {})
        ts = point.get("timestamp", "")
        entry = {"timestamp": ts}
        for tag in tag_list:
            entry[tag] = scada.get(tag)
        series.append(entry)

    return {
        "turbineId": turbine_id,
        "tags": tag_list,
        "count": len(series),
        "data": series,
    }
