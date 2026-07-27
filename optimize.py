import argparse
import sys
import re
from src.operators import Operator, Scan, Filter, Project, Join
from src.heuristic import HeuristicOptimizer
from src.cbo import Catalog, CostBasedOptimizer

def parse_sql(sql: str) -> Operator:
    """A basic SQL query parser mapping SELECT-FROM-JOIN-WHERE statements to Logical Operator Trees."""
    sql = sql.strip().replace('\n', ' ')
    
    # 1. Parse Project columns
    select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE)
    if not select_match:
        raise ValueError("Could not parse SELECT columns")
    proj_cols = [c.strip() for c in select_match.group(1).split(',')]

    # 2. Parse Tables & Joins
    from_match = re.search(r"FROM\s+(.*?)(?:\s+WHERE|$)", sql, re.IGNORECASE)
    if not from_match:
        raise ValueError("Could not parse FROM clause")
    
    from_clause = from_clause_str = from_match.group(1).strip()
    
    # Check if there is a JOIN ON clause
    join_match = re.search(r"(\w+)\s+JOIN\s+(\w+)\s+ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)", from_clause, re.IGNORECASE)
    
    if join_match:
        tbl1, tbl2, col1, col2 = join_match.groups()
        # Default scan columns to select fields + join columns
        scan_left = Scan(tbl1, [col1] + [c for c in proj_cols if c.startswith(tbl1)])
        scan_right = Scan(tbl2, [col2] + [c for c in proj_cols if c.startswith(tbl2)])
        root = Join(col1, col2, scan_left, scan_right)
    else:
        # Single table scan
        tbl = from_clause.split()[0]
        root = Scan(tbl, proj_cols)

    # 3. Parse WHERE / Filter condition
    where_match = re.search(r"WHERE\s+(.*)", sql, re.IGNORECASE)
    if where_match:
        cond = where_match.group(1).strip()
        root = Filter(cond, root)

    # 4. Project operator on top
    root = Project(proj_cols, root)
    return root

def main():
    parser = argparse.ArgumentParser(description="Relational SQL Query Optimizer Engine")
    parser.add_argument("--sql", type=str, required=True, help="SQL query to parse and optimize")
    args = parser.parse_args()

    # Configure Statistical Catalog
    catalog = Catalog()
    catalog.add_table("users", 100000, {"id": 100000, "age": 100})
    catalog.add_table("logs", 5000000, {"user_id": 100000, "id": 5000000})

    print("==================================================")
    print("Relational SQL Query Optimizer Engine")
    print("==================================================")
    print(f"Input SQL:\n  {args.sql}\n")

    try:
        # Parse AST
        logical_plan = parse_sql(args.sql)
        print("--- [Logical Execution Plan] ---")
        print(logical_plan.print_tree())

        # 1. Apply Heuristic Rule Optimizations
        heuristic_opt = HeuristicOptimizer()
        heuristic_plan = heuristic_opt.optimize(logical_plan)
        print("--- [Optimized Plan (Heuristics)] ---")
        print(heuristic_plan.print_tree())

        # 2. Evaluate Costs
        cbo = CostBasedOptimizer(catalog)
        orig_card = cbo.estimate_cardinality(logical_plan)
        orig_cost = cbo.estimate_cost(logical_plan)
        opt_card = cbo.estimate_cardinality(heuristic_plan)
        opt_cost = cbo.estimate_cost(heuristic_plan)

        print("--- [Cost Calculations] ---")
        print(f"Original Plan:  Cardinality ~ {orig_card:,} rows, Cost score ~ {orig_cost:,.2f}")
        print(f"Optimized Plan: Cardinality ~ {opt_card:,} rows, Cost score ~ {opt_cost:,.2f}")
        
        speedup = (orig_cost / opt_cost) if opt_cost > 0 else 1.0
        print(f"Plan Cost Reduction: {speedup:.2f}x improvement!")

    except Exception as e:
        print(f"Optimization failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
