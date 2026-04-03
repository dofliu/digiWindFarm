"""i18n API — SCADA tag labels in multiple languages."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/i18n", tags=["i18n"])


@router.get("/tags")
async def get_tag_labels(lang: str = "en"):
    """Get SCADA tag labels in the specified language (en, zh)."""
    from simulator.physics import SCADA_REGISTRY
    return SCADA_REGISTRY.labels(lang)


@router.get("/tags/all")
async def get_all_tag_labels():
    """Get full i18n dict: {tag_id: {en: ..., zh: ...}}."""
    from simulator.physics import SCADA_REGISTRY
    return SCADA_REGISTRY.to_i18n_dict()


@router.get("/tags/registry")
async def get_tag_registry():
    """Get full tag registry with OPC tags, Modbus addresses, units, and ranges."""
    from simulator.physics import SCADA_REGISTRY
    return [
        {
            "id": t.id,
            "opc_tag": t.opc_tag,
            "subsystem": t.subsystem,
            "data_type": t.data_type,
            "unit": t.unit,
            "label_en": t.label_en,
            "label_zh": t.label_zh,
            "modbus_reg": t.modbus_reg,
            "sim_min": t.sim_min,
            "sim_max": t.sim_max,
        }
        for t in SCADA_REGISTRY.all_tags
    ]
