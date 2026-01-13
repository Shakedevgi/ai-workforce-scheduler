import json
import calendar
import re
from datetime import date
from typing import List, Dict, Any
import ollama

# --- CONFIGURATION ---
MODEL_NAME = "gemma3:27b"  # Or "llama3", whatever you have installed


class ConstraintAgent:
    def parse_constraints(self, user_text: str, year: int, month: int, employee_names: List[str]) -> List[
        Dict[str, Any]]:

        # 1. BUILD THE CHEAT SHEET (Crucial Step!)
        # We calculate exactly which days correspond to which weekdays.
        cal_obj = calendar.monthcalendar(year, month)
        num_days = calendar.monthrange(year, month)[1]

        weekdays_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday",
                        6: "Sunday"}
        weekday_cheat_sheet = []

        for d in range(1, num_days + 1):
            wd_index = date(year, month, d).weekday()
            wd_name = weekdays_map[wd_index]
            # specific format to help the AI: "Day 1 is Sunday", "Day 2 is Monday"...
            # To save tokens, we can group them: "Sundays: 1, 8, 15..."
            pass

            # Let's make a grouped cheat sheet
        sundays = [d for d in range(1, num_days + 1) if date(year, month, d).weekday() == 6]
        mondays = [d for d in range(1, num_days + 1) if date(year, month, d).weekday() == 0]
        thursdays = [d for d in range(1, num_days + 1) if date(year, month, d).weekday() == 3]
        fridays = [d for d in range(1, num_days + 1) if date(year, month, d).weekday() == 4]

        cheat_sheet_text = f"""
        CALENDAR CHEAT SHEET for {month}/{year}:
        - Total Days: {num_days}
        - Sundays are days: {sundays}
        - Mondays are days: {mondays}
        - Thursdays are days: {thursdays}
        - Fridays are days: {fridays}
        """

        # 2. BUILD THE PROMPT
        # We use "Few-Shot" prompting (giving it examples) to teach it logic.
        prompt = f"""
        You are an expert Scheduling Assistant. 
        Your goal is to convert Natural Language constraints into a JSON array.

        CONTEXT:
        {cheat_sheet_text}
        VALID EMPLOYEES: {", ".join(employee_names)}

        RULES:
        1. Output ONLY a valid JSON array. No text, no markdown.
        2. Schema: {{ "employee_name": "Name", "day": int, "shift": 0 (Morning) | 1 (Night) | null (All Day) }}
        3. SHIFT LOGIC:
           - "Morning" -> shift 0
           - "Night" / "Evening" -> shift 1
           - "All day" / "Can't work" -> shift null
           - "Sunday Night to Wednesday Night" -> Means: Sunday(Night) + Mon(All) + Tue(All) + Wed(Night).
        4. RECURRING DAYS:
           - If user says "Any Sunday", use the CHEAT SHEET to find all Sunday dates.

        EXAMPLES:
        User: "Lior cannot work on the 5th."
        JSON: [{{ "employee_name": "Lior", "day": 5, "shift": null }}]

        User: "Shaked cannot work Sunday mornings." (Assuming Sundays are 2, 9...)
        JSON: [
            {{ "employee_name": "Shaked", "day": 2, "shift": 0 }},
            {{ "employee_name": "Shaked", "day": 9, "shift": 0 }}
        ]

        TASK:
        User Input: "{user_text}"

        JSON Output:
        """

        try:
            # 3. CALL OLLAMA
            response = ollama.chat(model=MODEL_NAME, messages=[
                {'role': 'user', 'content': prompt}
            ])

            raw_content = response['message']['content']

            # 4. CLEANUP (Find JSON inside text)
            # Find the first '[' and the last ']'
            match = re.search(r'\[.*\]', raw_content, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                # Fallback if it didn't use brackets
                json_str = raw_content if raw_content.strip().startswith('[') else "[]"

            parsed = json.loads(json_str)

            # 5. VALIDATION
            valid_constraints = []
            if isinstance(parsed, list):
                for item in parsed:
                    # Validate logic
                    if item.get("employee_name") in employee_names and 1 <= item.get("day", 0) <= num_days:
                        valid_constraints.append(item)

            return valid_constraints

        except Exception as e:
            print(f"Parsing Error: {e}")
            return []


agent = ConstraintAgent()