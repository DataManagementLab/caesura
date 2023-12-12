import datetime
from pathlib import Path
import time
import logging
from typing import Any
from openai import Completion
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate


logger = logging.getLogger(__name__)

MAX_RPM = {
    "gpt-3.5-turbo-0613": 3_500,
    "gpt-4-0613": 200
}

MAX_TPM = {
    "gpt-3.5-turbo-0613": 90_000,
    "gpt-4-0613": 40_000
}

MAX_NUM_TOKENS_SOFT = {
    "gpt-3.5-turbo-0613": 4_096 - 1024,
    "gpt-4-0613": 4_096
}

MAX_NUM_TOKENS_HARD = {
    "gpt-3.5-turbo-0613": 4_096 - 1024,
    "gpt-4-0613": 8_192 - 1024
}

MULTIPLIER = 0.5
REDUCE_MULTIPLIER = False


class MyOpenAI(ChatOpenAI):
    last_call = 0
    logging_dir: Path = None
    start_time = datetime.datetime.now()
    call_counter = 0
    max_num_tokens_soft: int = 0
    max_num_tokens_hard: int = 0
    max_rpm: int = 0
    max_tpm: int = 0

    def _generate(self, prompts, *args, **kwargs):
        if not isinstance(self.client, MyClient):
            self.max_num_tokens_hard = MAX_NUM_TOKENS_HARD[self.model_name]
            self.max_num_tokens_soft = MAX_NUM_TOKENS_SOFT[self.model_name]
            self.max_rpm = int(MAX_RPM[self.model_name] * MULTIPLIER)
            self.max_tpm = int(MAX_TPM[self.model_name] * MULTIPLIER)

            self.client = MyClient(self.client, self)

        num_tokens = self.get_prompt_len(prompts)
        while num_tokens > self.max_num_tokens_soft and len(prompts) > 3:
            prompts = prompts[:2] + prompts[3:]
            num_tokens = self.get_prompt_len(prompts)

        while num_tokens > self.max_num_tokens_hard:
                prompts[0].content = prompts[0].content[100:]
                if prompts[0].content == "":
                    raise ValueError("Prompt too long. No more possibility to shorten it. Abort!")
                num_tokens = self.get_prompt_len(prompts)

        current_call = time.time()
        delta = current_call - self.last_call

        requests_delay = 60 / self.max_rpm
        tokens_delay = (60 * num_tokens) / self.max_tpm
        sleep_time = max(0.0, requests_delay - delta, tokens_delay - delta)
        print(sleep_time)
        time.sleep(sleep_time)

        logger.debug(f"Request: {prompts}")
        result = super()._generate(prompts, *args, **kwargs)
        logger.debug(f"Response: {result}")

        if self.logging_dir is not None:
            time_dir = self.logging_dir / ".prompts" / self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
            time_dir.mkdir(parents=True, exist_ok=True)
            with open(time_dir / str(self.call_counter), "w") as f:
                print("\n\n--\n".join(f"{type(p).__name__}: {p.content}" for p in prompts), file=f)
                print("*" * 300, file=f)
                print(result.generations[0].text, file=f)
            self.call_counter += 1
            if self.call_counter > 50:
                raise Exception("Too many prompts generated. Failed.")


        self.last_call = current_call
        return result

    def get_prompt_len(self, prompts):
        return self.get_num_tokens(ChatPromptTemplate.from_messages(prompts).format()) + 100


class MyClient(Completion):
    def __init__(self, client, llm):
        self._client = client
        self._llm = llm

    def create(self, *args, **kwargs):
        try:
            result = self._client.create(*args, **kwargs)
        except Exception as e:
            if REDUCE_MULTIPLIER:
                self._llm.max_rpm //= 2  # TODO also add possibility to increase rate again
                self._llm.max_tpm //= 2
            raise e
        return result

    def __getattr__(self, _attr):
        return getattr(self._client, _attr)

    def __setattr__(self, _name: str, _value: Any) -> None:
        if _name in ("_client", "_llm"):
            super().__setattr__(_name, _value)
        else:
            return setattr(self._client, _name, _value)
