import pandas as pd
import requests
import tqdm
from pathlib import Path

NUM_MOVEMENTS = 40

df = pd.read_csv("datasets/art/paintings.csv")
movements = df.groupby(by="movement").size().sort_values()[-NUM_MOVEMENTS:].index
df = pd.DataFrame(df.loc[df["movement"] == m].iloc[0] for m in movements)

# write to csv
df.to_csv("datasets/art/paintings_sampled.csv", index=False)