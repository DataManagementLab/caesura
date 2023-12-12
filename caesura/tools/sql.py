import re
from caesura.tools.base_tool import BaseTool

from caesura.observations import ExecutionError, Observation

class SqlTool(BaseTool):
    name = "SQL"
    description = (
        "Useful for when you want to query tables using SQL in SQLite syntax. "
        "The input to the tool is: (query referencing tables in the database). "
        "The result of the tool is the result table of the SQL query. "
        "For example if you want to combine two tables, you can join them using a SQL query. "
        "If you want to an aggregation, you can issue a SQL-Query using GROUP BY, etc.\n"
    )
    args = ("query referencing tables in the database",)

    def run(self, tables, input_args, output) -> str:
        """Use the tool."""
        try:
            sql_query = input_args[0]
            plan_step_info = {}
            if not input_args[0].lower().startswith("select"):
                update_statement = next(filter(lambda x:x.lower().startswith("update"), input_args))
                table, column, expression = re.match("UPDATE (\w+) SET (\w+) = (.*)", update_statement).groups()
                sql_query = f"SELECT *, {expression} AS {column} FROM {table}"
                plan_step_info = dict(plan_step_info=sql_query)

            sql_result = self.database.sql(output, sql_query)
            observation = self.database.register_working_memory(table=sql_result)
            observation = Observation(description=observation, **plan_step_info)
            return observation

        except Exception as e:
            err_str = "An error occurred while executing SQL."
            if "no such column" in str(e):
                col_name = str(e).split("no such column:")[1].split("\n")[0].strip().split(".")[-1]
                err_str = f"{err_str} Did you specify the wrong table? {self.database.alternatives(table_name=None, column_name=col_name, thresh=99)}"
            if "json" in str(e).lower():
                err_str = "The column is not in JSON Format. Use another tool, e.g. Text Question Answering!"
            raise ExecutionError(description=err_str, original_error=e)
    
    def validate_args(self, args):
        pass
