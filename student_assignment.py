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
FAIRNESS_FILE = "fairness_summary.csv"
UNASSIGNED_FILE = "unassigned_students.csv"

SEED = 42
random.seed(SEED)

# -----------------------------
# LOAD DATA
# -----------------------------
try:
    df = pd.read_csv(STUDENTS_FILE)
    projects_df = pd.read_csv(PROJECTS_FILE)
except FileNotFoundError as e:
    raise FileNotFoundError(
        "Could not find one of the input files. "
        "Make sure student_preferences.csv and projects.csv are in the same folder."
    ) from e

required_student_cols = {
    "Name",
    "Nationality",
    "Background",
    "TimeSlots",
    "Pref1",
    "Pref2",
    "Pref3",
    "Pref4",
    "Pref5",
    "CompanyPreference",
}
required_project_cols = {"Project", "Type", "Capacity"}

if not required_student_cols.issubset(df.columns):
    raise ValueError(f"student_preferences.csv must have columns: {required_student_cols}")

if not required_project_cols.issubset(projects_df.columns):
    raise ValueError(f"projects.csv must have columns: {required_project_cols}")

proj_types = dict(zip(projects_df["Project"], projects_df["Type"]))
proj_capacity = dict(zip(projects_df["Project"], projects_df["Capacity"]))
projects = list(proj_types.keys())

if sum(proj_capacity.values()) < len(df):
    raise ValueError(
        f"Total capacity ({sum(proj_capacity.values())}) "
        f"is less than number of students ({len(df)}). Increase project capacities."
    )

# -----------------------------
# HELPERS
# -----------------------------
def can_assign(student_row, project, assignments):
    """Check if student can join a project (capacity + nationality + background + time overlap)."""
    if project not in proj_capacity:
        return False
    if len(assignments[project]) >= proj_capacity[project]:
        return False

    members_df = df[df["Name"].isin(assignments[project])]
    nats = members_df["Nationality"].tolist()
    bgs = members_df["Background"].tolist()

    # ≤ 2 per nationality and ≤ 2 per background
    if nats.count(student_row["Nationality"]) >= 2:
        return False
    if bgs.count(student_row["Background"]) >= 2:
        return False

    # Time overlap rule: at least 2 shared slots collectively
    if not members_df.empty:
        member_slots = [set(ts.split(",")) for ts in members_df["TimeSlots"]]
        new_slots = set(student_row["TimeSlots"].split(","))
        all_slots = member_slots + [new_slots]
        shared = set.intersection(*all_slots)
        if len(shared) < 2:
            return False

    return True

# -----------------------------
# STEP 1: Initial preference assignment
# -----------------------------
assignments = defaultdict(list)
assigned_set = set()
unassigned_students = []
pref_cols = [f"Pref{i}" for i in range(1, 6)]
student_order = df["Name"].tolist()
random.shuffle(student_order)

print("Starting initial preference assignment...")
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
            print(f"{name} assigned to {proj} (Pref {pref[-1]})")

