import pandas as pd
import random
from collections import defaultdict

# -----------------------------
# CONFIG
# -----------------------------
STUDENTS_FILE = "student_preferences.csv"
PROJECTS_FILE = "projects.csv"
ASSIGNED_FILE = "assigned_teams.csv"
SUMMARY_FILE = "team_nationality_summary.csv"

SEED = 42
random.seed(SEED)

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv(STUDENTS_FILE)
projects_df = pd.read_csv(PROJECTS_FILE)

proj_types = dict(zip(projects_df["Project"], projects_df["Type"]))
proj_capacity = dict(zip(projects_df["Project"], projects_df["Capacity"]))
projects = list(proj_types.keys())

if sum(proj_capacity.values()) < len(df):
    raise ValueError("⚠️ Total capacity is less than number of students.")

# -----------------------------
# HELPERS
# -----------------------------
def can_assign(student_row, project, assignments):
    """Check if student can join a project (capacity + nationality)."""
    if len(assignments[project]) >= proj_capacity[project]:
        return False
    current_nats = df[df["Name"].isin(assignments[project])]["Nationality"].tolist()
    return current_nats.count(student_row["Nationality"]) < 2  # <= 2 of same nationality

# -----------------------------
# STEP 1: Initial preference assignment
# -----------------------------
assignments = defaultdict(list)
assigned_set = set()
pref_cols = [f"Pref{i}" for i in range(1,6)]
student_order = df["Name"].tolist()
random.shuffle(student_order)

for pref in pref_cols:
    for name in student_order:
        if name in assigned_set:
            continue
        row = df[df["Name"] == name].iloc[0]
        proj = row[pref]
        if proj not in proj_capacity:
            continue
        if can_assign(row, proj, assignments):
            assignments[proj].append(name)
            assigned_set.add(name)

# -----------------------------
# STEP 2: Drop undersubscribed projects
# -----------------------------
not_viable = [p for p, members in assignments.items()
              if len(members) < (proj_capacity[p] // 2)]

# Collect students from dropped projects
to_reassign = []
for p in not_viable:
    to_reassign.extend(assignments[p])
    assignments[p] = []

# -----------------------------
# STEP 3: Reassign dropped students
# -----------------------------
for name in to_reassign:
    row = df[df["Name"] == name].iloc[0]
    placed = False

    # Try preferences again (only viable projects)
    for pref in pref_cols:
        proj = row[pref]
        if proj in not_viable:
            continue
        if can_assign(row, proj, assignments):
            assignments[proj].append(name)
            placed = True
            break

    # If not placed, try CompanyPreference
    if not placed:
        preferred_type = row["CompanyPreference"]
        feasible = [p for p in projects if p not in not_viable
                    and proj_types[p] == preferred_type
                    and can_assign(row, p, assignments)]
        if feasible:
            assignments[random.choice(feasible)].append(name)
            placed = True

    # If still not placed, fallback anywhere with space
    if not placed:
        fallback = [p for p in projects if p not in not_viable
                    and can_assign(row, p, assignments)]
        if fallback:
            assignments[random.choice(fallback)].append(name)

# -----------------------------
# STEP 4: Final balancing
# -----------------------------
# Place any unassigned students (just in case)
leftovers = [s for s in df["Name"] if all(s not in group for group in assignments.values())]
for name in leftovers:
    row = df[df["Name"] == name].iloc[0]
    preferred_type = row["CompanyPreference"]

    # First try projects of their type
    feasible = [p for p in projects if p not in not_viable
                and proj_types[p] == preferred_type
                and can_assign(row, p, assignments)]
    if feasible:
        assignments[random.choice(feasible)].append(name)
        continue

    # Otherwise try any project with space
    fallback = [p for p in projects if p not in not_viable
                and can_assign(row, p, assignments)]
    if fallback:
        assignments[random.choice(fallback)].append(name)

# -----------------------------
# STEP 5: Save results
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
            "PreferenceRank": rank if rank else "Fallback"
        })

result_df = pd.DataFrame(rows).sort_values(["Project", "Student"]).reset_index(drop=True)
result_df.to_csv(ASSIGNED_FILE, index=False)

summary = []
for project, members in assignments.items():
    if members:  # only viable projects
        nats = df[df["Name"].isin(members)]["Nationality"].tolist()
        summary.append({
            "Project": project,
            "ProjectType": proj_types[project],
            "Capacity": proj_capacity[project],
            "TeamSize": len(members),
            "RemainingSpots": proj_capacity[project] - len(members),
            "Nationalities": ", ".join(nats)
        })
summary_df = pd.DataFrame(summary).sort_values("Project")
summary_df.to_csv(SUMMARY_FILE, index=False)

print("✅ Assignment complete! Fallback respects Company/TUe preference.")
print(f"Saved {ASSIGNED_FILE}")
print(f"Saved {SUMMARY_FILE}")
