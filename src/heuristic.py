from .operators import Operator, Scan, Filter, Project, Join

class HeuristicOptimizer:
    def optimize(self, op: Operator) -> Operator:
        """Apply predicate and projection pushdowns recursively (immutable tree transformations)."""
        op = self.push_down_predicates(op)
        op = self.push_down_projections(op)
        return op

    def push_down_predicates(self, op: Operator) -> Operator:
        """Push filters down past joins to reduce row counts early."""
        if isinstance(op, Filter):
            cond = op.condition
            child = self.push_down_predicates(op.child)
            
            # Case 1: Filter on top of a Join: try to push down
            if isinstance(child, Join):
                left_cols = self.get_referenced_columns(child.left)
                right_cols = self.get_referenced_columns(child.right)
                ref_cols = self.get_condition_columns(cond)

                # If all columns in condition belong to left child
                if all(col in left_cols for col in ref_cols):
                    pushed_left = Filter(cond, child.left)
                    return Join(child.left_col, child.right_col, pushed_left, child.right)
                
                # If all columns in condition belong to right child
                if all(col in right_cols for col in ref_cols):
                    pushed_right = Filter(cond, child.right)
                    return Join(child.left_col, child.right_col, child.left, pushed_right)
                
            return Filter(cond, child)

        elif isinstance(op, Join):
            return Join(op.left_col, op.right_col, 
                        self.push_down_predicates(op.left), 
                        self.push_down_predicates(op.right))

        elif isinstance(op, Project):
            return Project(op.columns, self.push_down_predicates(op.child))

        return op

    def push_down_projections(self, op: Operator) -> Operator:
        """Push projections down to eliminate unused columns early."""
        if isinstance(op, Project):
            cols = op.columns
            child = self.push_down_projections(op.child)

            if isinstance(child, Filter):
                # Push past Filter: Project(cols, Filter(cond, grandchild)) -> Filter(cond, Project(cols + cond_cols, grandchild))
                cond_cols = self.get_condition_columns(child.condition)
                required_cols = list(set(cols + cond_cols))
                return Filter(child.condition, Project(required_cols, child.child))

            elif isinstance(child, Join):
                # Push past Join: split columns between left and right join inputs
                left_ref = self.get_referenced_columns(child.left)
                right_ref = self.get_referenced_columns(child.right)
                
                # Ensure join key columns are retained
                required_cols = cols + [child.left_col, child.right_col]
                
                left_proj = [c for c in required_cols if c in left_ref]
                right_proj = [c for c in required_cols if c in right_ref]

                new_left = Project(left_proj, child.left) if left_proj else child.left
                new_right = Project(right_proj, child.right) if right_proj else child.right
                return Join(child.left_col, child.right_col, new_left, new_right)

            return Project(cols, child)

        elif isinstance(op, Join):
            return Join(op.left_col, op.right_col, 
                        self.push_down_projections(op.left), 
                        self.push_down_projections(op.right))

        elif isinstance(op, Filter):
            return Filter(op.condition, self.push_down_projections(op.child))

        return op

    def get_referenced_columns(self, op: Operator) -> list:
        """Returns all column references present under this operator subtree."""
        if isinstance(op, Scan):
            return op.columns
        elif isinstance(op, Filter):
            return self.get_referenced_columns(op.child)
        elif isinstance(op, Project):
            return op.columns
        elif isinstance(op, Join):
            return self.get_referenced_columns(op.left) + self.get_referenced_columns(op.right)
        return []

    def get_condition_columns(self, condition: str) -> list:
        """Extract columns referenced in a basic comparison string (e.g. 'users.id = 5' -> ['users.id'])."""
        parts = condition.split()
        cols = []
        for p in parts:
            if '.' in p: # Column identifier like users.id
                cols.append(p)
            elif p.isidentifier() and p not in ('AND', 'OR', 'NOT', 'NULL'):
                cols.append(p)
        return cols
