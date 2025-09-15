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

# -----------------------------
# LOAD DATA
# -----------------------------
try:
    df = pd.read_csv(STUDENTS_FILE)
    projects_df = pd.read_csv(PROJECTS_FILE)
except FileNotFoundError as e:
    raise FileNotFoundError("⚠️ Could not find one of the input files. "
                            "Make sure student_preferences.csv and projects.csv are in the same folder.") from e

required_student_cols = {"Name", "Nationality", "Pref1", "Pref2", "Pref3", "Pref4", "Pref5", "CompanyPreference"}
required_project_cols = {"Project", "Type", "Capacity"}

if not required_student_cols.issubset(df.columns):
    raise ValueError(f"⚠️ student_preferences.csv must have columns: {required_student_cols}")

if not required_project_cols.issubset(projects_df.columns):
    raise ValueError(f"⚠️ projects.csv must have columns: {required_project_cols}")

proj_types = dict(zip(projects_df["Project"], projects_df["Type"]))
proj_capacity = dict(zip(projects_df["Project"], projects_df["Capacity"]))
projects = list(proj_types.keys())

if sum(proj_capacity.values()) < len(df):
    raise ValueError(f"⚠️ Total capacity ({sum(proj_capacity.values())}) "
                     f"is less than number of students ({len(df)}). Increase project capacities.")

# -----------------------------
# HELPERS
# -----------------------------
def can_assign(student_row, project, assignments):
    """Check if student can join a project (capacity + nationality)."""
    if project not in proj_capacity:
        return False
    if len(assignments[project]) >= proj_capacity[project]:
        return False
    current_nats = df[df["Name"].isin(assignments[project])]["Nationality"].tolist()
    return current_nats.count(student_row["Nationality"]) < 2  # ≤ 2 per nationality

# -----------------------------
# STEP 1: Initial preference assignment
# -----------------------------
assignments = defaultdict(list)
assigned_set = set()
pref_cols = [f"Pref{i}" for i in range(1,6)]
student_order = df["Name"].tolist()
random.shuffle(student_order)

print("➡️ Starting initial preference assignment...")
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
            print(f"  ✅ {name} assigned to {proj} (Pref {pref[-1]})")

# -----------------------------
# STEP 2: Drop undersubscribed projects
# -----------------------------
not_viable = [p for p, members in assignments.items()
              if len(members) < (proj_capacity[p] // 2)]

if not_viable:
    print("\n⚠️ Dropping undersubscribed projects:")
    for p in not_viable:
        print(f"   - {p}: {len(assignments[p])}/{proj_capacity[p]} students")
else:
    print("\n✅ All projects have enough students to be viable.")

to_reassign = []
for p in not_viable:
    to_reassign.extend(assignments[p])
    assignments[p] = []

# -----------------------------
# STEP 3: Reassign dropped students
# -----------------------------
print("\n➡️ Reassigning students from dropped projects...")
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
            print(f"  🔄 {name} reassigned to {proj} via Pref {pref[-1]}")
            placed = True
            break

    # If not placed, try CompanyPreference
    if not placed:
        preferred_type = row["CompanyPreference"]
        feasible = [p for p in projects if p not in not_viable
                    and proj_types[p] == preferred_type
                    and can_assign(row, p, assignments)]
        if feasible:
            proj = random.choice(feasible)
            assignments[proj].append(name)
            print(f"  🔄 {name} reassigned to {proj} via CompanyPreference={preferred_type}")
            placed = True

    # If still not placed, fallback anywhere with space
    if not placed:
        fallback = [p for p in projects if p not in not_viable
                    and can_assign(row, p, assignments)]
        if fallback:
            proj = random.choice(fallback)
            assignments[proj].append(name)
            print(f"  🔄 {name} assigned randomly to {proj}")
        else:
            print(f"  ❌ Could not assign {name}, no space available!")

# -----------------------------
# STEP 4: Final balancing
# -----------------------------
leftovers = [s for s in df["Name"] if all(s not in group for group in assignments.values())]
if leftovers:
    print("\n⚠️ Final balancing, placing leftovers...")
for name in leftovers:
    row = df[df["Name"] == name].iloc[0]
    preferred_type = row["CompanyPreference"]

    # First try projects of their type
    feasible = [p for p in projects if p not in not_viable
                and proj_types[p] == preferred_type
                and can_assign(row, p, assignments)]
    if feasible:
        proj = random.choice(feasible)
        assignments[proj].append(name)
        print(f"  🔄 {name} placed in {proj} (CompanyPreference={preferred_type})")
        continue

    # Otherwise try any project with space
    fallback = [p for p in projects if p not in not_viable
                and can_assign(row, p, assignments)]
    if fallback:
        proj = random.choice(fallback)
        assignments[proj].append(name)
        print(f"  🔄 {name} placed in {proj} (Fallback random)")
    else:
        print(f"  ❌ ERROR: Could not place {name}, all projects full!")

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
    if members:
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

# -----------------------------
# STEP 6: Fairness Summary
# -----------------------------
print("\n📊 Fairness Summary")
pref_counts = Counter(result_df["PreferenceRank"])
total_students = len(result_df)

for i in range(1,6):
    count = pref_counts.get(i, 0)
    pct = 100 * count / total_students
    print(f" - Pref{i}: {count} students ({pct:.1f}%)")

fallback_count = pref_counts.get("Fallback", 0)
print(f" - Fallback: {fallback_count} students ({100*fallback_count/total_students:.1f}%)")

# Match between CompanyPreference and actual assignment
match_type = 0
for _, row in result_df.iterrows():
    if row["CompanyPreference"] == row["ProjectType"]:
        match_type += 1
print(f" - Type match (Company/TUe): {match_type}/{total_students} "
      f"({100*match_type/total_students:.1f}%)")

print("\n✅ Assignment complete! Results saved.")
print(f"📂 {ASSIGNED_FILE}")
print(f"📂 {SUMMARY_FILE}")
