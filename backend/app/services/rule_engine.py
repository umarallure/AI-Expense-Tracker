from typing import List, Dict, Any, Optional
from app.db.supabase import get_supabase_client
from app.schemas.rule import Rule, RuleCreate, RuleUpdate
from supabase import Client
import json

class RuleEngine:
    def __init__(self):
        self.supabase: Client = get_supabase_client()

    async def create_rule(self, rule_data: RuleCreate) -> Rule:
        """Create a new rule in the database"""
        rule_dict = rule_data.model_dump()
        # Convert conditions and actions to JSON strings for storage
        rule_dict['conditions'] = json.dumps([cond.model_dump() for cond in rule_data.conditions])
        rule_dict['actions'] = json.dumps([action.model_dump() for action in rule_data.actions])

        response = self.supabase.table("rules").insert(rule_dict).execute()

        if not response.data:
            raise Exception("Failed to create rule")

        # Convert back to proper format
        rule_data = response.data[0]
        rule_data['conditions'] = json.loads(rule_data['conditions'])
        rule_data['actions'] = json.loads(rule_data['actions'])

        return Rule(**rule_data)

    async def get_all_rules(self, business_id: Optional[str] = None) -> List[Rule]:
        """Get all rules, optionally filtered by business"""
        query = self.supabase.table("rules").select("*")

        if business_id:
            query = query.eq("business_id", business_id)

        query = query.order("priority", desc=True).order("created_at", desc=True)

        response = query.execute()

        rules = []
        for rule_data in response.data:
            # Parse JSON strings back to objects
            rule_data['conditions'] = json.loads(rule_data['conditions'])
            rule_data['actions'] = json.loads(rule_data['actions'])
            rules.append(Rule(**rule_data))

        return rules

    async def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID"""
        response = self.supabase.table("rules").select("*").eq("id", rule_id).single().execute()

        if not response.data:
            return None

        rule_data = response.data
        rule_data['conditions'] = json.loads(rule_data['conditions'])
        rule_data['actions'] = json.loads(rule_data['actions'])

        return Rule(**rule_data)

    async def update_rule(self, rule_id: str, rule_data: RuleUpdate) -> Optional[Rule]:
        """Update an existing rule"""
        update_dict = rule_data.model_dump(exclude_unset=True)

        if not update_dict:
            return None

        # Convert conditions and actions to JSON if present
        if 'conditions' in update_dict:
            update_dict['conditions'] = json.dumps([cond.model_dump() for cond in rule_data.conditions])
        if 'actions' in update_dict:
            update_dict['actions'] = json.dumps([action.model_dump() for action in rule_data.actions])

        response = self.supabase.table("rules").update(update_dict).eq("id", rule_id).execute()

        if not response.data:
            return None

        # Convert back to proper format
        rule_data = response.data[0]
        rule_data['conditions'] = json.loads(rule_data['conditions'])
        rule_data['actions'] = json.loads(rule_data['actions'])

        return Rule(**rule_data)

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        response = self.supabase.table("rules").delete().eq("id", rule_id).execute()
        return len(response.data) > 0

    def evaluate_conditions(self, transaction: Dict[str, Any], conditions: List[Dict[str, Any]]) -> bool:
        """Evaluate if transaction matches all rule conditions"""
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = condition['value']

            transaction_value = transaction.get(field)

            if not self._check_condition(transaction_value, operator, value):
                return False
        return True

    def _check_condition(self, transaction_value: Any, operator: str, rule_value: Any) -> bool:
        """Check a single condition"""
        if operator == "equals":
            return transaction_value == rule_value
        elif operator == "not_equals":
            return transaction_value != rule_value
        elif operator == "contains":
            return str(rule_value).lower() in str(transaction_value).lower()
        elif operator == "greater_than":
            try:
                return float(transaction_value) > float(rule_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(transaction_value) < float(rule_value)
            except (ValueError, TypeError):
                return False
        elif operator == "starts_with":
            return str(transaction_value).startswith(str(rule_value))
        elif operator == "ends_with":
            return str(transaction_value).endswith(str(rule_value))
        return False

    def execute_actions(self, transaction: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute rule actions on a transaction"""
        for action in actions:
            action_type = action['type']
            value = action['value']

            if action_type == "set_category":
                transaction["category_id"] = value
            elif action_type == "add_tag":
                if "tags" not in transaction:
                    transaction["tags"] = []
                transaction["tags"].append(value)
            elif action_type == "require_approval":
                transaction["requires_approval"] = True
            elif action_type == "flag_suspicious":
                transaction["is_suspicious"] = True

        return transaction

    async def apply_rules(self, transaction: Dict[str, Any], business_id: str) -> Dict[str, Any]:
        """Apply all active rules for a business to a transaction"""
        rules = await self.get_all_rules(business_id)
        active_rules = [rule for rule in rules if rule.is_active]

        for rule in active_rules:
            if self.evaluate_conditions(transaction, [cond.model_dump() for cond in rule.conditions]):
                transaction = self.execute_actions(transaction, [action.model_dump() for action in rule.actions])

        return transaction