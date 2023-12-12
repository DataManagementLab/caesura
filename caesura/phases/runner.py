from caesura.phases.base_phase import Phase
from caesura.observations import Observation, ExecutionError


class RunnerPhase(Phase):
    is_step_by_step = True

    def execute(self, step_nr, step, **kwargs):
        observation = None
        for i, call in enumerate(step.tool_execs):
            observation = self.tool_execute(step_nr, step, call.tool, call.args,
                                            is_first=i==0, is_last=(i == len(step.tool_execs) - 1))
        raise observation

    def tool_execute(self, step_nr, step, tool, args, is_first, is_last):
        try:
            observation = tool.run(tables=step.input_tables if is_first else ["tmp"], input_args=args,
                                   output=step.output_table if is_last else "tmp")
        except ExecutionError as e:
            e.set_target_phase(type(self.previous))
            raise e

        if isinstance(observation, Observation):
            observation.set_step_number(step_nr)
            observation.set_target_phase(type(self.previous))
            step.set_execution_info(observation.plan_step_info)
        else:
            observation = Observation(description=observation or "", step_nr=step_nr, target_phase=type(self.previous))
        return observation

    def init_chat(self, **kwargs):
        return None

    def reinit_chat(self, **kwargs):
        return None

    def handle_observation(self, observation, **kwargs):
        return None
