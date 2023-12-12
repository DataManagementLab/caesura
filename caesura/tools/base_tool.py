from abc import ABC, abstractmethod

from caesura.observations import ExecutionError

class BaseTool(ABC):
    def __init__(self, database):
        super().__init__()
        self.database = database
        assert hasattr(type(self), "args")
        assert hasattr(type(self), "name")
        assert hasattr(type(self), "description")

    @abstractmethod
    def run(self, tables, input_args, output) -> str:
        pass

    def validate_args(self, args):
        if len(args) != len(self.args):
            raise ExecutionError(
                description=f"Expected {len(self.args)} argument(s) for {self.name} tool. "
                f"Please specify these arguments: ({'; '.join(self.args)})")
