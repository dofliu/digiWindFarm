import csv
import io
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional

router = APIRouter(prefix="/api/export", tags=["export"])


def get_broker():
    from server.app import broker
    return broker


@router.get("/snapshot")
async def export_snapshot():
    """Export current state of all turbines."""
    turbines = get_broker().get_all_turbines()
    return {
        "count": len(turbines),
        "data": [t.model_dump() for t in turbines],
    }


@router.get("/history")
async def export_history(
    turbine_id: str = Query(..., description="Turbine ID"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    limit: int = Query(5000, ge=1, le=50000),
    format: str = Query("json", description="json or csv"),
):
    """Export historical data as JSON or CSV."""
    rows = get_broker().get_history(turbine_id, start, end, limit)

    if format == "csv":
        if not rows:
            return StreamingResponse(
                io.StringIO("No data\n"),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={turbine_id}_history.csv"},
            )

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={turbine_id}_history.csv"},
        )

    return {"turbineId": turbine_id, "count": len(rows), "data": rows}
