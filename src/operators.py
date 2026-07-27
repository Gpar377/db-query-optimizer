class Operator:
    def print_tree(self, indent: int = 0) -> str:
        raise NotImplementedError

class Scan(Operator):
    def __init__(self, table_name: str, columns: list):
        self.table_name = table_name
        self.columns = columns

    def print_tree(self, indent: int = 0) -> str:
        space = "  " * indent
        return f"{space}Scan({self.table_name}, cols={self.columns})\n"

    def __repr__(self):
        return f"Scan({self.table_name})"

class Filter(Operator):
    def __init__(self, condition: str, child: Operator):
        # condition is e.g. "age > 30" or "users.id = 5"
        self.condition = condition
        self.child = child

    def print_tree(self, indent: int = 0) -> str:
        space = "  " * indent
        res = f"{space}Filter(cond='{self.condition}')\n"
        res += self.child.print_tree(indent + 1)
        return res

    def __repr__(self):
        return f"Filter({self.condition}, {self.child})"

class Project(Operator):
    def __init__(self, columns: list, child: Operator):
        self.columns = columns
        self.child = child

    def print_tree(self, indent: int = 0) -> str:
        space = "  " * indent
        res = f"{space}Project(cols={self.columns})\n"
        res += self.child.print_tree(indent + 1)
        return res

    def __repr__(self):
        return f"Project({self.columns}, {self.child})"

class Join(Operator):
    def __init__(self, left_col: str, right_col: str, left: Operator, right: Operator):
        # Join condition: e.g. users.id = logs.user_id
        self.left_col = left_col
        self.right_col = right_col
        self.left = left
        self.right = right

    def print_tree(self, indent: int = 0) -> str:
        space = "  " * indent
        res = f"{space}Join(cond='{self.left_col} = {self.right_col}')\n"
        res += self.left.print_tree(indent + 1)
        res += self.right.print_tree(indent + 1)
        return res

    def __repr__(self):
        return f"Join({self.left_col} = {self.right_col}, {self.left}, {self.right})"
