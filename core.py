import calendar
from datetime import date
from ortools.sat.python import cp_model
# Import models from the file above (assuming same directory for this snippet)
from models import ScheduleRequest, ScheduleResponse, ShiftAssignment, EmployeeStats, SolverMetadata


class WorkforceSchedulerEngine:
    def __init__(self, request: ScheduleRequest):
        self.req = request
        self.num_days = calendar.monthrange(request.year, request.month)[1]
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.shifts = {}  # Decision variables
        self.employee_map = {e.name: i for i, e in enumerate(request.employees)}
        self.shabbat_indices = self._calculate_shabbat_indices()

    def _calculate_shabbat_indices(self):
        shabbat_shifts = []
        for day in range(1, self.num_days + 1):
            weekday = date(self.req.year, self.req.month, day).weekday()
            # 4=Friday, 5=Saturday
            if weekday == 4:
                shabbat_shifts.append((day, 1))  # Fri Night
            elif weekday == 5:
                shabbat_shifts.append((day, 0))  # Sat Morn
                shabbat_shifts.append((day, 1))  # Sat Night
        return shabbat_shifts

    def solve(self) -> ScheduleResponse:
        self._build_variables()
        self._add_hard_constraints()
        self._add_dynamic_constraints()
        self._add_objectives()

        # Configure Solver
        self.solver.parameters.max_time_in_seconds = self.req.config.timeout_seconds
        status_val = self.solver.Solve(self.model)
        status_name = self.solver.StatusName(status_val)

        # Logic to map raw solver data to Output Models
        if status_val in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._serialize_solution(status_name)
        else:
            # Return empty structure with failure status
            return ScheduleResponse(
                metadata=SolverMetadata(status=status_name, objective_value=0.0, wall_time=self.solver.WallTime()),
                schedule=[],
                statistics={}
            )

    def _build_variables(self):
        for d in range(1, self.num_days + 1):
            for s in range(2):
                for e_idx in range(len(self.req.employees)):
                    self.shifts[(d, s, e_idx)] = self.model.NewBoolVar(f'd{d}_s{s}_e{e_idx}')

    def _add_hard_constraints(self):
        num_emp = len(self.req.employees)

        # 1. One employee per shift
        for d in range(1, self.num_days + 1):
            for s in range(2):
                self.model.Add(sum(self.shifts[(d, s, e)] for e in range(num_emp)) == 1)

        # 2. Max one shift per day
        for e in range(num_emp):
            for d in range(1, self.num_days + 1):
                self.model.Add(sum(self.shifts[(d, s, e)] for s in range(2)) <= 1)

        # 3. Consecutive constraints (2 Mornings, 2 Nights, 3 Days)
        for e in range(num_emp):
            # Mornings
            for d in range(1, self.num_days - 1):
                self.model.Add(sum(self.shifts[(d + i, 0, e)] for i in range(3)) <= 2)
            # Nights
            for d in range(1, self.num_days - 1):
                self.model.Add(sum(self.shifts[(d + i, 1, e)] for i in range(3)) <= 2)
            # Working days
            is_working = {d: self.model.NewBoolVar(f'w_{d}_{e}') for d in range(1, self.num_days + 1)}
            for d in range(1, self.num_days + 1):
                self.model.Add(sum(self.shifts[(d, s, e)] for s in range(2)) == is_working[d])
            for d in range(1, self.num_days - 2):
                self.model.Add(sum(is_working[d + i] for i in range(4)) <= 3)

        # 4. Monthly Limits & Shabbat
        for e_idx, emp in enumerate(self.req.employees):
            # Total
            all_shifts = [self.shifts[(d, s, e_idx)] for d in range(1, self.num_days + 1) for s in range(2)]
            self.model.Add(sum(all_shifts) <= emp.max_shifts)

            # Shabbat
            shabbat_vars = [self.shifts[(d, s, e_idx)] for (d, s) in self.shabbat_indices]
            self.model.Add(sum(shabbat_vars) >= emp.min_shabbat)
            self.model.Add(sum(shabbat_vars) <= emp.max_shabbat)

            # Shabbat Night Only Logic
            if emp.shabbat_night_only:
                for (d, s) in self.shabbat_indices:
                    # If it's NOT Sat Night (i.e., Fri Night or Sat Morn), forbid it
                    weekday = date(self.req.year, self.req.month, d).weekday()
                    is_sat_night = (weekday == 5 and s == 1)
                    if not is_sat_night:
                        self.model.Add(self.shifts[(d, s, e_idx)] == 0)
        # --- ADD THIS NEW BLOCK ---
        # 5. REST CONSTRAINT: No Morning Shift after a Night Shift
        # Logic: If Employee works Day(d-1) Night, they CANNOT work Day(d) Morning.
        for e in range(num_emp):
            for d in range(2, self.num_days + 1):
                # Sum of (Yesterday Night) + (Today Morning) <= 1
                # If Yesterday Night is 1, Today Morning MUST be 0.
                self.model.Add(
                    self.shifts[(d - 1, 1, e)] + self.shifts[(d, 0, e)] <= 1
                )
    def _add_dynamic_constraints(self):
        for c in self.req.constraints:
            if c.employee_name in self.employee_map and 1 <= c.day <= self.num_days:
                e_idx = self.employee_map[c.employee_name]
                if c.shift is None:
                    self.model.Add(self.shifts[(c.day, 0, e_idx)] == 0)
                    self.model.Add(self.shifts[(c.day, 1, e_idx)] == 0)
                elif c.shift in [0, 1]:
                    self.model.Add(self.shifts[(c.day, c.shift, e_idx)] == 0)

    def _add_objectives(self):
        # We need vars for stats to optimize them
        deficits = []
        imbalances = []

        for e_idx, emp in enumerate(self.req.employees):
            # Deficit
            total_shifts = sum(self.shifts[(d, s, e_idx)] for d in range(1, self.num_days + 1) for s in range(2))
            deficit = self.model.NewIntVar(0, 50, f'def_{e_idx}')
            # Max(0, min_shifts - total)
            self.model.Add(deficit >= emp.min_shifts - total_shifts)
            deficits.append(deficit)

            # Imbalance
            m_count = sum(self.shifts[(d, 0, e_idx)] for d in range(1, self.num_days + 1))
            n_count = sum(self.shifts[(d, 1, e_idx)] for d in range(1, self.num_days + 1))
            diff = self.model.NewIntVar(0, 50, f'diff_{e_idx}')
            self.model.Add(diff >= m_count - n_count)
            self.model.Add(diff >= n_count - m_count)
            imbalances.append(diff)

        # Configurable weights
        w_def = self.req.config.weight_deficit
        w_bal = self.req.config.weight_balance
        self.model.Minimize(sum(deficits) * w_def + sum(imbalances) * w_bal)

    def _serialize_solution(self, status: str) -> ScheduleResponse:
        schedule_list = []
        stats = {e.name: {"total": 0, "m": 0, "n": 0, "s": 0} for e in self.req.employees}

        # Build Schedule List
        for d in range(1, self.num_days + 1):
            m_emp, n_emp = None, None

            # Find who worked
            for e_idx, emp in enumerate(self.req.employees):
                if self.solver.Value(self.shifts[(d, 0, e_idx)]):
                    m_emp = emp.name
                    stats[emp.name]["total"] += 1
                    stats[emp.name]["m"] += 1
                    if (d, 0) in self.shabbat_indices: stats[emp.name]["s"] += 1

                if self.solver.Value(self.shifts[(d, 1, e_idx)]):
                    n_emp = emp.name
                    stats[emp.name]["total"] += 1
                    stats[emp.name]["n"] += 1
                    if (d, 1) in self.shabbat_indices: stats[emp.name]["s"] += 1

            weekday = date(self.req.year, self.req.month, d).weekday()
            is_shabbat_m = (weekday == 5)
            is_shabbat_n = (weekday == 4 or weekday == 5)

            schedule_list.append(ShiftAssignment(
                day=d,
                day_name=calendar.day_name[weekday],
                morning_employee=m_emp,
                night_employee=n_emp,
                is_shabbat_morning=is_shabbat_m,
                is_shabbat_night=is_shabbat_n
            ))

        # Build Stats Dict
        stats_response = {}
        for e in self.req.employees:
            s = stats[e.name]
            stats_response[e.name] = EmployeeStats(
                total_shifts=s["total"],
                morning_shifts=s["m"],
                night_shifts=s["n"],
                shabbat_shifts=s["s"],
                min_shifts_req=e.min_shifts,
                max_shifts_req=e.max_shifts,
                min_shabbat_req=e.min_shabbat,
                max_shabbat_req=e.max_shabbat
            )

        return ScheduleResponse(
            metadata=SolverMetadata(
                status=status,
                objective_value=self.solver.ObjectiveValue(),
                wall_time=self.solver.WallTime()
            ),
            schedule=schedule_list,
            statistics=stats_response
        )