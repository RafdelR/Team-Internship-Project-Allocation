# 🧑‍🎓 Project Assignment Algorithm

A transparent, reproducible algorithm for assigning students to projects based on **ranked preferences**, **nationality diversity**, and **organization type preferences** (**Company** vs **TU/e**).  
It avoids “lonely” teams, prefers full or semi‑full teams, and publishes a **fairness report**.

> **Why this repo?** After project pitches, students submit a short form listing their **top 5 projects**, their **nationality**, and a **type preference** (Company or TU/e). This script forms teams using clear rules that everybody can audit and re-run (same seed → same result).

---

## 🚀 Quick Start

```bash
# 1) Put these files in the repo root:
#    - assign_students.py
#    - student_preferences.csv
#    - projects.csv
#
# 2) Run the script
python assign_students.py

# 3) Outputs generated
#    - assigned_teams.csv
#    - team_nationality_summary.csv
#    - fairness_summary.csv
```

---

## 📁 Repository Structure

```
.
├── assign_students.py              # Main script
├── student_preferences.csv         # Student inputs (see schema below)
├── projects.csv                    # Project definitions (type + capacity)
├── assigned_teams.csv              # OUTPUT: final assignments
├── team_nationality_summary.csv    # OUTPUT: per-team composition
├── fairness_summary.csv            # OUTPUT: fairness metrics
└── README.md                       # This file
```

---

## 🧾 CSV Schemas

### `student_preferences.csv` (required columns)
| Column              | Type   | Required | Notes                                                                 |
|---------------------|--------|----------|-----------------------------------------------------------------------|
| `Name`              | string | ✓        | Unique student identifier (name or id)                                |
| `Nationality`       | string | ✓        | Used for diversity (max 2 per nationality per project)                |
| `Pref1`..`Pref5`    | string | ✓        | Ranked project ids, e.g., `Project4`                                  |
| `CompanyPreference` | string | ✓        | Either `Company` or `TUe` (used as **fallback** only)                 |

**Rules**
- Preferences must match valid project ids in `projects.csv` (invalid names are ignored gracefully).
- CompanyPreference is only used if none of the 5 preferences can be honored.

---

### `projects.csv` (required columns)
| Column     | Type    | Required | Notes                                             |
|------------|---------|----------|---------------------------------------------------|
| `Project`  | string  | ✓        | Unique project id, e.g., `Project7`              |
| `Type`     | string  | ✓        | Either `Company` or `TUe`                        |
| `Capacity` | integer | ✓        | Maximum number of students in this project       |

**Rules**
- Sum of all capacities **must be ≥** number of students, otherwise the script aborts.
- Teams should be reasonably filled; extremely undersubscribed projects may be **dropped** and their students re-assigned.

---

## ⚙️ Configuration (inside `assign_students.py`)

- `SEED = 42` — fixed seed for reproducibility.
- **Nationality limit:** hard rule of **max 2 students per nationality per project** (change in `can_assign()` if needed).
- **Undersubscription threshold:** projects with fewer than **half** their capacity initially filled are considered **not viable** and get dropped (change in “Step 2” if you want a different threshold).

---

## 🧠 Algorithm (Greedy, Company/TU/e‑aware)

### Goals
1. **Honor preferences** (Pref1 → Pref5) as much as possible.  
2. **Respect capacity** (never overfill).  
3. **Enforce diversity** (≤2 students per nationality per team).  
4. **Avoid ghost teams**: drop severely undersubscribed projects and reassign their members.  
5. **Fallback by type**: if a student gets none of their 5 choices, try **Company/TUe** projects matching their `CompanyPreference`.

### Steps
1. **Initial Preference Assignment**  
   - Iterate Pref1→Pref5 in rounds; place students when the target project has space and nationality cap allows.

2. **Drop Undersubscribed Projects**  
   - Any project with `< capacity/2` students after Step 1 is **not viable** and is dropped.

3. **Reassign from Dropped Projects**  
   - For each affected student:  
     a) Try remaining preferences (viable projects only).  
     b) Else try any project of their **CompanyPreference** type.  
     c) Else assign to any viable project with space.

4. **Final Balancing**  
   - If any students are still unassigned (rare), place them using the same **type‑aware** logic.

5. **Outputs & Fairness Summary**  
   - Write `assigned_teams.csv`, `team_nationality_summary.csv`, and `fairness_summary.csv`.  
   - Print a console summary (Pref ranks, fallback count, type match %).

---

## 🧩 Pseudocode

```text
read students, projects
assert total_capacity >= num_students

assignments = {}

# Step 1: Preferences
for pref in Pref1..Pref5:
  for student in shuffled_students:
    if student not assigned:
      target = student[pref]
      if capacity[target] not full and nationality_ok(student, target):
        assign(student, target)

# Step 2: Drop undersubscribed
not_viable = [p for p in projects if size[p] < capacity[p]//2]
to_reassign = all students from not_viable
clear assignments[not_viable]

# Step 3: Reassign dropped students
for s in to_reassign:
  placed = try remaining preferences on viable projects
        or try projects of s.CompanyPreference type
        or try any viable project with space
  if not placed: log warning

# Step 4: Final balancing for leftovers (rare)
place by type if possible, else anywhere feasible

# Step 5: Save outputs + fairness
write assigned_teams.csv, team_nationality_summary.csv, fairness_summary.csv
print fairness summary
```

---

## 🔍 Logging & Transparency

The script prints:
- Who was assigned and at which **preference rank**.
- Which projects were **dropped** and why (members/capacity).
- Where **reassignments** went (preference vs fallback).
- A final **fairness report** (also saved to CSV).

