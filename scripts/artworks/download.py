import pandas as pd
import requests
import tqdm
import sys
from pathlib import Path

try:
    NUM_IMAGES = int(sys.argv[-1])
    print(f"Download {NUM_IMAGES} images.")
except ValueError:
    print("Download all images")
    NUM_IMAGES = 2 ** 32


DATA_DIR = (Path(__file__).parents[2] / "datasets" / "art").absolute()
DATA_DIR.mkdir(exist_ok=True, parents=True)

df = pd.read_csv("scripts/artworks/paintings_orig.csv")
df ["img_path"] = ""
df = df.loc[:NUM_IMAGES]

# Download images
for i, row in tqdm.tqdm(df.iterrows(), total=len(df)):
    response = requests.get(row["image_url"], headers={"User-Agent": "Mozilla/5.0"})
    art_dir = Path("datasets/art")
    (art_dir / "images").mkdir(exist_ok=True)  # Create images directory if it doesn't exist
    path = Path(f"images/img_{i}.jpg")
    with open(art_dir / path, "wb") as f:
        f.write(response.content)  # Write image to file
    df.loc[i, "img_path"] = "." / path

# Save data frame
df.to_csv("datasets/art/paintings.csv", index=False)
