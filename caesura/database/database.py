import logging
from caesura.database.index import RelevantValueIndex
from caesura.database.table import Table
from pathlib import Path
from fuzzywuzzy import fuzz
from pandasql import sqldf
import sqlparse

from caesura.observations import ExecutionError


logger = logging.getLogger(__name__)

class Link():
    def __init__(self, table1, table2, column1, column2):
        """Initializes a link between two tables."""
        self.table1 = table1
        self.table2 = table2
        self.column1 = column1
        self.column2 = column2

    def __str__(self) -> str:
        return f"{self.table1.name}.{self.column1} -> {self.table2.name}.{self.column2}"

    def __repr__(self) -> str:
        return str(self)


class Database():
    def __init__(self):
        """Initializes a database."""
        self._tables = {}
        self._working_set = {}
        self._relevant_values_indexes = {}
        self.history = list()

    @property
    def tables(self):
        return {**self._tables, **self._working_set}

    def clear_working_set(self):
        self.history = list()
        self._working_set = {}
        logger.info("Working set cleared!", stack_info=True)

    def final_result(self):
        if self.history:
            return self._working_set[self.history[-1]]

    def get_table_by_name(self, name: str):
        """Returns a table by name."""
        if name in self._tables:
            return self._tables[name]
        if name in self._working_set:
            return self._working_set[name]
        raise ValueError(f"table {name} not found. " + self.alternatives(name))

    def register_working_memory(self, table, peek=False):
        """Registers a table as working memory."""
        if len(table.data_frame) == 0:
            raise ExecutionError(description="Empty table encountered. Check your filter or join conditions.")
        self.history.append(table.name)
        self._working_set[table.name] = table
        added_str = f"Table {table.name} has been added."
        rows_str = f"The table {table.name} has {table.data_frame.shape[0]} rows."
        columns_str = f"The table {table.name} has these columns: {table.data_frame.columns.tolist()}"
        logger.debug(f"Added {table.name}:\n{table.data_frame}")
        if peek and isinstance(peek, list):
            return f"{added_str}\nNew column(s):\n{self.peek_table(table, columns=peek)}\n{columns_str}\n{rows_str}"
        elif peek is True:
            return f"{added_str}\n{table.name}:\n{self.peek_table(table)}\n{rows_str}"
        else:
            return f"{added_str}\n{columns_str}\n{rows_str}"

    def add_image_table(self, name: str, path: Path, description: str, file_paths=()):
        """Adds an image table to the database."""
        self._tables[name] = Table.create_image_table(name, path, description, file_paths=file_paths)

    def add_text_table(self, name: str, path: Path, description: str):
        """Adds a text table to the database."""
        self._tables[name] = Table.create_text_table(name, path, description)

    def add_tabular_table(self, name: str, path: Path, description: str, path_columns=()):
        """Adds a tabular table to the database."""
        self._tables[name] = Table.create_tabular_table(name, path, description, path_columns)

    def build_relevant_values_index(self, table, *columns):
        for c in columns:
            values = self.tables[table].data_frame[c].unique()
            self._relevant_values_indexes[table, c] = RelevantValueIndex()
            self._relevant_values_indexes[table, c].build(values)

    def get_relevant_values(self, table, column, keywords="", num=10):
        if (table, column) in self._relevant_values_indexes:
            return self._relevant_values_indexes[table, column].get_relevant_values(*keywords, num=10)
        return self.tables[table].data_frame[column][:num].tolist()

    def has_relevant_values_index(self, table, column):
        return (table, column) in self._relevant_values_indexes

    def _link(self, table1, table2, column1, column2):
        """Links a tabular table to another table."""
        table1.add_link(Link(table1, table2, column1, column2))

    def link_image(self, tabular_table, image_table, column):
        """Links an tabular table to an image table."""
        self._link(self._tables[tabular_table],
                  self._tables[image_table],
                  column1=column, column2="img_path")

    def link_text(self, tabular_table, text_table, column):
        """Links an tabular table to a text table."""
        self._link(self._tables[tabular_table],
                  self._tables[text_table],
                  column1=column, column2="txt_path")

    def link(self, tabular_table1, tabular_table2, column1, column2=None):
        """Links two tabular tables."""
        self._link(self._tables[tabular_table1],
                  self._tables[tabular_table2],
                  column1=column1, column2=column2 or column1)

    def describe(self):
        """Describes the database."""
        result = "The database contains the following tables:\n"
        for _, table in self._tables.items():
            result += table.describe() + "\n"
        result += "\n"
        result += "A column with the IMAGE datatype stores images. "
        result += "A column with the TEXT datatype stores long text.\n"
        return result + "\n"

    def peek_table(self, table, num_rows=5, max_num_rows=10, columns=None, example_text=False):
        """Peeks at a table."""
        df = table.data_frame
        datatypes = [table.get_datatype_for_column(c) for c in columns or table.get_columns()]
        method = "key-value"
        if columns:
            df = df[columns]
            method = "markdown"
        ds_num_rows = len(df)
        if ds_num_rows > max_num_rows:
            result =  self.serialize(df.head(num_rows), datatypes=datatypes, method=method, example_text=example_text)
            if ds_num_rows > num_rows:
                result += f"\n and {ds_num_rows - num_rows} more rows. \n"
        else:
            result = self.serialize(df, datatypes=datatypes, method=method, example_text=example_text)
        return result

    def serialize(self, df, datatypes, method="markdown", example_text=True):
        df_orig = df
        df = df.copy()
        example_texts = {}
        for c, dt, in zip(df.columns, datatypes):
            if dt == "TEXT":
                df[c] = df[c].apply(lambda _: "<TEXT>")
                example_texts[c] = " ".join(df_orig[c].iloc[0].split()[:200]) + " ..."

        result = ""
        if method == "key-value":
            result = []
            for _, row in df.iterrows():
                row_serialized = " | ".join(f"{c}: {v}" for c, v in zip(df.columns, row))
                result.append(row_serialized)
            result = "\n".join(result)
        elif method == "markdown":
            result = df.to_markdown()
        else:
            raise ValueError("Unknown serialization methods.")

        if example_text and example_texts:
            result += "\n\nExample texts for columns of TEXT datatype. Data-GPT is able to process these and to extract relevant information in structured form:\n" + \
                "\n".join(f"Column '{k}': {v}" for k, v in example_texts.items())
        return result

    def peek(self, table_name, *args, **kwargs):
        """Peeks at a table."""
        return self.peek_table(self.tables[table_name], *args, **kwargs)

    def sql(self, result_name, query):
        """Executes an SQL query on the database."""
        result = sqldf(query, {k: v.data_frame for k, v in self.tables.items()})
        cols = []
        remove = False
        for c in result.columns:
            if c in cols:
                cols.append("--to-be-removed--")
                remove = True
            else:
                cols.append(c)
        result.columns = cols
        if remove:
            result.drop("--to-be-removed--", axis=1, inplace=True)
        mentioned_tables = [x.normalized.split(".")[0] for x in sqlparse.parse(query)[0].tokens
                              if isinstance(x, sqlparse.sql.Identifier)]
        mentioned_tables = [n for n in mentioned_tables if n in self.tables]
        image_columns = tuple(c for d in mentioned_tables for c in self.get_table_by_name(d).image_columns
                              if c in result.columns)
        text_columns = tuple(c for d in mentioned_tables for c in self.get_table_by_name(d).text_columns
                             if c in result.columns)
        result = Table(result_name, result, f"Result of SQL query: {query}",
                         image_columns=image_columns, text_columns=text_columns)
        return result

    def get_column_values(self, table_name, column_name, force_datatype=None):
        """Gets the values of a column."""
        if table_name not in self.tables:
            raise ExecutionError(description=f"table {table_name} not found. "
                                 + self.alternatives(table_name, column_name, force_datatype))
        if column_name not in self.tables[table_name].data_frame.columns:
            raise ExecutionError(description=f"Column {column_name} not found in table {table_name}. "
                                 + self.alternatives(table_name, column_name, force_datatype))

        is_datatype = self.tables[table_name].get_datatype_for_column(column_name)
        if force_datatype is not None and force_datatype != is_datatype:
            raise ExecutionError(
                    description=f"Column {column_name} is of type {is_datatype}, "
                                f"but selected tool requires {force_datatype}. "
                                " Consider choosing a different tool!"
                )
        return self.tables[table_name].data_frame[column_name].values

    def get_column_datatype(self, table_name, column_name):
        """Gets the values of a column."""
        if table_name not in self.tables:
            raise ValueError(f"table {table_name} not found. "
                             + self.alternatives(table_name, column_name))
        if column_name not in self.tables[table_name].data_frame.columns:
            raise ValueError(f"Column {column_name} not found in table {table_name}. "
                             + self.alternatives(table_name, column_name))
        return self.tables[table_name].get_datatype_for_column(column_name)

    def alternatives(self, table_name, column_name=None, force_datatype=None, num_suggestions=3, thresh=0):
        """Returns a list of alternatives for a column."""
        suggested = []
        for table_similarity, table in ((fuzz.ratio(n, table_name), d) for n, d in self.tables.items()):
            if column_name is None:
                suggested.append((table_similarity, table.name))
                continue

            for column_similarity, column in ((fuzz.ratio(c, column_name), c) for c in table.data_frame.columns):
                if force_datatype is None or force_datatype == table.get_datatype_for_column(column):
                    suggested.append(((table_similarity + column_similarity), f"{table.name}.{column}"))
        final_suggestions = [x for s, x in sorted(suggested)[::-1]  if s > thresh][:num_suggestions]
        if final_suggestions:
            return "Did you mean any of: " + ", " .join(final_suggestions)
        return ""

    def register_tool(self, tool):
        """Registers a tool."""
        if hasattr(tool, "on_ingest"):
            for table in self._tables.values():
                tool.on_ingest(table, 0, len(table.data_frame))
        if hasattr(tool, "persist"):
            tool.persist()

