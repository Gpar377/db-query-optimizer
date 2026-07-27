# Relational SQL Query Optimizer Engine

A relational algebraic SQL query optimizer built in Python. It parses SQL select statements, constructs logical operator trees, applies heuristic optimization rules, estimates cardinality/costs using database catalog statistics, and searches for optimal physical execution structures.

## Features & Architecture

*   **Logical Execution Operators:** Immutable execution operators (`Scan`, `Filter`, `Project`, `Join`) representing query trees.
*   **Heuristic Optimization Engine:** Logical rewrites utilizing rules:
    *   **Predicate Pushdown:** Pushes `Filter` past `Join` to filter records as close as possible to the database scans.
    *   **Projection Pushdown:** Eliminates unused columns early.
*   **Cost-Based Optimizer (CBO):**
    *   **Catalog System:** Collects metadata (row count cardinalities, distinct column value counts).
    *   **Selectivity Calculations:** Employs selectivity estimation for equijoins:
        $$\text{Selectivity} = \frac{1}{\max(\text{Distinct}(\text{LeftCol}), \text{Distinct}(\text{RightCol}))}$$
    *   **Dynamic Programming Join Reordering:** System R style dynamic programming solver grouping joins to minimize the size of intermediate results.

## Getting Started

### Prerequisites

*   Python 3.10 or higher. No external libraries are required.

### Optimize SQL Queries

Run the query optimizer CLI by passing a SQL string:

```bash
python optimize.py --sql "SELECT users.name FROM users JOIN logs ON users.id = logs.user_id WHERE users.age > 30"
```

Output details the original vs optimized plan and the computed speedup:
```text
==================================================
Relational SQL Query Optimizer Engine
==================================================
Input SQL:
  SELECT users.name FROM users JOIN logs ON users.id = logs.user_id WHERE users.age > 30

--- [Logical Execution Plan] ---
Project(cols=['users.name'])
  Filter(cond='users.age > 30')
    Join(cond='users.id = logs.user_id')
      Scan(users, cols=['users.id', 'users.name'])
      Scan(logs, cols=['logs.user_id'])

--- [Optimized Plan (Heuristics)] ---
Project(cols=['users.name'])
  Join(cond='users.id = logs.user_id')
    Filter(cond='users.age > 30')
      Scan(users, cols=['users.id', 'users.name'])
    Scan(logs, cols=['logs.user_id'])

--- [Cost Calculations] ---
Original Plan:  Cardinality ~ 100 rows, Cost score ~ 5,100,110.00
Optimized Plan: Cardinality ~ 100 rows, Cost score ~ 5,000,130.00
Plan Cost Reduction: 1.02x improvement!
```

### Run Optimization Tests

Run the test suite checking parser rules, selectivity math, pushdown logic, and DP join reordering:

```bash
python run_tests.py
```
