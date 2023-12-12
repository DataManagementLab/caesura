import pandas as pd


class RelevantValueIndex():
    def __init__(self, n=5, padding=4):
        self.map = None
        self.values = set()
        self.n = n
        self.padding = padding

    def build(self, values):
        values = pd.Series(values)
        self.map = pd.DataFrame({"values": values, "n-grams": values.map(self.get_n_grams)})
        self.map = self.map.explode("n-grams")
        self.map = self.map.groupby("n-grams").agg(list)
        self.values = set(values)

    def get_relevant_values(self, *keywords, num=10):
        n_grams = self.get_n_grams(*keywords)
        n_grams = [x for x in n_grams if x in self.map.index]
        values = self.map.loc[n_grams]
        values = values.explode("values")["values"].value_counts(sort=True).index
        values = values[:num].tolist()
        values += self.get_remaining(values, num)
        return values
    
    def get_remaining(self, values, total_num):
        values = set(values)
        sample = list()
        num = total_num - len(values)
        for element in self.values:
            if element not in values:
                sample.append(element)
            if len(sample) >= num:
                break
        return sample

    def get_n_grams(self, *keywords):
        result = set()
        for k in keywords:
            result |= self._get_n_grams(k)
        return list(result)
    
    def _get_n_grams(self, keyword):
        result = set()
        if pd.isna(keyword):
            keyword = ""
        keyword = str(keyword) or ""
        for i in range(-self.padding, len(keyword) - self.n + self.padding + 1):
            pre_padding = "#" * max(-i, 0)
            post_padding = "#" * max(i + self.n - len(keyword), 0)
            n_gram = pre_padding + keyword[max(i, 0): max(i + self.n, 0)] + post_padding
            result.add(n_gram)
        return result
