from pathlib import Path
import langchain
import logging
from caesura.model import MyOpenAI
from caesura.phases import PlanningPhase, DiscoveryPhase, MappingPhase, MappingPhase
from langchain.cache import SQLiteCache
from caesura.phases.base_phase import PhaseList
from caesura.phases.runner import RunnerPhase
from caesura.scenarios import get_database
from caesura.tools import ImageSelectTool, SqlTool, TransformTool, VisualQATool, PlottingTool
from caesura.tools.noop import NoopTool
from caesura.tools.text_qa import TextQATool

langchain.llm_cache = SQLiteCache(database_path=".langchain.db")
logger = logging.getLogger(__name__)



MAX_NUM_RETRIES = {
    "gpt-3.5-turbo-0613": 3,
    "gpt-4-0613": 1
}

MAX_NUM_ERRORS = {
    "gpt-3.5-turbo-0613": 5,
    "gpt-4-0613": 3
}

class Caesura():
    def __init__(self, database, model_name="gpt-3.5-turbo-0613", interactive=True, log_path=None):
        self.database = database
        self.interactive = interactive
        self.working_memory = dict()
        self.llm = MyOpenAI(temperature=0, model_name=model_name, max_tokens=1024, logging_dir=log_path or ".")
        self.phases = list()
        self.tools = list()
        self.max_num_tries = MAX_NUM_RETRIES[model_name]
        self.max_num_errors = MAX_NUM_ERRORS[model_name]
        self.log_path = log_path
        self.file_handler = None

        # setup
        self.setup_logging()
        self.setup_tools()
        self.setup_phases()

    def setup_logging(self):
        if self.log_path is not None:
            for handler in logging.root.handlers:
                handler.level = logging.root.level
            self.log_path.mkdir(exist_ok=True, parents=True)
            self.file_handler = logging.FileHandler(self.log_path / 'out.log')
            logging.root.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.file_handler.setFormatter(formatter)
            logging.root.addHandler(self.file_handler)

    def setup_tools(self):
        self.tools = list()
        self.tools.append(ImageSelectTool(self.database))
        self.tools.append(VisualQATool(self.database))
        self.tools.append(SqlTool(self.database))
        self.tools.append(TransformTool(self.database, self.llm, self.interactive))
        self.tools.append(PlottingTool(self.database, self.interactive, self.log_path))
        self.tools.append(TextQATool(self.database))
        self.tools.append(NoopTool(self.database))
        for tool in self.tools:
            self.database.register_tool(tool)

    def setup_phases(self):
        self.phases = PhaseList(
            DiscoveryPhase(llm=self.llm, database=self.database, max_num_errors=self.max_num_errors),
            PlanningPhase(llm=self.llm, database=self.database, max_num_errors=self.max_num_errors),
            MappingPhase(llm=self.llm, database=self.database, max_num_errors=self.max_num_errors),
            RunnerPhase(llm=self.llm, database=self.database, max_num_errors=self.max_num_errors),
            reset_on_error=True
        )

    def run(self, query):
        query = query.strip().strip(".")
        error = None
        num_tries = 0
        final_plan = None
        final_result = None
        while num_tries < self.max_num_tries:
            try:
                final_plan = self.phases.run(query=query, tools=self.tools)
                error = None
                break
            except RuntimeError as e:
                error = self.restart_after_error(e)
            except Exception as e:
                if self.interactive:
                    raise e
                error = self.restart_after_error(e)
            finally:
                num_tries += 1
                final_result = self.database.final_result()
                self.database.clear_working_set()

        if error is not None:
            logging.root.removeHandler(self.file_handler)
            if self.interactive:
                raise error
            return
        self.log_final_plan(query, final_plan, final_result)

    def restart_after_error(self, e):
        logger.warning(e, exc_info=True)
        self.setup_tools()
        self.setup_phases()
        error = e
        self.llm = MyOpenAI(temperature=self.llm.temperature + 0.2,
                            model_name=self.llm.model_name, max_tokens=1024)
        return error

    def log_final_plan(self, query, final_plan, final_result):
        plan_str = final_plan.final_format(query)
        print()
        print(plan_str)
        result_str = final_result.data_frame.to_markdown() if final_result is not None else None
        print()
        print(result_str)

        if self.log_path is not None:
            path = Path(self.log_path) / "final-plan.log" 
            with open(path, "w") as f: 
                print(plan_str, file=f)

            if result_str is not None:
                path = Path(self.log_path) / "final-result.log"
                with open(path, "w") as f: 
                    print(result_str, file=f)
        logging.root.removeHandler(self.file_handler)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)


    model = {"3": "gpt-3.5-turbo-0613", "4": "gpt-4-0613"}[input("Model (GPT-3/GPT-4): GPT-").strip()]
    dataset_name = input("Dataset (artwork/rotowire): ").strip()
    dl = get_database(dataset_name, sampled=False)
    agent = Caesura(dl, model_name=model, interactive=False)
    agent.run(input("Query : ").strip())

    # agent.run("For every player, what is the highest number of points they scored in a game?")
    # agent.run("Plot the number religious artworks from each century.")
    # agent.run("Plot the average number of persons depicted in the paintings of each genre.")
    # agent.run("Plot the number of paintings that depict Madonna and Child for each century.")

    # fake_llm_responses=[]
