# Toy Database Query Optimizer
A database query optimizer in C++ or Python demonstrating execution planning and query restructuring. It parses SQL-like relational queries into logical query trees, applies heuristic rewrite rules, estimates costs using statistical catalog profiles, and compiles optimized physical execution plans.

## Proposed Git Repo Name
`db-query-optimizer`

## Architecture & Scope
*   **Query Parser & AST:** A parser reading a basic subset of SQL (e.g., `SELECT`, `PROJECT`, `JOIN`, `FILTER/WHERE`).
*   **Logical Execution Plan:** Representation of relational algebraic operators:
    *   `Scan(Table)`
    *   `Filter(Predicate, Child)`
    *   `Project(Attributes, Child)`
    *   `Join(Condition, Left, Right)`
*   **Heuristic Optimizer:** Logical rewrites utilizing rules:
    *   **Predicate Pushdown:** Pushing `Filter` down past `Join` nodes to reduce data volume before joining.
    *   **Projection Pushdown:** Eliminating unused columns early.
*   **Cost-Based Optimizer (CBO):**
    *   **Catalog System:** Basic table statistics (row counts, column histograms, distinct value counts).
    *   **Cost Functions:** Calculating CPU and I/O costs for joins (Hash Join vs. Nested Loop Join vs. Sort-Merge Join).
    *   **Join Reordering:** Dynamically ordering joins using dynamic programming (System R style) to find the cheapest tree.

## Target Milestones
1. AST Parser and logical tree representation.
2. Heuristic rewrite rule processor (Predicate/Projection pushdown).
3. Statistical database catalog with cardinalities.
4. Join reordering solver using dynamic programming.
5. Physical plan generator and comparative benchmarking suite.
