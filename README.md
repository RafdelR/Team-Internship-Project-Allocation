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
#    - unassigned_students.csv
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
├── unassigned_students.csv         # OUTPUT: students who couldn't be placed
└── README.md                       # This file
```

---

## 🧾 CSV Schemas

### `student_preferences.csv`
| Column              | Type   | Required | Notes                                                                 |
|---------------------|--------|----------|-----------------------------------------------------------------------|
| `Name`              | string | ✓        | Unique student identifier (name or id)                                |
| `Nationality`       | string | ✓        | Used for diversity (max 2 per nationality per project)                |
| `Pref1`..`Pref5`    | string | ✓        | Ranked project ids, e.g., `Project4`                                  |
| `CompanyPreference` | string | ✓        | Either `Company` or `TUe` (used as fallback type)                     |

**Rules**
- Preferences must match valid project ids in `projects.csv` (invalid names are ignored gracefully).
- CompanyPreference is used **only** when none of the 5 preferences can be fulfilled.

---

### `projects.csv`
| Column     | Type    | Required | Notes                                             |
|------------|---------|----------|---------------------------------------------------|
| `Project`  | string  | ✓        | Unique project id, e.g., `Project7`              |
| `Type`     | string  | ✓        | Either `Company` or `TUe`                        |
| `Capacity` | integer | ✓        | Maximum number of students in this project       |

**Rules**
- Total capacity must be **≥** total number of students, otherwise the script aborts.
- Projects that attract fewer than half their capacity are considered **not viable** and their students are reassigned.

---

## ⚙️ Configuration

- `SEED = 42` — ensures reproducibility.
- **Nationality limit:** max 2 students per nationality per project (set in `can_assign()`).
- **Undersubscription threshold:** projects with fewer than **half their capacity** filled are dropped.

---

## 🧠 Algorithm (Greedy + Company/TU/e-aware + Unassignment Logic)

### Goals
1. **Honor preferences** (Pref1 → Pref5) as much as possible.  
2. **Respect capacity** (no overfilling).  
3. **Maintain diversity** (≤2 per nationality per project).  
4. **Avoid “ghost projects”** (drop low-interest ones).  
5. **Respect type preferences** (Company vs TU/e).  
6. **Do not assign anyone randomly** — if a student can’t be placed, they are added to an *unassigned list* for manual review.

---

### Step-by-Step

1. **Initial Preference Assignment**  
   - Students are shuffled (for fairness) and placed into their highest available preference that respects nationality and capacity.

2. **Drop Undersubscribed Projects**  
   - Projects with fewer than half their capacity filled are removed.
   - Students in those projects go back into the reassignment pool.

3. **Reassign Students**  
   - Each student is reassigned by priority:
     1. Try another valid preference (among viable projects).
     2. Try a project matching their `CompanyPreference` type.
     3. If neither works, they are **added to the unassigned list** (no random fallback).

4. **Final Balancing**  
   - Remaining unplaced students are again checked against projects of their preferred type.
   - If still none fits → added to unassigned list.

5. **Outputs & Fairness Summary**  
   - `assigned_teams.csv` → final placements.  
   - `team_nationality_summary.csv` → diversity overview.  
   - `fairness_summary.csv` → stats on how fair the matching was.  
   - `unassigned_students.csv` → list of students who couldn’t be placed automatically.

---

## 📊 Fairness Summary (example)

```
📊 Fairness Summary
 - Pref1: 8 students (40.0%)
 - Pref2: 5 students (25.0%)
 - Pref3: 3 students (15.0%)
 - Pref4: 2 students (10.0%)
 - Pref5: 1 students (5.0%)
 - Reassigned: 1 students (5.0%)
 - Unassigned: 2 students (10.0%)
 - Type match (Company/TUe): 18/20 (90.0%)
```

This fairness summary is printed and saved to `fairness_summary.csv`.

---

## 🧾 Example of `unassigned_students.csv`

```csv
UnassignedStudent
Alice
Jonas
```

These students did not fit in any project given capacity, nationality, or type constraints and should be manually reviewed.

---

## 🪪 Reproducibility

- Deterministic (fixed random seed).  
- Identical CSV inputs → identical team outputs.  
- Allows transparent reruns and auditability.

---

## 🧱 Edge Cases & Fixes

1. **Lonely students**  
   - Projects under half capacity are dropped; students reassigned or unassigned.

2. **Oversubscribed projects**  
   - Overflow handled by next preferences or type-based fallback.

3. **Nationality limit**  
   - Hard cap of 2 per nationality per team.

4. **Invalid preferences**  
   - Ignored automatically; no crash.

5. **Type respect**  
   - When possible, fallback tries projects of same type first.

6. **No random placements**  
   - If none of the above rules apply → student is marked *unassigned* and output separately.

---

## ❓ FAQ

**Q: What happens if a student can’t be placed anywhere?**  
A: They appear in `unassigned_students.csv` and are excluded from any team. This ensures transparency and avoids arbitrary placements.

**Q: Why not guarantee every project is full?**  
A: This script prioritizes clarity over global optimization. You can extend it later using ILP or OR-Tools for exact balancing.

**Q: Can I change the “max 2 per nationality” rule?**  
A: Yes, edit the `can_assign()` function.

**Q: Is the randomization fair?**  
A: Yes — it’s deterministic (fixed seed). Rerunning with the same inputs yields identical results.

---

## 🧰 Contributing

PRs are welcome!  
Please:
1. Open an issue before large changes.  
2. Include test CSVs if possible.  
3. Keep logging clear and reproducible.

---

## 🗓️ Changelog

- **v1.2.0** — *Removed random fallback entirely:* students who cannot be placed are now output to `unassigned_students.csv` instead of being randomly assigned.  
- **v1.1.0** — Added fairness summary and type-aware fallback logic.  
- **v1.0.0** — Initial public release: preference assignment with nationality & type balance, fairness reporting, and anti-ghost-team logic.
