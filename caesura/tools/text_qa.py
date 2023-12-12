import re
from caesura.database.database import Database, Table
from caesura.tools.backend.text_qa import TextQA
from caesura.tools.base_tool import BaseTool
import logging

from caesura.observations import ExecutionError
from caesura.utils import convert

logger = logging.getLogger(__name__)

# aggregations = {
#     "highest": "maximum",
#     "lowest": "minimum",
#     "maximum": "maximum",
#     "minimum": "minimum",
#     "median": "median",
#     "average": "mean",
#     "mean": "mean",
#     "earliest": "minimum",
#     "latest": "maximum"
# }


MAX_NUM_TEXTS = 200


class TextQATool(BaseTool):
    name = "Text Question Answering"
    description = (
        "It is useful for when you want to extract information from texts inside of columns of TEXT datatype. It is Data-GPTs way of reading texts. "
        "Four input arguments: (name of column with TEXT datatype; name of new column; question_template; datatype), "
        "e.g. (patient_report; diagnosis; What is the diagnosis of <patient_name>?; string), where 'patient_name' is a column from the same table as patient_report. "
        "The question_template can be anything that can be answered by reading a text. Importantly, the question_template is a template, and must reference columns from the same table in <>. The values from this column will then be inserted into the question. "
        "The tool will automatically convert the extracted information to the specified datatype [should be one of string, int, float, date, boolean]. "
        "The tool adds a new column to the table with the extracted information (e.g. [fever, sore throat, ...]) from each individual text.\n"
    )
    args = ("name of column with TEXT datatype", "name of new column", "question_template", "datatype to automatically cast the result column to [string, int, float, date, boolean]")

    def __init__(self, database: Database):
        super().__init__(database)
        self.extractor = TextQA()

    def run(self, tables, input_args, output):
        """Use the tool."""
        table = tables[0]
        column, new_column, query, datatype = tuple(input_args)
        if "." in column:
            table, column = column.split(".")
        texts = self.database.get_column_values(table, column, force_datatype="TEXT")
        # query = self.handle_aggregations(query)

        queries = self.get_queries(table, query)
        result = self.extractor.extract(texts[:MAX_NUM_TEXTS], queries[:MAX_NUM_TEXTS])
        result = convert(result, datatype)
        ds = self.database.get_table_by_name(table)
        df = ds.data_frame[:MAX_NUM_TEXTS].copy()
        # Replace spaces and remove special characters
        df[new_column] = result
        result = Table(output if output is not None else table, df,
                       f"Result of text_qa: table={table}, column={column}, query={query}",
                       parent=ds)

        # Add the result to the working memory
        return self.database.register_working_memory(result, peek=[new_column])

    # def handle_aggregations(self, query):
    #     for a in aggregations:
    #         if a in query:
    #             query = " ".join(q for q in query.split() if q not in aggregations)
    #     return query

    def get_queries(self, table, query):
        placeholders = [x for x in re.findall("<(.+)>", query)]
        missing = ", ".join(set(placeholders) - set(self.database.tables[table].data_frame.columns))
        if missing:
            raise ExecutionError(description=f"Missing column(s) {missing} from template placeholder in the table {table}. Maybe rearrange the plan to join first.")
        
        def format_query(row):
            result = query
            for p in placeholders:
                result = result.replace(f"<{p}>", row[p])
            return result

        queries = self.database.tables[table].data_frame.apply(format_query, axis=1)
        return queries
