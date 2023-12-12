from caesura.observations import ExecutionError

class Plan(list):
    def __str__(self, without_tools=False):
        result = []
        for i, step in enumerate(self):
            result.append(f"Step {i + 1}: {step.__str__(without_tools=without_tools)}")
        return "\n".join(result)

    def final_format(self, query):
        result = []
        result.append(f"Query: {query}\n")
        for i, step in enumerate(self):
            result.append(f"Step {i + 1}: {step.final_format()}")
        return "\n".join(result)
    
    def without_tools(self):
        return self.__str__(without_tools=True)


class PlanStep():
    def __init__(self, description, available_tables):
        self.description = description
        self.input_tables = []
        self.output_table = None
        self.new_columns = []
        self.tool_execs = []
        self.available_tables = available_tables
        self.execution_info = None

    def set_execution_info(self, execution_info):
        self.execution_info = execution_info

    def set_input(self, input_tables):
        self.input_tables = [x.strip() for x in input_tables]
        self.input_tables = [x for x in self.input_tables if x != "N/A"]
        for t in self.input_tables:
            if t not in self.available_tables:
                raise ExecutionError(description=f"Table {t} does not exist! Use correct table names. "
                                     f"These tables are available: {list(self.available_tables)}.")

    def set_output(self, output_table):
        self.output_table = output_table

    def set_new_columns(self, new_columns):
        self.new_columns = [x.strip() for x in new_columns]

    def set_tool_calls(self, tool_execs):
        self.tool_execs = tool_execs

    def __str__(self, without_tools=False, without_output=False):
        result = self.description
        if len(self.input_tables) > 1:
            step_str = ", ".join(self.input_tables)
            result += f" The input to this step are the {step_str} tables."
        if len(self.input_tables) == 1:
            result += f" The input to this step is the '{self.input_tables[0]}' table."
        new_columns_table = "" if self.output_table is not None else f"'{self.input_tables[0]}' " 
        if len(self.new_columns) > 1:
            step_str = ", ".join(self.new_columns)
            result += f" The operation should add new {step_str} columns to the {new_columns_table}table."
        if len(self.new_columns) == 1:
            result += f" The operation should add a new '{self.new_columns[0]}' column to the {new_columns_table}table."
        if self.output_table is not None and not without_output:
            result += f" The output of the operation will be referenced by '{self.output_table}'."
        if len(self.tool_execs) and not without_tools:
            result += f" These tools are used for execution: {self.tool_execs}."
        return result
    
    def without_tools(self):
        return self.__str__(without_tools=True)

    def final_format(self):
        result = self.description + "\n"
        if len(self.new_columns) >= 1:
            step_str = ", ".join(self.new_columns)
            result += f"New Column(s): {step_str}.\n"
        if self.output_table is not None:
            result += f"Output: {self.output_table}.\n"
        for call in self.tool_execs:
            result += f"Operator: {call.tool.name}{call.args}.\n"
        return result

    def get_step_prompt(self):
        return self.__str__(without_tools=True, without_output=True)


class ToolExecutions(list):
    def __str__(self):
        result = []
        for call in self:
            args = "; ".join(call.args)
            result.append(f"{call.tool.name}({args})")
        return ", ".join(result)


class ToolExecution:
    def __init__(self, tool, args):
        self.tool = tool
        self.args = args
        self.tool.validate_args(args)
