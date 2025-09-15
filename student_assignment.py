import pandas as pd
import random
from collections import defaultdict

# ---------------- CONFIG ---------------- #
GROUP_SIZE = 4
MAX_SAME_NATIONALITY = 2
PREF_COLUMNS = ["Pref1","Pref2","Pref3","Pref4","Pref5"]
ENFORCE_TYPE_IN_PREF_ROUNDS = True  # hard constraint in preference rounds
SEED = 42
random.seed(SEED)

# ---------------- LOAD DATA ---------------- #
students = pd.read_csv("student_preferences.csv")
projects = pd.read_csv("projects.csv")

proj_type = dict(zip(projects["Project"], projects["Type"]))
proj_capacity = dict(zip(projects["Project"], projects["Capacity"]))

assignments = defaultdict(list)
student_row = {row["Name"]: row for _, row in students.iterrows()}
student_assigned = {row["Name"]: None for _, row in students.iterrows()}

# ---------------- HELPERS ---------------- #
def nationality_ok(project, nat):
    current_nats = [student_row[s]["Nationality"] for s in assignments[project]]
    return current_nats.count(nat) < MAX_SAME_NATIONALITY

def capacity_ok(project):
    return len(assignments[project]) < proj_capacity[project]

def type_matches(student, project):
    return student["CompanyPreference"] == proj_type[project]

def can_assign(student, project, enforce_type: bool):
    if not capacity_ok(project):
        return False
    if not nationality_ok(project, student["Nationality"]):
        return False
    if enforce_type and not type_matches(student, project):
        return False
    return True

# ---------------- ASSIGNMENT ---------------- #
# Shuffle students for fairness, reproducible by seed
student_names = list(students["Name"])
random.shuffle(student_names)

# Step 1: preference-based assignment
for pref in PREF_COLUMNS:
    for name in student_names:
        if student_assigned[name] is not None:
            continue
        s = student_row[name]
        project = s[pref]
        if can_assign(s, project, enforce_type=ENFORCE_TYPE_IN_PREF_ROUNDS):
            assignments[project].append(name)
            student_assigned[name] = project

# Step 2: type-enforced leftovers
leftovers = [n for n, p in student_assigned.items() if p is None]
for name in leftovers:
    s = student_row[name]
    valid_projects = [p for p in projects["Project"]
                      if can_assign(s, p, enforce_type=True)]
    if valid_projects:
        chosen = random.choice(valid_projects)
        assignments[chosen].append(name)
        student_assigned[name] = chosen

# Step 3: relax type if still unassigned
leftovers = [n for n, p in student_assigned.items() if p is None]
for name in leftovers:
    s = student_row[name]
    valid_projects = [p for p in projects["Project"]
                      if can_assign(s, p, enforce_type=False)]
    if valid_projects:
        chosen = random.choice(valid_projects)
        assignments[chosen].append(name)
        student_assigned[name] = chosen

# Step 4: relax nationality if still unassigned
leftovers = [n for n, p in student_assigned.items() if p is None]
for name in leftovers:
    s = student_row[name]
    valid_projects = [p for p in projects["Project"] if capacity_ok(p)]
    if valid_projects:
        chosen = random.choice(valid_projects)
        assignments[chosen].append(name)
        student_assigned[name] = chosen

# ---------------- OUTPUT ---------------- #
records = []
for project, members in assignments.items():
    for m in members:
        s = student_row[m]
        rank = None
        for i, pref in enumerate(PREF_COLUMNS, start=1):
            if s[pref] == project:
                rank = i
                break
        records.append({
            "Student": m,
            "AssignedProject": project,
            "ProjectType": proj_type[project],
            "StudentTypePreference": s["CompanyPreference"],
            "TypeMatched": s["CompanyPreference"] == proj_type[project],
            "Nationality": s["Nationality"],
            "PreferenceRank": rank if rank is not None else 999
        })

assigned_df = pd.DataFrame(records)
assigned_df.sort_values(by=["AssignedProject","PreferenceRank","Student"], inplace=True)
assigned_df.to_csv("assigned_teams.csv", index=False)

# Summary outputs
project_nat_summary = (assigned_df
    .groupby(["AssignedProject","Nationality"])
    .size()
    .reset_index(name="Count"))

project_type_match = (assigned_df
    .groupby("AssignedProject")["TypeMatched"]
    .mean()
    .reset_index(name="TypeMatchRate"))

pref_satisfaction = assigned_df["PreferenceRank"].value_counts().sort_index()
pref_satisfaction = pref_satisfaction.rename_axis("PreferenceRank").reset_index(name="NumStudents")

# Save summaries into one CSV
with open("assignment_summary.csv", "w", encoding="utf-8") as f:
    f.write("# Type match rate by project\n")
    project_type_match.to_csv(f, index=False)
    f.write("\n# Nationality distribution by project\n")
    project_nat_summary.to_csv(f, index=False)
    f.write("\n# Preference satisfaction distribution\n")
    pref_satisfaction.to_csv(f, index=False)

print("Assignments saved to assigned_teams.csv")
print("Summary saved to assignment_summary.csv")