Example console lines:
```
✅ Alice assigned to Project3 (Pref 1)
⚠️ Dropping Project7: 1/4 students
🔄 Marta reassigned to Project3 via CompanyPreference=Company
📊 Fairness Summary...
```

---

## 📊 Fairness Summary (what you get)

- **Preference ranks:** how many got Pref1, Pref2, … Pref5.  
- **Fallback:** how many needed fallback (Company/TUe or random within rules).  
- **Type match:** percent placed into a project whose type matches their `CompanyPreference`.

All of the above are printed **and** saved to `fairness_summary.csv`.

---

## 🪪 Reproducibility

- All randomized steps use a fixed seed (`SEED = 42`).  
- Given the same input CSVs, anyone can **re-run and verify** identical outputs.  
- Great for student transparency: publish the code and the random seed.

---

## 🧱 Edge Cases & How They’re Handled

1. **Lonely student in a big project**  
   - Projects with `< capacity/2` members are **dropped**, and students are re‑assigned. No ghost teams.

2. **Oversubscribed popular projects**  
   - Capacity + nationality constraints are enforced; excess students move to next preferences or fallback type.

3. **Nationality bottlenecks**  
   - Hard cap of **≤2 per nationality** per team at all times (including fallback and balancing).

4. **Invalid project names in preferences**  
   - Ignored gracefully during assignment (student will be considered at later preferences/fallback).

5. **Capacities too small for total students**  
   - The script stops early with a clear error message.

6. **All projects of a student’s preferred type are full**  
   - We try other viable projects (cross-type) to ensure everyone gets placed.

---

## 🧪 Example Input (optional demo)

`projects.csv`
```csv
Project,Type,Capacity
Project1,Company,3
Project2,TUe,2
Project3,Company,3
Project4,TUe,3
Project5,Company,3
Project6,TUe,2
Project7,Company,2
Project8,TUe,2
```

`student_preferences.csv`
```csv
Name,Nationality,Pref1,Pref2,Pref3,Pref4,Pref5,CompanyPreference
Alice,NL,Project1,Project2,Project3,Project4,Project5,TUe
Bob,DE,Project2,Project1,Project3,Project5,Project6,Company
Carlos,ES,Project3,Project1,Project2,Project4,Project7,Company
Diego,PT,Project1,Project3,Project2,Project4,Project8,TUe
Emma,FR,Project4,Project2,Project1,Project3,Project5,TUe
Liam,UK,Project5,Project4,Project2,Project6,Project1,Company
Sofia,IT,Project2,Project3,Project4,Project1,Project8,TUe
Marco,BR,Project3,Project5,Project7,Project1,Project2,Company
Yuki,JP,Project1,Project4,Project6,Project3,Project2,Company
Kenji,JP,Project4,Project1,Project2,Project8,Project6,TUe
Hannah,NL,Project5,Project2,Project4,Project7,Project3,Company
Noah,NL,Project2,Project6,Project3,Project5,Project1,TUe
Marta,ES,Project1,Project5,Project7,Project2,Project4,Company
Oliver,SE,Project3,Project4,Project1,Project6,Project8,TUe
Lucas,MX,Project2,Project1,Project6,Project4,Project5,Company
Zara,IN,Project4,Project5,Project2,Project1,Project7,TUe
Elena,IT,Project5,Project3,Project1,Project7,Project8,Company
Raj,IN,Project1,Project6,Project3,Project4,Project5,TUe
Mina,EG,Project2,Project4,Project8,Project5,Project1,Company
Jonas,DE,Project3,Project1,Project2,Project6,Project4,TUe
```

---

## 🗺️ Visual Flow (Mermaid)

```mermaid
flowchart TD
  A[Start] --> B[Load CSVs & validate]
  B --> C{Total capacity ≥ students?}
  C -- No --> X[Abort with error]
  C -- Yes --> D[Pref rounds: Pref1→Pref5]
  D --> E[Drop undersubscribed projects]
  E --> F[Reassign from dropped projects]
  F --> G{All students placed?}
  G -- No --> H[Final balancing (type-aware)]
  G -- Yes --> I[Save outputs & fairness]
  H --> I[Save outputs & fairness]
  I --> Z[End]
```

---

## ❓ FAQ

**Q: Why not guarantee every project is exactly full?**  
A: That requires a global optimization model (ILP). This repo prioritizes **simplicity and transparency** with a greedy approach that still avoids ghost teams and honors constraints. You can extend it to ILP later if needed.

**Q: Can we change the “≤2 per nationality” rule?**  
A: Yes — see the `can_assign()` function in `assign_students.py`.

**Q: Is the randomization fair?**  
A: Yes — it’s reproducible with a fixed seed so everyone sees the same result when re-running with identical inputs.

---

## 🧩 Extending the Script

- Add **per‑project nationality caps** (instead of a global 2).  
- Add **hard constraints** for Company/TUe (never cross type).  
- Switch to **ILP** (e.g., OR‑Tools / PuLP) for guaranteed globally optimal assignments.  
- Add **CLI flags** for seed, thresholds, and file paths.

---

## 🔐 License

Choose a license (e.g., MIT) and update this section.

---

## 🧰 Contributing

PRs are welcome! Please:
1. Open an issue to discuss your idea.
2. Include tests or example inputs when possible.
3. Keep logs human‑readable and concise.

---

## 🗓️ Changelog

- **v1.0.0** — Initial public release: greedy preference assignment with diversity, type‑aware fallback, fairness reporting, and anti‑ghost‑team logic.
