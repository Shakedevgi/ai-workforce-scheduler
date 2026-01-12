from fastapi import FastAPI, HTTPException
from models import ScheduleRequest, ScheduleResponse
from core import WorkforceSchedulerEngine
import uvicorn

app = FastAPI(title="Workforce Scheduler API", version="1.0.0")


@app.post("/schedule", response_model=ScheduleResponse)
async def generate_schedule(request: ScheduleRequest):
    """
    Generates a monthly schedule based on employee constraints and AI-injected rules.
    """
    try:
        # 1. Initialize Engine with Request Data
        engine = WorkforceSchedulerEngine(request)

        # 2. Run Optimization
        result = engine.solve()

        # 3. Check for specific failure cases (optional logic)
        if result.metadata.status not in ["OPTIMAL", "FEASIBLE"]:
            # In a real system, you might want to return a 422 here,
            # but returning the metadata allows the AI to see 'INFEASIBLE'
            pass

        return result

    except Exception as e:
        # Catch unexpected errors (e.g., date errors, internal logic bugs)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)