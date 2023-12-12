import torch
from typing import List
from transformers import AutoTokenizer, BartForQuestionAnswering
BATCH_SIZE = 2



class TextQA():
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("valhalla/bart-large-finetuned-squadv1")
        self.model = BartForQuestionAnswering.from_pretrained("valhalla/bart-large-finetuned-squadv1")


    def extract(self, texts: List[str], query: List[str]):
        """Retrieves images from the database."""
        data = self.tokenizer(query.tolist(), texts.tolist(), return_tensors="pt", padding=True, truncation=True)
        _, uq_indexes, uq_inverse = unique(data["input_ids"], dim=0)
        data_unique = {k: v[uq_indexes] for k, v in data.items()}
        result_values = list()
        for i in range(0, data_unique["input_ids"].shape[0], BATCH_SIZE):
            inputs = {k: v[i: i + BATCH_SIZE] for k, v in data.items()}
            result = self.model(**inputs)
            start = result["start_logits"].argmax(1)
            end = result["start_logits"].argmax(1)
            for i in range(len(start)):
                value = self.tokenizer.decode(data["input_ids"][i][start[i]: end[i] + 1]).strip()
                result_values.append(value)
        result = [result_values[i] for i in uq_inverse]
        return result


def unique(x, dim=None):
    """Unique elements of x and indices of those unique elements
    https://github.com/pytorch/pytorch/issues/36748#issuecomment-619514810

    e.g.

    unique(tensor([
        [1, 2, 3],
        [1, 2, 4],
        [1, 2, 3],
        [1, 2, 5]
    ]), dim=0)
    => (tensor([[1, 2, 3],
                [1, 2, 4],
                [1, 2, 5]]),
        tensor([0, 1, 3]))
    """
    unique, inverse = torch.unique(
        x, sorted=True, return_inverse=True, dim=dim)
    perm = torch.arange(inverse.size(0), dtype=inverse.dtype,
                        device=inverse.device)
    inverse, perm = inverse.flip([0]), perm.flip([0])
    return unique, inverse.new_empty(unique.size(0)).scatter_(0, inverse, perm), inverse
