from typing import Tuple, Mapping
from fastapi import HTTPException


ALLOWED_FILTERS = {"city", "state", "zip", "label"}

def parse_filters(qp: Mapping[str, str]) -> list[Tuple[str, str, str]]:
    """
    Accepts filter.<field>=$op:value
    e.g. filter.zip=$eq:92830  filter.city=$ilike:full
    Supported ops: $eq, $ne, $in, $nin, $ilike
    """
    OP_MAP = {"$eq", "$ne", "$in", "$nin", "$ilike"}
    triples: list[Tuple[str, str, str]] = []
    for key, val in qp.multi_items():
        if not key.startswith("filter."):
            continue
        field = key.split(".", 1)[1]
        if field not in ALLOWED_FILTERS:
            raise HTTPException(400, detail=f"Unsupported filter field: {field}")
        op, value = ("$eq", val)
        if ":" in val:
            op, value = val.split(":", 1)
        op = op.strip()
        if op not in OP_MAP:
            raise HTTPException(400, detail=f"Unsupported operator {op}")
        triples.append((field, op, value.strip()))
    return triples