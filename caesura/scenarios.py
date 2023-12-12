from caesura.database.database import Database
import datetime


def get_database(scenario, sampled=True):
    if scenario == "artwork":
        return artwork_scenario(sampled=sampled)
    if scenario == "rotowire":
        return rotowire_scenario(sampled=sampled)
    raise KeyError(scenario)


def artwork_scenario(sampled=True):
    dl = Database()
    dl.add_tabular_table("paintings_metadata", f"datasets/art/paintings{'_sampled' if sampled else ''}.csv",
                           "a table that contains general information about paintings", path_columns=("img_path",))
    mask = dl._tables["paintings_metadata"].data_frame["inception"].apply(lambda x: not x.startswith("http"))
    dl._tables["paintings_metadata"].data_frame = dl._tables["paintings_metadata"].data_frame[mask].reset_index(drop=True)
    dl.add_image_table("painting_images", "datasets/art/images",
                         "a table that contains images of paintings",
                         file_paths=dl.get_column_values("paintings_metadata", "img_path").tolist())
    dl.link_image("paintings_metadata", "painting_images", "img_path")
    dl.build_relevant_values_index("paintings_metadata", "genre", "movement")
    return dl


def rotowire_scenario(sampled=True):
    dl = Database()
    dl.add_tabular_table("players", "datasets/rotowire/players.csv",
                         "a table that contains general information about basketball players")
    dl.add_tabular_table("teams", "datasets/rotowire/teams.csv",
                         "a table that contains general information about basketball teams")
    dl.add_tabular_table("players_to_games", "datasets/rotowire/players_to_games.csv",
                         "a table that maps players to games")
    dl.add_tabular_table("teams_to_games", "datasets/rotowire/teams_to_games.csv",
                         "a table that maps teams to games")
    dl.add_text_table("game_reports", f"datasets/rotowire/reports{'_sampled' if sampled else ''}.csv",
                      "a table containing game reports about basketball games. Each report contains statistics about all the teams and players that participated in a single game, e.g. number of points scored by each player / team, number of assists by each player / team, etc.")
    dl.link("players_to_games", "game_reports", "game_id")
    dl.link("teams_to_games", "game_reports", "game_id")
    dl.link("teams", "teams_to_games", "name")
    dl.link("players", "players_to_games", "name")
    dl.build_relevant_values_index("players", "name", "nationality", "position")
    dl.build_relevant_values_index("teams", "arena", "location", "president", "coach")
    dl.tables["players"].data_frame["birth_date"].apply(
        lambda x: datetime.datetime.strptime(x, "%d.%m.%Y").strftime("%Y-%m-%d")
    )
    return dl
