import csv
import io
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional

router = APIRouter(prefix="/api/export", tags=["export"])


def get_broker():
    from server.app import broker
    return broker


# SCADA tag IDs for flattened CSV export (same order as scada_registry)
SCADA_CSV_COLUMNS = [
    "WTUR_TurSt", "WTUR_TotPwrAt",
    "WGEN_GnPwrMs", "WGEN_GnSpd", "WGEN_GnVtgMs", "WGEN_GnCurMs",
    "WGEN_GnStaTmp1", "WGEN_GnAirTmp1", "WGEN_GnBrgTmp1",
    "WROT_RotSpd", "WROT_PtAngValBl1", "WROT_PtAngValBl2", "WROT_PtAngValBl3",
    "WROT_RotTmp", "WROT_RotCabTmp", "WROT_LckngPnPos", "WROT_RotLckd", "WROT_SrvcBrkAct",
    "WCNV_CnvCabinTmp", "WCNV_CnvDClVtg", "WCNV_CnvGdPwrAt", "WCNV_CnvGnFrq",
    "WCNV_CnvGnPwr", "WCNV_IGCTWtrCond", "WCNV_IGCTWtrPres1", "WCNV_IGCTWtrPres2", "WCNV_IGCTWtrTmp",
    "WGDC_TrfCoreTmp",
    "WMET_WSpeedNac", "WMET_WDirAbs", "WMET_TmpOutside",
    "WNAC_NacTmp", "WNAC_NacCabTmp", "WNAC_VibMsNacXDir", "WNAC_VibMsNacYDir",
    "WYAW_YwVn1AlgnAvg5s", "WYAW_YwBrkHyPrs", "WYAW_CabWup",
    "WSRV_SrvOn", "MBUS_Contact2",
]


@router.get("/snapshot")
async def export_snapshot():
    """Export current state of all turbines (JSON with full SCADA tags)."""
    turbines = get_broker().get_all_turbines()
    return {
        "count": len(turbines),
        "data": [t.model_dump() for t in turbines],
    }


@router.get("/history")
async def export_history(
    turbine_id: str = Query(..., description="Turbine ID (e.g. WT001)"),
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    limit: int = Query(5000, ge=1, le=50000),
    format: str = Query("json", description="json or csv"),
):
    """Export historical data as JSON or CSV.

    CSV format flattens all 40 SCADA tags into individual columns,
    ready for analysis in Excel, Python pandas, or R.
    """
    rows = get_broker().get_history(turbine_id, start, end, limit)

    if format == "csv":
        return _export_csv(turbine_id, rows)

    # JSON: include expanded scada dict
    return {"turbineId": turbine_id, "count": len(rows), "data": rows}


def _export_csv(turbine_id: str, rows: list) -> StreamingResponse:
    """Generate flattened CSV with SCADA tags as individual columns."""
    if not rows:
        return StreamingResponse(
            io.StringIO("No data\n"),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={turbine_id}_history.csv"},
        )

    # Core columns + all SCADA tags as separate columns
    core_cols = ["timestamp", "turbine_id", "status", "tur_state"]
    all_cols = core_cols + SCADA_CSV_COLUMNS

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(all_cols)

    for row in rows:
        # Parse scada_json or scada dict
        scada = row.get("scada", {})
        if not scada and row.get("scada_json"):
            try:
                scada = json.loads(row["scada_json"])
            except (json.JSONDecodeError, TypeError):
                scada = {}

        csv_row = [
            row.get("timestamp", ""),
            row.get("turbine_id", ""),
            row.get("status", ""),
            row.get("tur_state", ""),
        ]
        for tag in SCADA_CSV_COLUMNS:
            val = scada.get(tag, "")
            csv_row.append(val)

        writer.writerow(csv_row)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={turbine_id}_scada_history.csv"},
    )
