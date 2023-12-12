from caesura.database.database import Database, Table
from caesura.tools.backend.image_retriever import ImageRetriever
from caesura.tools.base_tool import BaseTool

from caesura.utils import get_paths_from_images

class ImageSelectTool(BaseTool):
    name = "Image Select"
    description = (
        "It is useful for when you want to select tuples based on what is depicted in images (column with IMAGE datatype) e.g. to select all rows where the image depicts a skateboard. "
        "Two input arguments: (column with IMAGE datatype; the description to match), e.g. (image; skateboard). "
        "The tool selects the tuples where the images match the description. It will not add new columns to the table.\n"
    )
    args = ("column with IMAGE datatype", "the description to match")

    def __init__(self, database: Database):
        super().__init__(database)
        self.retriever = ImageRetriever()

    def run(self, tables, input_args, output):
        """Use the tool."""
        table = tables[0]
        column, query = tuple(input_args)
        if "." in column:
            table, column = column.split(".")
        images = self.database.get_column_values(table, column, force_datatype="IMAGE")
        paths = get_paths_from_images(images)
        result = self.retriever.retrieve(paths, query, table, column)
        image_placeholders = [f"<IMAGE stored at '{x}'>" for x in result]
        ds = self.database.tables[table]
        mask = ds.data_frame[column].isin(image_placeholders)
        result = ds.data_frame[mask]

        result = Table(output if output is not None else table, result,
                         f"Result of retrieval: table={table}, column={column}, query={query}",
                         parent=ds)

        # Add the result to the working memory
        return self.database.register_working_memory(result)

    def on_ingest(self, table, start_index, end_index):
        """Called when a new data is ingested."""
        self.retriever.on_ingest(table, start_index, end_index)

    def persist(self):
        """Persist the tool."""
        self.retriever.persist()

