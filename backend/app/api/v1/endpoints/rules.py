from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.rule import RuleCreate, RuleUpdate, Rule
from app.services.rule_engine import RuleEngine

router = APIRouter()
rule_engine = RuleEngine()

@router.post("/", response_model=Rule)
async def create_rule(rule: RuleCreate):
    return await rule_engine.create_rule(rule)

@router.get("/", response_model=List[Rule])
async def get_rules():
    return await rule_engine.get_all_rules()

@router.get("/{rule_id}", response_model=Rule)
async def get_rule(rule_id: str):
    rule = await rule_engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.put("/{rule_id}", response_model=Rule)
async def update_rule(rule_id: str, rule: RuleUpdate):
    updated_rule = await rule_engine.update_rule(rule_id, rule)
    if not updated_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return updated_rule

@router.delete("/{rule_id}", response_model=dict)
async def delete_rule(rule_id: str):
    success = await rule_engine.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"detail": "Rule deleted successfully"}