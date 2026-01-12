import json
import calendar
import re  # Added for finding JSON inside text
from typing import List, Dict, Any
import ollama

# --- CONFIGURATION ---
MODEL_NAME = "gemma3:12b"


class ConstraintAgent:
    def parse_constraints(self, user_text: str, year: int, month: int, employee_names: List[str]) -> List[
        Dict[str, Any]]:

        num_days = calendar.monthrange(year, month)[1]

        # PROMPT: Explicitly asking for NO text, just JSON
        prompt = f"""
        You are a strict data extraction tool.
        CONTEXT: Year {year}, Month {month}. Valid dates: 1 to {num_days}.
        VALID EMPLOYEES: {", ".join(employee_names)}.

        TASK: Extract constraints from this text: "{user_text}"

        OUTPUT RULES:
        1. Return ONLY a JSON array. Do not write "Here is the JSON" or any markdown.
        2. Schema: [{{"employee_name": "Name", "day": int, "shift": 0}}] 
           (0=Morning, 1=Night, null=All Day).
        3. If "Sunday", find all Sundays in {month}/{year}.
        4. If "14th to 16th", output days 14, 15, 16.
        """

        try:
            # 1. Call Ollama
            response = ollama.chat(model=MODEL_NAME, messages=[
                {'role': 'user', 'content': prompt}
            ])

            raw_content = response['message']['content']
            print(f"DEBUG - Raw AI Output: {raw_content}")  # Check your terminal to see what it actually said!

            # 2. CLEANUP: Extract JSON from Markdown or Text
            # This regex looks for anything between '[' and ']'
            match = re.search(r'\[.*\]', raw_content, re.DOTALL)

            if match:
                json_str = match.group(0)
            else:
                # If no brackets found, maybe it's just one object? Try wrapping it.
                json_str = raw_content if raw_content.strip().startswith('[') else f"[{raw_content}]"

            # 3. Parse & Validate
            parsed = json.loads(json_str)

            valid_constraints = []
            if isinstance(parsed, list):
                for item in parsed:
                    # Double check the AI didn't invent names or dates
                    if item.get("employee_name") in employee_names and 1 <= item.get("day", 0) <= num_days:
                        valid_constraints.append(item)

            return valid_constraints

        except Exception as e:
            print(f"Error Parsing: {e}")
            return []


agent = ConstraintAgent()