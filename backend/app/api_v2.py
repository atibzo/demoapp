from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict
from .models_v2 import SessionStatusV2, PlanRowV2, AnalyzeResponseV2, Policy
from .engine_v2 import plan, analyze, load_policy, save_policy, session_status

router = APIRouter()

@router.get("/session", response_model=SessionStatusV2)
def get_session() -> Dict:
    return session_status()

@router.get("/plan", response_model=List[PlanRowV2])
def get_plan(top: int = Query(10, ge=1, le=100)) -> List[Dict]:
    rows, _meta = plan(top_n=top)
    return rows

@router.get("/analyze", response_model=AnalyzeResponseV2)
def get_analyze(symbol: str) -> Dict:
    if not symbol:
        raise HTTPException(400, "symbol required")
    return analyze(symbol)

@router.get("/policy", response_model=Policy)
def get_policy() -> Dict:
    body, rev = load_policy()
    return {"rev": rev, "body": body}

@router.post("/policy", response_model=Policy)
def post_policy(new_policy: Dict) -> Dict:
    rev = save_policy(new_policy)
    body, _ = load_policy()
    return {"rev": rev, "body": body}
