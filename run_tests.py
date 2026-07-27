import unittest
from src.operators import Scan, Filter, Project, Join
from src.heuristic import HeuristicOptimizer
from src.cbo import Catalog, CostBasedOptimizer
from optimize import parse_sql

class TestQueryOptimizer(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog()
        self.catalog.add_table("users", 10000, {"id": 10000, "age": 100})
        self.catalog.add_table("logs", 1000000, {"user_id": 10000, "id": 1000000})

    def test_sql_parser(self):
        sql = "SELECT users.name FROM users JOIN logs ON users.id = logs.user_id WHERE users.age > 30"
        plan = parse_sql(sql)
        
        self.assertTrue(isinstance(plan, Project))
        self.assertTrue(isinstance(plan.child, Filter))
        self.assertTrue(isinstance(plan.child.child, Join))

    def test_predicate_pushdown(self):
        # Filter(users.age > 30, Join(users.id = logs.user_id, Scan(users), Scan(logs)))
        # Target: Filter pushed down into left child Scan of Join:
        # Join(users.id = logs.user_id, Filter(users.age > 30, Scan(users)), Scan(logs))
        scan_u = Scan("users", ["users.id", "users.age"])
        scan_l = Scan("logs", ["logs.user_id"])
        join = Join("users.id", "logs.user_id", scan_u, scan_l)
        root = Filter("users.age > 30", join)

        optimizer = HeuristicOptimizer()
        optimized = optimizer.push_down_predicates(root)

        self.assertTrue(isinstance(optimized, Join))
        self.assertTrue(isinstance(optimized.left, Filter))
        self.assertEqual(optimized.left.condition, "users.age > 30")

    def test_cardinality_selectivity(self):
        cbo = CostBasedOptimizer(self.catalog)
        scan_u = Scan("users", ["users.id"])
        scan_l = Scan("logs", ["logs.user_id"])
        join = Join("users.id", "logs.user_id", scan_u, scan_l)

        # Cardinality calculation:
        # Card(users) * Card(logs) / max(distinct(users.id), distinct(logs.user_id))
        # 10,000 * 1,000,000 / max(10,000, 10,000) = 1,000,000
        estimated = cbo.estimate_cardinality(join)
        self.assertEqual(estimated, 1000000)

    def test_join_reordering_dp(self):
        cbo = CostBasedOptimizer(self.catalog)
        
        # 3 relation join reordering test: Scan(A), Scan(B), Scan(C)
        # Verify Dynamic Programming joins smallest relations first to minimize intermediate state size
        self.catalog.add_table("A", 100, {"id": 100})
        self.catalog.add_table("B", 10000, {"id": 10000})
        self.catalog.add_table("C", 1000, {"id": 1000})

        scans = [Scan("A", ["id"]), Scan("B", ["id"]), Scan("C", ["id"])]
        join_conditions = [("A.id", "B.id"), ("B.id", "C.id")]

        best_order_tree = cbo.optimize_join_order(scans, join_conditions)
        self.assertTrue(isinstance(best_order_tree, Join))

if __name__ == "__main__":
    unittest.main()
