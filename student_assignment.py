import pandas as pd
import random
from collections import defaultdict, Counter

# -----------------------------
# CONFIG
# -----------------------------
STUDENTS_FILE = "student_preferences.csv"
PROJECTS_FILE = "projects.csv"
ASSIGNED_FILE = "assigned_teams.csv"
SUMMARY_FILE = "team_nationality_summary.csv"

SEED = 42
random.seed(SEED)

# Nationality cap strategy:
FIXED_NATIONALITY_CAP = 2

# -----------------------------
# LOAD INPUT FILES
# -----------------------------
df = pd.read_csv(STUDENTS_FILE)
projects_df = pd.read_csv(PROJECTS_FILE)

if any(col not in projects_df.columns for col in ["Project", "Type", "Capacity"]):
    raise ValueError("projects.csv must have columns: Project, Type, Capacity")

if any(col not in df.columns for col in ["Name", "Nationality", "Pref1", "Pref2", "Pref3", "Pref4", "Pref5", "CompanyPreference"]):
    raise ValueError("student_preferences.csv must have columns: Name, Nationality, Pref1..Pref5, CompanyPreference")

proj_types = dict(zip(projects_df["Project"], projects_df["Type"]))
proj_capacity = dict(zip(projects_df["Project"], projects_df["Capacity"]))
projects = list(proj_types.keys())

if sum(proj_capacity.values()) < len(df):
    raise ValueError("Total capacity is less than number of students.")

# -----------------------------
# HELPERS
# -----------------------------
assignments = defaultdict(list)

def nat_cap_for(project: str) -> int:
    cap = int(proj_capacity[project])
    if FIXED_NATIONALITY_CAP is not None:
        return min(cap, int(FIXED_NATIONALITY_CAP))
    return max(1, cap // 2)

def can_assign(student_row, project, ignore_nationality=False):
    if project not in proj_capacity:
        return False
    if len(assignments[project]) >= proj_capacity[project]:
        return False
    if ignore_nationality:
        return True
    current_nats = df[df["Name"].isin(assignments[project])]["Nationality"].tolist()
    return current_nats.count(student_row["Nationality"]) < nat_cap_for(project)

# -----------------------------
# STEP 1: Preference rounds
# -----------------------------
pref_cols = [f"Pref{i}" for i in range(1,6)]
student_order = df["Name"].tolist()
random.shuffle(student_order)
assigned_set = set()

for pref in pref_cols:
    for name in student_order:
        if name in assigned_set:
            continue
        row = df[df["Name"] == name].iloc[0]
        proj = row[pref]
        if proj not in proj_capacity:
            continue
        if can_assign(row, proj):
            assignments[proj].append(name)
            assigned_set.add(name)

# -----------------------------
# STEP 2: Fallback using CompanyPreference
# -----------------------------
leftovers = [n for n in df["Name"].tolist() if n not in assigned_set]

for name in leftovers:
    row = df[df["Name"] == name].iloc[0]
    pref_type = row["CompanyPreference"]

    feasible = [p for p in projects if can_assign(row, p)]
    feasible_typed = [p for p in feasible if proj_types[p] == pref_type] if pref_type else feasible

    if feasible_typed:
        choice = random.choice(feasible_typed)
    elif feasible:
        choice = random.choice(feasible)
    else:
        relax = [p for p in projects if can_assign(row, p, ignore_nationality=True)]
        if not relax:
            raise RuntimeError("No available project to place student. Increase capacities or review constraints.")
        choice = random.choice(relax)

    assignments[choice].append(name)
    assigned_set.add(name)

# -----------------------------
# STEP 3: Save results
# -----------------------------
rows = []
for project, members in assignments.items():
    for name in members:
        st = df[df["Name"] == name].iloc[0]
        rank = None
        for i in range(1,6):
            if st[f"Pref{i}"] == project:
                rank = i
                break
        rows.append({
            "Project": project,
            "ProjectType": proj_types[project],
            "Capacity": proj_capacity[project],
            "Student": name,
            "Nationality": st["Nationality"],
            "CompanyPreference": st["CompanyPreference"],
            "PreferenceRank": rank if rank is not None else "Fallback"
        })

result_df = pd.DataFrame(rows).sort_values(["Project", "Student"]).reset_index(drop=True)
result_df.to_csv(ASSIGNED_FILE, index=False)

summary = []
for project, members in assignments.items():
    nats = df[df["Name"].isin(members)]["Nationality"].tolist()
    summary.append({
        "Project": project,
        "ProjectType": proj_types[project],
        "Capacity": proj_capacity[project],
        "TeamSize": len(members),
        "RemainingSpots": int(proj_capacity[project]) - len(members),
        "Nationalities": ", ".join(nats)
    })
summary_df = pd.DataFrame(summary).sort_values("Project")
summary_df.to_csv(SUMMARY_FILE, index=False)

print("✅ Assignment complete!")
print(f"Saved {ASSIGNED_FILE}")
print(f"Saved {SUMMARY_FILE}")
