import datetime
import itertools
import pathlib
import re
import numpy as np
import fire
from database_gpt.main import Caesura

from database_gpt.scenarios import get_database


forbidden_queries = {}

# forbidden_queries = {  # First 24 queries
#     "What is the newest painting in the database",
#     "Plot the lowest number of swords depicted in each genre",
#     "Plot the number of paintings that depict War for each century",
#     "Who is the smallest power forward in the database",
#     "What is the youngest team in the Southeast Division in terms of the founding date",
#     "Who is the oldest player per nationality",
#     "What is the oldest team per conference in terms of the founding date",
#     "Plot the age of the youngest player per position",
#     "Plot the age of the oldest team per conference in terms of the founding date",
#     "Who made the lowest number of assists in any game",
#     "Which team made the highest percentage of field goals in any game",
#     "What is the genre of the newest painting in the database",
#     "For each player, what is the highest number of assists they made in a game",
#     "How many games did each team loose",
#     "Plot the highest number of three pointers made by players from each nationality",
#     "Plot the  lowest percentage of field goals made by teams from each division",
#     "Get the century of the newest painting per movement",
#     "Get the number of paintings for each century",
#     "Plot the year of the oldest painting per genre",
#     "Plot the number of paintings for each century",
#     "What is depicted on the oldest Renaissance painting in the database",
#     "What is the movement of the painting that depicts the highest number of babies",
#     "Get the highest number of swords depicted in paintings of each genre",
#     "Get the number of paintings that depict Animals for each movement",
# }



def sample_queries(datasets=("artwork", "rotowire"), num_samples_per_template=2, seed=42):
    result = []
    rng = np.random.default_rng(seed=seed)
    for dataset in datasets:
        templates, template_values = get_queries[dataset]()
        for template in templates:
            values = [template_values[v.split(" ")[0]] for v in template.variables]
            options = list(itertools.product(*values))
            options = [template.instantiate(o) for o in options]
            options = [o for o in options if str(o).strip(" .?") not in forbidden_queries]
            sampled = rng.choice(options, min(num_samples_per_template, len(options)), replace=False)
            for chosen_values in sampled:
                result.append(chosen_values)
    return result


class Template():
    def __init__(self, template, multi_modal, output_type, scenario):
        assert isinstance(multi_modal, bool)
        assert output_type in {"value", "table", "plot"}
        self.template = template
        self.multi_modal = multi_modal
        self.output_type = output_type
        self.variables = self.get_variables()
        self.scenario = scenario

    def get_variables(self):
        return re.findall(r"{([^}]+)}", self.template)

    def instantiate(self, values):
        assert len(self.variables) == len(values)
        instantiated = self.template
        for key, value in zip(self.variables, values):
            instantiated = instantiated.replace("{" + key + "}", value)
        return Query(instantiated, self)

    def __str__(self):
        return self.template

    def __repr__(self):
        return self.template


class Query():
    def __init__(self, query, template):
        self.query = query
        self.template = template

    def __str__(self):
        return self.query
    
    def __repr__(self):
        return self.query


def query_templates_artwork():
    # Artworks
    template_values = dict(
        highest = ["highest", "lowest"],
        oldest = ["oldest", "newest"],
        century = ["century", "year"],
        genre = ["genre", "movement"],
        religious_artwork = ["painting", "religious artwork", "Renaissance painting", "impressionist artwork"],
        madonna_and_child = ["Madonna and Child", "War", "Animals", "Fruit", "Monarch"],
        animals = ["persons", "animals", "babies", "swords"],
    )
    template_values["genre_slash_century"] = template_values["century"] + template_values["genre"]


    templates = [
        # Single table
            # Single Value
        Template("What is the {oldest} {religious_artwork} in the database?", False, "value", "artwork"),
        Template("What is the {genre_slash_century} of the {oldest} painting in the database?", False, "value", "artwork"),

            # Table as Output
        Template("Get the {century} of the {oldest} painting per {genre}.", False, "table", "artwork"),
        Template("Get the number of {religious_artwork}s for each {century}.", False, "table", "artwork"),

            # Plot as Output
        Template("Plot the {century} of the {oldest} painting per {genre}.", False, "plot", "artwork"),
        Template("Plot the number of {religious_artwork}s for each {century}.", False, "plot", "artwork"),

        # Multi-Table
            # Single Value
        Template("What is depicted on the {oldest} {religious_artwork} in the database?", True, "value", "artwork"),
        Template("What is the {genre_slash_century} of the painting that depicts the {highest} number of {animals}?", True, "value", "artwork"),

            # Table as Output
        Template("Get the {highest} number of {animals} depicted in paintings of each {genre_slash_century}.", True, "table", "artwork"),
        Template("Get the number of paintings that depict {madonna_and_child} for each {genre_slash_century}.", True, "table", "artwork"),

            # Plot as Output
        Template("Plot the {highest} number of {animals} depicted in each {genre_slash_century}.", True, "plot", "artwork"),
        Template("Plot the number of paintings that depict {madonna_and_child} for each {genre_slash_century}.", True, "plot", "artwork"),
    ]
    return templates, template_values


