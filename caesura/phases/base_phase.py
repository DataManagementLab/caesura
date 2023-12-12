from abc import ABC, abstractmethod
from copy import copy
import logging

from caesura.observations import ExecutionError, Observation, PlanFinished

logger = logging.getLogger(__name__)

class Phase(ABC):
    is_step_by_step = False

    def __init__(self, llm, database, max_num_errors=5):
        self.llm = llm
        self.database = database
        self.previous = None
        self.next = None
        self.observation = None
        self.max_num_errors = max_num_errors
        self.num_errors = 0
        self.chat_history = None

    def collect_observation(self, observation):
        if self.observation is None:
            self.observation = observation

    def run(self, **state):
        state = copy(state)
        if self.chat_history is None:
            self.chat_history = self.init_chat(**state)
        if self.observation is not None:
            if not self.observation.handled or not isinstance(self.observation, ExecutionError):
                self.chat_history = self.handle_observation(observation=self.observation,
                                                            chat_history=self.chat_history, **state)
            else:
                self.chat_history = self.reinit_chat(observation=self.observation,
                                                     chat_history=self.chat_history, **state)
            self.set_handled()

        execution_out = self._execute(chat_history=self.chat_history, **state)
        self.chat_history = execution_out.chat_history
        return execution_out.state_update

    def set_handled(self):
        if not self.observation.handled:
            x = self
            while x is not None:
                if x.observation is None:
                    break
                x.observation.handled = True
                x = x.next
        self.observation = None

    def _execute(self, **kwargs):
        try:
            execution_out = self.execute(**kwargs)
        except PlanFinished as o:
            raise o
        except Observation as o:
            if self.is_step_by_step:
                o.set_step_number(kwargs["step_nr"])
            self.num_errors += int(isinstance(o, ExecutionError))
            logger.info(f"So far {self.num_errors} of a maximum of {self.max_num_errors} errors occurred in {type(self).__name__}.")
            if self.num_errors > self.max_num_errors:
                raise RuntimeError("Too many errors. Retry.")
            raise o
        assert isinstance(execution_out, ExecutionOutput)
        return execution_out

    @abstractmethod
    def init_chat(self, **kwargs):
        pass

    @abstractmethod
    def reinit_chat(self, observation, chat_history, **kwargs):
        pass

    @abstractmethod
    def execute(self, **kwargs):
        pass

    @abstractmethod
    def handle_observation(self, observation, **kwargs):
        pass


class ExecutionOutput():
    def __init__(self, state_update, chat_history):
        self.state_update = state_update
        self.chat_history = chat_history


class EndPhase():
    def __init__(self, previous):
        self.previous = previous
        self.observation = None
        self.next = None


class PhaseList():
    def __init__(self, *phases, reset_on_error=True):
        for i, p in enumerate(phases):
            p.previous = phases[i - 1] if i - 1 > -1 else None
            p.next = phases[i + 1] if i + 1 < len(phases) else EndPhase(p)
        self.current_phase = phases[0]
        self.reset_on_error = reset_on_error

    def get_next_phase(self, proceed_to_next_phase=True):
        if proceed_to_next_phase:
            self.current_phase = self.current_phase.next
        if isinstance(self.current_phase, EndPhase):
            return None
        return self.current_phase
    
    def collect_observation(self, observation):
        if observation.target_phase is not None:
            while not isinstance(self.current_phase, observation.target_phase):
                self.current_phase.collect_observation(observation)
                self.current_phase = self.current_phase.previous
        self.current_phase.collect_observation(observation)

    def run(self, **state):
        state["step_nr"] = 1
        proceed_to_next_phase = False
        while (phase := self.get_next_phase(proceed_to_next_phase)) != None:
            try:
                result = phase.run(**state)
                state.update(result)
                proceed_to_next_phase = True
            except PlanFinished as o:
                print(o)
                return state["plan"]
            except ExecutionError as o:
                if self.reset_on_error:
                    self.current_phase.database.clear_working_set()
                    state["step_nr"] = 1
                else:
                    state["step_nr"] += 1
                self.collect_observation(o)
                proceed_to_next_phase = False
            except Observation as o:
                state["step_nr"] += 1
                self.collect_observation(o)
                proceed_to_next_phase = False
