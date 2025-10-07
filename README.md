# 🧑‍🎓 Project Assignment Algorithm

A transparent, reproducible algorithm for assigning students to projects based on **ranked preferences**, **nationality diversity**, **academic background**, and **shared availability** (time slots **A–E**).  
It avoids “lonely” teams, ensures realistic meeting compatibility, and produces a **fairness report**.

> **Why this repo?**  
> After project pitches, students submit a short form listing their **top 5 projects**, **nationality**, **study background**, **availability slots**, and **organization preference** (Company or TU/e).  
> This algorithm automatically forms balanced, compatible teams under transparent and reproducible rules.

---

## 🚀 Quick Start

```bash
# 1) Place these files in the same folder:
#    - assign_students.py
#    - student_preferences.csv
#    - projects.csv

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

| Column              | Type   | Required | Notes |
|---------------------|--------|----------|--------|
| `Name`              | string | ✓ | Unique student identifier (name or ID). |
| `Nationality`       | string | ✓ | Used for diversity (≤2 per nationality per project). |
| `Background`        | string | ✓ | Academic background (≤2 per background per project). |
| `TimeSlots`         | string | ✓ | Availability slots, e.g. `"A,B,E"` (must share ≥2 slots collectively per team). |
| `Pref1`..`Pref5`    | string | ✓ | Ranked project IDs, e.g. `Project4`. |
| `CompanyPreference` | string | ✓ | Either `Company` or `TUe` (fallback type). |

**Time Slot Rules:**
- Possible values: `A`, `B`, `C`, `D`, `E` (each representing a time block).  
- Students list 3 they are free for team meetings, separated by commas.  
- All team members must share **at least 2 common slots collectively**.

---

### `projects.csv`

| Column     | Type    | Required | Notes |
|------------|---------|----------|--------|
| `Project`  | string  | ✓ | Unique project ID, e.g. `Project7`. |
| `Type`     | string  | ✓ | Either `Company` or `TUe`. |
| `Capacity` | integer | ✓ | Maximum number of students in the project. |

---

## ⚙️ Configuration

- `SEED = 42` — ensures reproducibility.  
- **Max per nationality:** 2  
- **Max per background:** 2  
- **Minimum shared time slots:** 2 (across all team members).  
- **Undersubscription rule:** Projects with fewer than half their capacity are dropped and students reassigned.

---

## 🧠 Algorithm Overview

### Goals
1. Honor ranked preferences as much as possible.  
2. Respect project capacity.  
3. Maintain nationality & background diversity.  
4. Guarantee at least two shared time slots collectively per team.  
5. Avoid underfilled (“ghost”) projects.  
6. Respect type preference (Company vs TU/e).  
7. Never assign randomly — unplaceable students are exported for review.

---

### Step-by-Step

1. **Initial Preference Assignment**  
   - Students are shuffled for fairness.  
   - Each is placed into their highest available preference that satisfies:
     - Capacity not full  
     - ≤2 same nationalities  
     - ≤2 same backgrounds  
     - ≥2 shared time slots with all current members  

2. **Drop Undersubscribed Projects**  
   - Projects with fewer than half their capacity filled are removed.  
   - Their members are re-entered into the assignment pool.

3. **Reassign Students**  
   - Reassign dropped students using:
     - Next valid preferences (only viable projects).  
     - Fallback projects matching their `CompanyPreference`.  
     - If no compatible project exists → student becomes unassigned.

4. **Final Balancing**  
   - Any remaining unassigned students are checked one last time for fitting projects (type-aware).  
   - If none fit, they are written to `unassigned_students.csv`.

5. **Outputs & Fairness Summary**  
   - Generates detailed CSVs and a console report showing preference satisfaction, unassigned count, and diversity metrics.

---

## 📊 Fairness Summary (example)

```
Fairness Summary
 - Pref1: 8 students (40.0%)
 - Pref2: 5 students (25.0%)
 - Pref3: 3 students (15.0%)
 - Pref4: 2 students (10.0%)
 - Pref5: 1 students (5.0%)
 - Reassigned: 1 students (5.0%)
 - Unassigned: 2 students (10.0%)
 - Type match (Company/TUe): 18/20 (90.0%)
```

---

## 🧾 Example of `TimeSlots` and `unassigned_students.csv`

`student_preferences.csv` example:
```csv
Name,Nationality,Background,TimeSlots,Pref1,Pref2,Pref3,Pref4,Pref5,CompanyPreference
Alice,NL,Electrical Engineering,A,B,E,Project1,Project2,Project3,Project4,Project5,TUe
Bob,DE,Mechanical Engineering,B,C,E,Project2,Project1,Project3,Project5,Project6,Company
...
```

`unassigned_students.csv` output:
```csv
UnassignedStudent
Carlos
Emma
```
These students could not be assigned without violating the nationality, background, or time-slot constraints.

---

## 🧱 Edge Cases & Handling

1. **Lonely projects:** dropped if fewer than half their capacity filled.  
2. **Nationality or background overload:** no more than 2 of either.  
3. **Time-slot conflicts:** project rejected if collective overlap <2 slots.  
4. **Invalid preferences:** ignored safely.  
5. **Type fallback:** fallback tries same-type projects first.  
6. **No random placement:** unassign incompatible students.  

---

## 🪪 Reproducibility

- Fixed seed ensures identical outputs for identical inputs.  
- Fully deterministic and auditable for transparency.  

---

## ❓ FAQ

**Q: What if a student can't be placed anywhere?**  
They appear in `unassigned_students.csv` and are not forced into a random project.

**Q: Can I adjust the time-slot rule?**  
Yes, edit the `can_assign()` function — change the number of required shared slots or accepted values (A–E).

**Q: Are overlapping slots checked collectively?**  
Yes — all team members (existing + new) must have ≥2 shared slots collectively.

---

## 🧰 Contributing

PRs are welcome.  
Please:
1. Open an issue before major changes.  
2. Include test CSVs when submitting improvements.  
3. Keep print logs readable and transparent.

---

## 🗓️ Changelog

- **v1.3.0** — Added *TimeSlots* availability rule: teams must share at least 2 common time slots collectively.  
- **v1.2.0** — Removed random fallback; unassign incompatible students.  
- **v1.1.0** — Added fairness summary and type-aware fallback logic.  
- **v1.0.0** — Initial public release: preference-based assignment with diversity and capacity logic.
