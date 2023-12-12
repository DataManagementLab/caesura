from caesura.database.database import Database
from caesura.tools.base_tool import BaseTool
from copy import deepcopy


class NoopTool(BaseTool):
    name = "No Op"
    description = (
        "Does not perform any operation. Useful when you should extract a column from the table, but this column already exists. "
        "E.g. Step X: Extract name from persons --> Column name already exists in Table persons. Hence, no operation necessary.\n"
    )
    args = ()

    def __init__(self, database: Database):
        super().__init__(database)

    def run(self, tables, input_args, output):
        """Use the tool."""
        table = tables[0]
        result = self.database.get_table_by_name(table)
        if output is not None:
            result = deepcopy(result)
            result.name = output
        return self.database.register_working_memory(result)

    def validate_args(self, args):
        pass
