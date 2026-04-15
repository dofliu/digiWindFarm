import csv
import io
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional

router = APIRouter(prefix="/api/export", tags=["export"])


def get_broker():
    """Return the shared DataBroker instance from the main app module."""
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
    "WCNV_ReactPwr", "WCNV_PwrFactor", "WCNV_AppPwr",
    "WCNV_FreqWattDerate", "WCNV_InertiaPwr", "WCNV_CnvMode", "WCNV_RtBand",
    "WGDC_TrfCoreTmp",
    "WMET_WSpeedNac", "WMET_WDirAbs", "WMET_TmpOutside",
    "WNAC_NacTmp", "WNAC_NacCabTmp", "WNAC_VibMsNacXDir", "WNAC_VibMsNacYDir",
    "WYAW_YwVn1AlgnAvg5s", "WYAW_YwBrkHyPrs", "WYAW_CabWup",
    "WVIB_Band1pX", "WVIB_Band1pY", "WVIB_Band3pX", "WVIB_Band3pY",
    "WVIB_BandGearX", "WVIB_BandGearY", "WVIB_BandHfX", "WVIB_BandHfY",
    "WVIB_BandBbX", "WVIB_BandBbY", "WVIB_CrestFactor", "WVIB_Kurtosis",
    "WLOD_TwrFaMom", "WLOD_TwrSsMom", "WLOD_BldFlapMom", "WLOD_BldEdgeMom",
    "WLOD_DelTwrFa", "WLOD_DelTwrSs", "WLOD_DelBldFlap", "WLOD_DelBldEdge",
    "WLOD_DmgTwrFa", "WLOD_DmgTwrSs", "WLOD_DmgBldFlap", "WLOD_DmgBldEdge",
    "WLOD_ProdHours",
    "WSRV_SrvOn", "MBUS_Contact2",
]

# Event severity mapping for grouping
EVENT_SEVERITY = {
    "fault": "critical",
    "fault_lifecycle": "warning",
    "grid": "warning",
    "operator": "info",
    "state": "info",
    "wind": "info",
    "config": "info",
}


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


@router.get("/events")
async def export_events(
    turbine_id: Optional[str] = Query(None, description="Turbine ID filter"),
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(5000, ge=1, le=50000),
    format: str = Query("json", description="json or csv"),
):
    """Export history events as JSON or CSV with severity grouping.

    Supports filtering by turbine_id, time range, and event_type.
    Each event includes a severity level derived from event_type.
    """
    broker = get_broker()
    events = broker.get_history_events(turbine_id, start, end, limit)

    # Apply event_type filter if specified
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    # Add severity grouping to each event
    for ev in events:
        et = ev.get("event_type", "")
        ev["severity"] = EVENT_SEVERITY.get(et, "info")
        # Upgrade severity for trip events
        if et == "fault" and ev.get("title", "").lower().startswith("automatic fault trip"):
            ev["severity"] = "critical"
        elif et == "fault_lifecycle":
            payload = ev.get("payload", {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, TypeError):
                    payload = {}
            phase = payload.get("toPhase") or payload.get("phase", "")
            if phase in ("critical", "advanced"):
                ev["severity"] = "critical"
            elif phase == "developing":
                ev["severity"] = "warning"
            else:
                ev["severity"] = "info"

    if format == "csv":
        return _export_events_csv(events)

    return {
        "count": len(events),
        "data": events,
        "severity_summary": _severity_summary(events),
    }


def _severity_summary(events: list) -> dict:
    """Count events by severity level."""
    summary = {"critical": 0, "warning": 0, "info": 0}
    for ev in events:
        sev = ev.get("severity", "info")
        summary[sev] = summary.get(sev, 0) + 1
    return summary


def _export_events_csv(events: list) -> StreamingResponse:
    """Export events as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    cols = ["timestamp", "end_timestamp", "turbine_id", "event_type",
            "severity", "source", "title", "detail"]
    writer.writerow(cols)
    for ev in events:
        writer.writerow([
            ev.get("timestamp", ""),
            ev.get("end_timestamp", ""),
            ev.get("turbine_id", ""),
            ev.get("event_type", ""),
            ev.get("severity", ""),
            ev.get("source", ""),
            ev.get("title", ""),
            ev.get("detail", ""),
        ])
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=events_export.csv"},
    )


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