def query_templates_rotowire():
    # Rotowire
    template_values = dict(
        points = ["points", "assists", "field goals", "three pointers", "rebounds"],
        number_of_total_points = ["number of total points", "number of points in 1st quarter", "percentage of field goals"],
        win = ["win", "loose"],
        tallest = ["tallest", "oldest", "youngest", "smallest"],
        position = ["position", "nationality"],
        oldest = ["oldest", "youngest"],
        division = ["division", "conference"],
        age_player = ["age", "height"],
        age_team = ["age"],
        small_forward = ["small forward", "power forward", "point guard", "shooting guard"],
        eastern_conference = ["Eastern conference", "Western conference", "Southeast Division", "Pacific Division"],
        highest = ["highest", "lowest"],
    )

    templates = [
        # Single Table
            # Single Value
        Template("Who is the {tallest} {small_forward} in the database?", False, "value", "rotowire"),
        Template("What is the {oldest} team in the {eastern_conference} in terms of the founding date?", False, "value", "rotowire"),
            # Table as Output
        Template("Who is the {tallest} player per {position}?", False, "table", "rotowire"),
        Template("What is the {oldest} team per {division} in terms of the founding date?", False, "table", "rotowire"),

            # Plot as output
        Template("Plot the {age_player} of the {oldest} player per {position}.", False, "plot", "rotowire"),
        Template("Plot the {age_team} of the {oldest} team per {division} in terms of the founding date.", False, "plot", "rotowire"),


        # Multi Table
            # Single Value
        Template("Who made the {highest} number of {points} in any game?", True, "value", "rotowire"),
        Template("Which team made the {highest} {number_of_total_points} in any game?", True, "value", "rotowire"),

            # Table as Output
        Template("For each player, what is the {highest} number of {points} they made in a game?", True, "table", "rotowire"),
        Template("How many games did each team {win}?", True, "table", "rotowire"),

            # Plot as Output
        Template("Plot the {highest} number of {points} made by players from each {position}.", True, "plot", "rotowire"),
        Template("Plot the  {highest} {number_of_total_points} made by teams from each {division}.", True, "plot", "rotowire"),
    ]
    return templates, template_values


get_queries = dict(
    artwork=query_templates_artwork,
    rotowire=query_templates_rotowire
)


MODELS = {
    3: "gpt-3.5-turbo-0613",
    4: "gpt-4-0613"
}


def run_experiment(dataset: str = None, model: int = None,
                   seed: int = 43, num_samples_per_template:int = 1, skip_queries: int = -1):
    model = list(MODELS.values()) if model is None else (MODELS[int(model)], )
    datasets = ("artwork", "rotowire") if dataset is None else (dataset, )

    print("Models:", model, [type(x) for x in model])
    print("Datasets:", datasets, [type(x) for x in datasets])

    queries = sample_queries(datasets=datasets, num_samples_per_template=num_samples_per_template, seed=seed)
    previous_db_name = None
    db = None
    current_time = datetime.datetime.now()
    time_string = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    for m in model:
        for i, q in enumerate(queries):
            if skip_queries >= i:
                continue
            path = pathlib.Path("experiments") / m / time_string  / "ours" / f"query_{i}"
            db_name = q.template.scenario
            if db_name != previous_db_name:
                db = get_database(db_name, sampled=False)
                previous_db_name = db_name
            agent = Caesura(db, model_name=m, interactive=False, log_path=path)
            agent.run(str(q))


if __name__ == "__main__":
    fire.Fire(run_experiment)
