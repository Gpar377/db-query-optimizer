from typing import Dict, List, Tuple
from .operators import Operator, Scan, Join

class Catalog:
    def __init__(self):
        # Table stats: { table_name: { "row_count": N, "columns": { col_name: distinct_values } } }
        self.tables = {}

    def add_table(self, name: str, row_count: int, col_stats: Dict[str, int]):
        self.tables[name] = {
            "row_count": row_count,
            "columns": col_stats
        }

    def get_row_count(self, table_name: str) -> int:
        return self.tables.get(table_name, {}).get("row_count", 1000)

    def get_distinct_values(self, table_name: str, col_name: str) -> int:
        return self.tables.get(table_name, {}).get("columns", {}).get(col_name, 100)

class CostBasedOptimizer:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def estimate_cardinality(self, op: Operator) -> int:
        """Estimate the number of rows output by this operator subtree."""
        if isinstance(op, Scan):
            return self.catalog.get_row_count(op.table_name)
        
        elif isinstance(op, Join):
            card_left = self.estimate_cardinality(op.left)
            card_right = self.estimate_cardinality(op.right)
            
            # Selectivity formula derivation:
            # Under uniform distribution and containment assumptions, the join selectivity is
            # 1 / max(distinct_values(left_col), distinct_values(right_col)).
            table_l = op.left_col.split('.')[0] if '.' in op.left_col else ""
            col_l = op.left_col.split('.')[1] if '.' in op.left_col else op.left_col
            table_r = op.right_col.split('.')[0] if '.' in op.right_col else ""
            col_r = op.right_col.split('.')[1] if '.' in op.right_col else op.right_col

            dist_l = self.catalog.get_distinct_values(table_l, col_l)
            dist_r = self.catalog.get_distinct_values(table_r, col_r)
            
            selectivity = 1.0 / max(dist_l, dist_r, 1)
            return int(card_left * card_right * selectivity)
            
        # Filters and Projects return fractional/constant estimates
        return 100

    def estimate_cost(self, op: Operator) -> float:
        """Estimate the overall processing cost score (CPU + I/O load)."""
        if isinstance(op, Scan):
            # Scan cost: proportional to row count
            return float(self.catalog.get_row_count(op.table_name))
        
        elif isinstance(op, Join):
            card_left = self.estimate_cardinality(op.left)
            card_right = self.estimate_cardinality(op.right)
            
            # Hash Join cost model:
            # Building hash table on right relation: cost proportional to card_right
            # Probing hash table from left relation: cost proportional to card_left
            join_cost = float(card_left + 2.0 * card_right)
            return join_cost + self.estimate_cost(op.left) + self.estimate_cost(op.right)
            
        return 10.0

    def optimize_join_order(self, scans: List[Scan], join_conditions: List[Tuple[str, str]]) -> Operator:
        """
        System R style Dynamic Programming join reordering solver.
        Finds the join order tree with the lowest estimated cost.
        """
        # Map of { frozen_set_of_scans: (CheapestOperatorTree, CostScore) }
        memo = {}

        # 1. Base cases: single tables
        for scan in scans:
            memo[frozenset([scan.table_name])] = (scan, self.estimate_cost(scan))

        # 2. Build combinations of increasing size
        n = len(scans)
        for length in range(2, n + 1):
            for subset in self.generate_subsets(scans, length):
                best_op = None
                best_cost = float('inf')

                # Try all possible splits of the subset
                for split_l in self.generate_splits(subset):
                    split_r = subset - split_l
                    
                    if split_l in memo and split_r in memo:
                        op_l, cost_l = memo[split_l]
                        op_r, cost_r = memo[split_r]

                        # Find matching join condition between the two subsets
                        cond = self.find_join_condition(split_l, split_r, join_conditions)
                        if cond:
                            left_col, right_col = cond
                            join_op = Join(left_col, right_col, op_l, op_r)
                            total_cost = self.estimate_cost(join_op)

                            if total_cost < best_cost:
                                best_cost = total_cost
                                best_op = join_op

                if best_op:
                    memo[subset] = (best_op, best_cost)

        final_subset = frozenset([s.table_name for s in scans])
        return memo.get(final_subset, (None, 0))[0]

    def generate_subsets(self, scans: List[Scan], length: int) -> List[frozenset]:
        import itertools
        return [frozenset(names) for names in itertools.combinations([s.table_name for s in scans], length)]

    def generate_splits(self, subset: frozenset) -> List[frozenset]:
        import itertools
        splits = []
        lst = list(subset)
        for r in range(1, len(lst)):
            for comb in itertools.combinations(lst, r):
                splits.append(frozenset(comb))
        return splits

    def find_join_condition(self, left_set: frozenset, right_set: frozenset, conditions: List[Tuple[str, str]]) -> Tuple[str, str]:
        for c1, c2 in conditions:
            tbl1 = c1.split('.')[0]
            tbl2 = c2.split('.')[0]
            if (tbl1 in left_set and tbl2 in right_set):
                return (c1, c2)
            if (tbl2 in left_set and tbl1 in right_set):
                return (c2, c1)
        return None
