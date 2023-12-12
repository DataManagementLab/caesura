import sys
import zipfile
import shutil
from pathlib import Path
import gdown
import logging
import pandas as pd

sys.path.append(Path(__file__).parent)

from wiki_infoboxes import WikiInfoboxes
from rotowire import Rotowire


logging.basicConfig(format="%(levelname)s %(asctime)s %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = (Path(__file__).parents[2] / "datasets" / "rotowire").absolute()
DATA_DIR.mkdir(exist_ok=True, parents=True)
SPLIT = "valid"


if __name__ == "__main__":

    # Step 1: Download
    if not DATA_DIR.exists() or next(DATA_DIR.iterdir(), None) is None:
        DATA_DIR.mkdir(exist_ok=True, parents=True)
        gdown.cached_download("https://drive.google.com/u/0/uc?id=1zTfDFCl1nf_giX7IniY5WbXi9tAuEHDn",
                              DATA_DIR / "data-release.zip")
        with zipfile.ZipFile(DATA_DIR / "data-release.zip", 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)
        for f in (DATA_DIR / "data" / "rotowire").iterdir():
            f.rename(DATA_DIR / f.name)
        shutil.rmtree(DATA_DIR / "data")

    # Step 2: Compute Wikidata Rotowire mapping and Evidences
    w = WikiInfoboxes(DATA_DIR)
    if not (DATA_DIR / "players.csv").exists():
        w.compute_evidences()


    game_reports = []
    players_to_games = []
    teams_to_games = []
    for i, team_labels, player_labels, report in Rotowire(SPLIT, DATA_DIR):
        game_reports.append((i, report.strip()))
        if "Name" in player_labels:
            players_to_games.extend([(n, i) for n in player_labels["Name"].tolist()])
        if "Name" in team_labels:
            teams_to_games.extend([(n, i) for n in team_labels["Name"].tolist()])


    pd.DataFrame(game_reports, columns=["game_id", "report"]).set_index("game_id").to_csv(DATA_DIR / "reports.csv")
    pd.DataFrame(players_to_games, columns=["name", "game_id"]).set_index(["name", "game_id"]).sort_index() \
        .to_csv(DATA_DIR / "players_to_games.csv")
    pd.DataFrame(teams_to_games, columns=["name", "game_id"]).set_index(["name", "game_id"]).sort_index() \
        .to_csv(DATA_DIR / "teams_to_games.csv")