# -----------------------------
# STEP 2: Drop undersubscribed projects
# -----------------------------
not_viable = [p for p, members in assignments.items() if len(members) < (proj_capacity[p] // 2)]

if not_viable:
    print("\nDropping undersubscribed projects:")
    for p in not_viable:
        print(f" - {p}: {len(assignments[p])}/{proj_capacity[p]} students")
else:
    print("\nAll projects have enough students to be viable.")

to_reassign = []
for p in not_viable:
    to_reassign.extend(assignments[p])
    assignments[p] = []

# -----------------------------
# STEP 3: Reassign dropped students
# -----------------------------
print("\nReassigning students from dropped projects...")
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
            print(f"{name} reassigned to {proj} via Pref {pref[-1]}")
            placed = True
            break

    # Try CompanyPreference type
    if not placed:
        preferred_type = row["CompanyPreference"]
        feasible = [
            p for p in projects
            if p not in not_viable
            and proj_types[p] == preferred_type
            and can_assign(row, p, assignments)
        ]
        if feasible:
            proj = random.choice(feasible)
            assignments[proj].append(name)
            print(f"{name} reassigned to {proj} via CompanyPreference={preferred_type}")
            placed = True

    # If still not placed → unassigned
    if not placed:
        unassigned_students.append(name)
        print(f"{name} could not be assigned — added to unassigned list.")

# -----------------------------
# STEP 4: Final balancing
# -----------------------------
leftovers = [s for s in df["Name"] if all(s not in group for group in assignments.values()) and s not in unassigned_students]
if leftovers:
    print("\nFinal balancing, placing leftovers...")
for name in leftovers:
    row = df[df["Name"] == name].iloc[0]
    preferred_type = row["CompanyPreference"]

    # Try projects of their type
    feasible = [
        p for p in projects
        if p not in not_viable
        and proj_types[p] == preferred_type
        and can_assign(row, p, assignments)
    ]
    if feasible:
        proj = random.choice(feasible)
        assignments[proj].append(name)
        print(f"{name} placed in {proj} (CompanyPreference={preferred_type})")
        continue

    # Otherwise mark as unassigned
    unassigned_students.append(name)
    print(f"{name} could not be placed — added to unassigned list.")

# -----------------------------
# STEP 5: Save results
# -----------------------------
rows = []
for project, members in assignments.items():
    for name in members:
        st = df[df["Name"] == name].iloc[0]
        rank = None
        for i in range(1, 6):
            if st[f"Pref{i}"] == project:
                rank = i
                break
        rows.append({
            "Project": project,
            "ProjectType": proj_types[project],
            "Capacity": proj_capacity[project],
            "Student": name,
            "Nationality": st["Nationality"],
            "Background": st["Background"],
            "TimeSlots": st["TimeSlots"],
            "CompanyPreference": st["CompanyPreference"],
            "PreferenceRank": rank if rank else "Reassigned"
        })

result_df = pd.DataFrame(rows).sort_values(["Project", "Student"]).reset_index(drop=True)
result_df.to_csv(ASSIGNED_FILE, index=False)

summary = []
for project, members in assignments.items():
    if members:
        members_df = df[df["Name"].isin(members)]
        nats = members_df["Nationality"].tolist()
        bgs = members_df["Background"].tolist()
        times = members_df["TimeSlots"].tolist()
        summary.append({
            "Project": project,
            "ProjectType": proj_types[project],
            "Capacity": proj_capacity[project],
            "TeamSize": len(members),
            "RemainingSpots": proj_capacity[project] - len(members),
            "Nationalities": ", ".join(nats),
            "Backgrounds": ", ".join(bgs),
            "TimeSlots": ", ".join(times)
        })
summary_df = pd.DataFrame(summary).sort_values("Project")
summary_df.to_csv(SUMMARY_FILE, index=False)

# -----------------------------
# STEP 6: Fairness Summary
# -----------------------------
print("\nFairness Summary")
pref_counts = Counter(result_df["PreferenceRank"])
total_students = len(df)

fairness_rows = []
for i in range(1, 6):
    count = pref_counts.get(i, 0)
    pct = 100 * count / total_students
    print(f" - Pref{i}: {count} students ({pct:.1f}%)")
    fairness_rows.append({"Category": f"Pref{i}", "Count": count, "Percentage": pct})

reassigned_count = pref_counts.get("Reassigned", 0)
print(f" - Reassigned (non-pref): {reassigned_count} students ({100*reassigned_count/total_students:.1f}%)")
fairness_rows.append({"Category": "Reassigned", "Count": reassigned_count, "Percentage": 100*reassigned_count/total_students})

unassigned_count = len(unassigned_students)
print(f" - Unassigned: {unassigned_count} students ({100*unassigned_count/total_students:.1f}%)")
fairness_rows.append({"Category": "Unassigned", "Count": unassigned_count, "Percentage": 100*unassigned_count/total_students})

match_type = sum(1 for _, row in result_df.iterrows() if row["CompanyPreference"] == row["ProjectType"])
pct_match = 100 * match_type / max(len(result_df), 1)
print(f" - Type match (Company/TUe): {match_type}/{len(result_df)} ({pct_match:.1f}%)")
fairness_rows.append({"Category": "TypeMatch", "Count": match_type, "Percentage": pct_match})

pd.DataFrame(fairness_rows).to_csv(FAIRNESS_FILE, index=False)

# -----------------------------
# STEP 7: Save unassigned students
# -----------------------------
if unassigned_students:
    print("\nThe following students could not be placed automatically:")
    for s in unassigned_students:
        print(f" - {s}")
    pd.DataFrame({"UnassignedStudent": unassigned_students}).to_csv(UNASSIGNED_FILE, index=False)
    print(f"\nUnassigned students saved to {UNASSIGNED_FILE}")
else:
    print("\nAll students successfully placed.")

print("\nAssignment complete! Results saved.")
print(f" {ASSIGNED_FILE}")
print(f" {SUMMARY_FILE}")
print(f" {FAIRNESS_FILE}")
