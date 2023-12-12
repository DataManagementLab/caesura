import re

from caesura.database.database import Database, Table
from caesura.tools.backend.image_qa import VisualQA
from caesura.tools.base_tool import BaseTool
from caesura.observations import ExecutionError
from caesura.utils import convert, get_paths_from_images


aggregations = {
    "highest": "maximum",
    "lowest": "minimum",
    "maximum": "maximum",
    "minimum": "minimum",
    "median": "median",
    "average": "mean",
    "mean": "mean"
}

MAX_NUM_IMAGES = 200


class VisualQATool(BaseTool):
    name = "Visual Question Answering"
    description = (
        "It is useful for when you want to know what is depicted on the images in a column with IMAGE datatype. It is Data-GPTs way of looking at images. "
        "The input to the tool is: (name of column with IMAGE datatype; name of new column with extracted info; question; datatype to automatically cast the result column to [string, int, float, date, boolean]), "
        "e.g. (image; breed_of_dog; What is the breed of dog?; string). "
        "The tool adds a new column to the table with the extracted information (e.g. [Poodle, Chihuahua, ...]). "
        "The question can be anything that can be answered by looking at an image: E.g. How many <x> are depicted? Is <y> depicted? What is in the background? ...\n"
    )
    args = ("name of column with IMAGE datatype", "name of new column with extracted info", "question", "datatype to automatically cast the result column to [string, int, float, date, boolean]")

    def __init__(self, database: Database):
        super().__init__(database)
        self.extractor = VisualQA()

    def run(self, tables, input_args, output):
        """Use the tool."""
        table = tables[0]
        column, new_column, query, datatype = tuple(input_args)
        if "." in column:
            table, column = column.split(".")
        query = self.handle_aggregations(query)

        images = self.database.get_column_values(table, column, force_datatype="IMAGE")
        paths = get_paths_from_images(images)
        result = self.extractor.extract(paths[:MAX_NUM_IMAGES], query)
        result = convert(result, datatype)
        ds = self.database.get_table_by_name(table)
        df = ds.data_frame[:MAX_NUM_IMAGES].copy()
        # Replace spaces and remove special characters
        df[new_column] = result
        result = Table(output if output is not None else table, df,
                       f"Result of visual_qa: table={table}, column={column}, query={query}",
                       parent=ds)

        # Add the result to the working memory
        return self.database.register_working_memory(result, peek=[new_column])

    def handle_aggregations(self, query):
        for a in aggregations:
            if a in query:
                query = " ".join(q for q in query.split() if q not in aggregations)
                if not self.error_raised:
                    self.error_raised = True
                    raise ExecutionError(
                        description=f"Question contains a {aggregations[a]} aggregation. This is not allowed. "
                        f"Replace this step by two steps: 1. Extract answer for '{query}'. "
                        f"2. Compute the {aggregations[a]}! All other steps can stay the same. Update the plan!")         
        return query
