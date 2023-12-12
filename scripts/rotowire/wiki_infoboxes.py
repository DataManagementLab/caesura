import itertools
from pathlib import Path
import re
import pandas as pd
import wptools
from tqdm import tqdm

from rotowire import Rotowire


class WikiInfoboxes():
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.mapping = Path(__file__).parent / "rotowire-wikipedia-mapping.txt"
        self.evidence_team = data_dir / "teams.csv"
        self.evidence_player = data_dir / "players.csv"

    def load_player_evidence_table(self):
        return pd.read_csv(self.evidence_player)

    def load_team_evidence_table(self):
        return pd.read_csv(self.evidence_team)

    def compute_rotowire_wikipedia_mapping(self):
        names = set(n for split in ("train", "valid", "test")
                    for line in Rotowire(split, self.data_dir)
                    for n in itertools.chain(line[2]["Name"], line[1]["Name"] if "Name" in line[1] else ()))

        # Lookup infoboxes
        with open(self.mapping, "w") as f:
            for rotowire_name in tqdm(names, total=len(names)):
                wikipedia_name = rotowire_name
                infobox = None
                try:
                    page = wptools.page(wikipedia_name).get_parse(show=False)
                    infobox = page.data["infobox"]
                    if infobox is None:
                        wikipedia_name += " (basketball)"
                        page = wptools.page(wikipedia_name).get_parse(show=False)
                        infobox = page.data["infobox"]
                except LookupError:
                    pass

                if infobox is None:  # must be filled in manually
                    print(rotowire_name, input(f"NOT FOUND: {rotowire_name} > ").strip(), sep="\t", file=f)
                else:
                    print(rotowire_name, wikipedia_name, sep="\t", file=f)
                f.flush()

    def compute_evidences(self):
        with open(self.mapping) as f:
            names_dict = dict(
                line.rstrip().split("\t") for line in f
            )

        fields = {
            "team": ["conference", "division", "founded", "arena", "location", "president", "coach"],
            "player": ["height", "nationality", "birth_place", "birth_date", "career_position"]
        }

        result = dict()
        for rotowire_name, wikipedia_name in tqdm(names_dict.items()):
            infobox = None
            try:
                page = wptools.page(wikipedia_name).get_parse(show=False)
                infobox = page.data["infobox"]

                table_teams = self.extract_information_for_team(infobox=infobox, fields=fields)
                table_player = self.extract_information_for_player(infobox=infobox, fields=fields)
                n_teams = len([v for v in table_teams.values() if v != ""])
                n_players =  len([v for v in table_player.values() if v != ""])
                table = table_teams if n_teams > n_players else table_player
            except Exception as e:
                input(f"Error occurred: {e}")
                raise e

            print('\033[94m', table, '\033[0m')
            result[rotowire_name] = table
        with open(self.evidence_team, "w") as f:
            df = pd.DataFrame({k: v for k, v in result.items() if "location" in v}).T
            df.index.name = "name"
            df.to_csv(f)
        with open(self.evidence_player, "w") as f:
            df = pd.DataFrame({k: v for k, v in result.items() if "location" not in v}).T
            df.index.name = "name"
            df.to_csv(f)

    def get_player_teams(self, infobox: dict) -> str:
        if infobox.get('name') in ['Mirza Teletović', 'Nikola Peković', 'Reggie Jackson']:
            return {}
        team_prefix = 'team'
        year_prefix = 'years'
        for key in infobox.keys():
            if key.startswith('coach_team'):
                team_prefix = 'coach_team'
                break
        team_names = []
        team_years = []
        for key in infobox.keys():
            if key.startswith(team_prefix):
                team_names.append(infobox.get(key).replace("[[", "").replace("]]", ""))
                years = infobox.get(year_prefix + key[len(team_prefix):], "{{nbay|0|full|=|y}}")
                regex = re.compile(r"{{\w+\|(\d+)\|\w+[^}]*}}|\[\[.*\|(\d+)[–,;-]\s*(\d*|present)\]\]|\[\[.*\|(\d+)\]\]|(?:^|<br\/>)(\d+)[–,;-]\s*(\d*|present)(?:$|,|;)|(?:^|<br\/>)(\d+)(?:$|,|;)")
                years = [int(g) if g != "present" else 2022 for m in regex.findall(years) for g in m if g]
                team_years.append(years)
        result = {}
        if any(len(x) == 0 for x in team_years):
            input("Could not find team years for " + infobox.get('name'))
        for name, years in zip(team_names, [range(y[0], y[1 if len(y) == 2 else 0] + 1) if y else [] for y in team_years]):
            for y in years:
                result[y] = result.get(y, [])
                result[y].append(name.split("|")[0].replace("→", ""))
        return result

    def parse_player_height(self, infobox: dict) -> str:
        if 'height_ft' in infobox.keys():
            return round(float(infobox.get('height_ft')) + float(infobox.get('height_in', 0)) / 12.0, ndigits=2)
        if 'height' in infobox.keys():
            match = re.search(
                r"(?<=convert\|)\d{1,2}\|ft\|\d{1,2}(?=\|in)", infobox.get('height', 'none'))
            if match:
                height_splited = match.group(0).split('|ft|')
                return round(float(height_splited[0]) + float(height_splited[1]) / 12.0, ndigits=2)
            else:
                return infobox.get('height', "none")

    def parse_player_weight(self, infobox: dict) -> str:
        for key in infobox.keys():
            if key.startswith('weight_lb'):
                return infobox.get(key)

    def search_position(self, string_to_search):
        match1 = re.search(r"((?<=\)\|)).*(?=\]\])", string_to_search)
        if match1:
            return [match1.group(0)]
        else:
            match2 = re.search(r"((?<=\[\[)).*(?=\]\])", string_to_search)
            if match2:
                return [match2.group(0)]
            else:
                return []

    def parse_player_position(self, infobox: dict, player_information: dict):
        result_positions = []
        infobox_keys = infobox.keys()
        career_position = 'career_position'
        if (career_position not in infobox_keys) and ('position' in infobox_keys):
            positions = infobox['position'].split('/')
            result_positions += self.search_position(positions[0])
            if len(positions) > 1:
                result_positions += self.search_position(
                    positions[1])
        elif career_position in infobox_keys:
            positions = infobox[career_position].split('/')
            match1 = re.search(r"((?<=\)\|)).*(?=\]\])",
                                positions[0].strip())
            if match1:
                result_positions += [match1.group(0)]
                if len(positions) > 1:
                    result_positions += self.search_position(
                        positions[1])
            else:
                match_alternative = re.search(
                    r"((?<=\[\[)).*(?=\]\])", positions[0].strip())
                result_positions += [match_alternative.group(0)]
        player_information["position"] = " ".join(result_positions)

    def parse_regex_standard(self, infobox: dict, field: str, table: dict):
        link_regex = re.compile(r"\[\[(.+\|)?(.+)\]\]")

        values = [infobox.get(field, "none")]
        if values[0].startswith("{{hlist"):
            values = []
            for v in infobox.get(field, "").split("|"):
                v = v.strip()
                if v == "ref":
                    continue
                values.append(v.strip())
        
        matches = [link_regex.match(v) for v in values]
        result = [m.group(2) if m else infobox[field] for m, v in zip(matches, values) if m or field in infobox]
        result =  ", ".join(result)
        table[field] = result
        return result

    def extract_information_for_player(self, infobox: dict, fields: dict) -> dict:
        player_information = {}
        teams = self.get_player_teams(infobox)
        for field in fields["player"]:
            if field == 'height':
                player_information[field] = self.parse_player_height(infobox)
                continue
            if field == 'weight_lbs':
                player_information[field] = self.parse_player_weight(infobox)
                continue
            if field == "birth_date":
                # Example: {{birth date and age|1994|2|18|df|=|y}}
                match = re.search(
                    r"{{.*\|(\d{4})\|(\d{1,2})\|(\d{1,2}).*}}", infobox.get(field, "none"))
                if match:
                    player_information[field] = f"{match.group(3)}.{match.group(2)}.{match.group(1)}"
                else:
                    player_information[field] = infobox.get(field, "none")
                continue
            if field == 'career_position':
                self.parse_player_position(infobox, player_information)
                continue
            if field.startswith("team"):
                year = int(field.split("_")[1])
                player_information[field] = ", ".join(teams.get(year, ""))
                continue
            self.parse_regex_standard(infobox, field, player_information)
        return player_information

    def extract_information_for_team(self, infobox: dict, fields: dict) -> dict:
        table = {}
        for field in fields["team"]:
            self.parse_regex_standard(infobox, field, table)
        return table