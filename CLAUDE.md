# Claude Code Guidelines - DB Query Optimizer

## Project Overview
This repository contains a logical/physical database query optimizer engine utilizing heuristic rewrite rules and cost-based join reordering.

## Technology Stack
*   **Python 3.10+** (Core AST, catalogs, optimization solver) or **C++17**
*   **Testing:** Pytest / Gtest

## Coding Standards & Conventions
*   Model Relational Operators as immutable tree nodes. Applying a rewrite rule should return a new tree rather than modifying the original tree in place.
*   Clearly document formula derivations used in join selectivity calculations.
*   Format physical query plans as readable ASCII trees showing calculated costs (e.g., cardinality, cost estimation score) for debugging.

## Workflow Rules & Commands
*   **Run Optimization Tests:** `pytest tests/`
*   **Optimize SQL Query:** `python optimize.py --sql "SELECT name FROM users JOIN logs ON users.id = logs.user_id WHERE users.age > 30"`
