import json
import copy
from typing import Dict, Any
from .api_client import SchedulerAPIClient
from .prompts import SYSTEM_PROMPT


class WorkforceAgent:
    def __init__(self, api_client: SchedulerAPIClient, current_context: Dict[str, Any]):
        self.client = api_client
        # Stores the current state of the schedule configuration (inputs)
        self.context = current_context
        self.latest_result = None

    def run(self, user_query: str) -> str:
        """
        Main entry point.
        1. Asks LLM to modify JSON based on query.
        2. Calls API if needed.
        3. Returns natural language explanation.
        """

        # 1. LLM Interaction (Simulated for this codebase)
        # In real life: response = call_llm(system=SYSTEM_PROMPT, user=user_query, context=self.context)
        llm_decision = self._mock_llm_call(user_query)

        # 2. Action Execution
        if llm_decision["intent"] == "CHANGE":
            new_payload = llm_decision["new_request_json"]

            # Call API
            api_result = self.client.get_schedule(new_payload)

            if "error" in api_result:
                return f"I tried to update the schedule, but the solver failed: {api_result['error']}"

            # Update State
            self.context = new_payload
            self.latest_result = api_result

            # 3. Final Explanation (In real life, feed result back to LLM for summary)
            return self._generate_explanation(llm_decision["thought"], api_result)

        elif llm_decision["intent"] == "QUESTION":
            # Just look at self.latest_result and answer
            return "Based on the current schedule... (Logic to read self.latest_result would go here)"

        return "I didn't understand that request."

    def _mock_llm_call(self, query: str) -> Dict[str, Any]:
        """
        SIMULATOR: determining intent and JSON modifications.
        This represents what GPT-4 would return.
        """
        query_lower = query.lower()

        # Scenario A: Adding a constraint
        if "sick" in query_lower or "unavailable" in query_lower:
            # logic to parse "Day 12" and "Shaked" (Simulated Intelligence)
            new_context = copy.deepcopy(self.context)

            # Hardcoded simulation of LLM extracting entities for the example
            if "shaked" in query_lower and "12" in query_lower:
                new_context["constraints"].append({
                    "employee_name": "Shaked",
                    "day": 12,
                    "shift": None
                })

            return {
                "thought": "User wants to mark Shaked unavailable on the 12th. I will add a constraint.",
                "intent": "CHANGE",
                "new_request_json": new_context,
                "explanation_required": True
            }

        # Scenario B: Adjusting Weights
        if "balance" in query_lower and "better" in query_lower:
            new_context = copy.deepcopy(self.context)
            new_context["config"]["weight_balance"] = 50  # Increase weight

            return {
                "thought": "User wants better balance. I will increase the 'weight_balance' parameter.",
                "intent": "CHANGE",
                "new_request_json": new_context,
                "explanation_required": True
            }

        return {"intent": "UNKNOWN", "new_request_json": None}

    def _generate_explanation(self, thought: str, result: Dict) -> str:
        """
        Simple generator to describe the outcome.
        """
        status = result["metadata"]["status"]
        obj_val = result["metadata"]["objective_value"]

        if status == "OPTIMAL" or status == "FEASIBLE":
            return f"✅ Done. {thought}\n\nSolver Status: {status}. Optimization Score: {obj_val}.\nThe schedule has been updated to reflect your request."
        else:
            return f"⚠️ I tried to update the schedule, but it became impossible (Status: {status}). Please relax some constraints."