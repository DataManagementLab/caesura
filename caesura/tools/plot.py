from pathlib import Path
from typing import Optional
import seaborn as sns
from matplotlib import pyplot as plt
from caesura.database.database import Database
from caesura.tools.base_tool import BaseTool
from caesura.observations import ExecutionError
import logging


logger = logging.getLogger(__name__)

class PlottingTool(BaseTool):
    name = "Plot"
    description = (
        "Plot the results, if the user asks for a plot. Three input arguments "
        "(Type of Plot [scatter, line, bar]; column on x axis; column on y axis). "
        "Unfortunately, is it not possible to customize the labels, color, title, axes etc.\n"
    )
    args = ("Type of Plot [scatter, line, bar]", "column on x axis", "column on y axis")

    def __init__(self, database: Database, interactive: bool, log_path: Optional[Path]):
        super().__init__(database)
        self.interactive = interactive
        self.log_path = log_path

    def run(self, tables, input_args, output):
        """Use the tool."""
        table = tables[0]
        plot_type, col_x, col_y = tuple(input_args)
        try:
            if plot_type == "line":
                sns.lineplot(data=self.database.get_table_by_name(table).data_frame,
                            x=col_x, y=col_y, marker="X")
            if plot_type == "scatter":
                sns.scatterplot(data=self.database.get_table_by_name(table).data_frame,
                                x=col_x, y=col_y)
            if plot_type == "bar":
                sns.barplot(data=self.database.get_table_by_name(table).data_frame,
                            x=col_x, y=col_y)
        except Exception as e:
            logger.warning(e, exc_info=True)
            raise ExecutionError(description="An error occurred while plotting", original_error=e)

        plt.xticks(rotation=90)
        plt.savefig(Path(self.log_path if self.log_path is not None else ".") / "plot-out.png", bbox_inches="tight")
        if self.interactive:
            plt.show()
            if next(iter(input("\nIs the created plot fine (Y, n)?")), "y").lower() != "y":
                raise ExecutionError(description="I don't like the final plot! This should be improved: "
                                    + input("\nWhat can be improved? > ") + ".", add_step_nr=False)
        return "Plot created successfully!"
