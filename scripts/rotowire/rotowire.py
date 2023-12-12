import pandas as pd

DATA_SUFFIX = ".data"
TEXT_SUFFIX = ".text"
NEW_LINE = " <NEWLINE> "
SEPARATOR_STRING = '|'


class Rotowire():
    def __init__(self, split, data_dir, skip=-1):
        self.split = split
        self.skip = skip
        self.data_path = data_dir / (self.split + DATA_SUFFIX)
        self.text_path = data_dir / (self.split + TEXT_SUFFIX)

    def __iter__(self):
        with open(self.data_path) as f_data, open(self.text_path) as f_text:
            for i, (line_data, line_text) in enumerate(zip(f_data, f_text)):
                if i < self.skip:
                    continue
                changed_line = line_data.replace(NEW_LINE, '\n')
                team_df, player_df = self.convert_output_to_df(changed_line)
                yield i, team_df, player_df, line_text

    def iter_raw(self):
        with open(self.data_path) as f_data, open(self.text_path) as f_text:
            yield from zip(f_data, f_text)

    def __len__(self):
        with open(self.data_path) as f:
            return len(f.readlines())

    @staticmethod
    def convert_row_to_cells(row: str) -> list:
        """
        return array of cell texts
        """
        texts = row.split(SEPARATOR_STRING)
        left_offset = 0
        right_offset = 0
        if row.endswith(SEPARATOR_STRING):
            right_offset = 1
        if row.startswith(SEPARATOR_STRING):
            left_offset = 1
        return texts[left_offset: -right_offset]

    @staticmethod
    def convert_text_to_df(text: str) -> pd.DataFrame:
        rows = text.split('\n')
        header = rows[0]

        header_texts = Rotowire.convert_row_to_cells(header)
        df_dict = {}
        for text in header_texts:
            df_dict[text.strip()] = []

        for i in range(1, len(rows)):
            #
            entry_texts = Rotowire.convert_row_to_cells(rows[i])
            for id, item in enumerate(df_dict.items()):
                item[1].append(entry_texts[id].strip())
        result = pd.DataFrame(df_dict)
        result.rename(columns={'': 'Name'}, inplace=True)
        return result


    @staticmethod
    def convert_output_to_df(output: str):
        # Team:
        # |  | Percentage of 3 points | Percentage of field goals | Losses | Total points | Wins |
        # | Raptors | 68 | 55 | 6 | 122 | 11 |
        # | 76ers |  | 42 | 14 | 95 | 4 |
        # Player:
        # |  | Assists | Blocks | Field goals attempted | Field goals made | Points | Total rebounds | Steals |
        # | Robert Covington | 2 | 1 | 11 | 7 | 20 | 5 | 2 |
        # | Ersan Ilyasova |  |  |  |  | 11 |  |  |
        # | Jahlil Okafor |  |  |  |  | 15 | 5 |  |
        # | Nik Stauskas |  |  |  |  | 11 |  |  |
        # | Richaun Holmes |  |  |  |  | 11 |  |  |
        # | Sergio Rodriguez |  |  |  |  | 11 |  |  |
        # | Jonas Valanciunas |  |  |  |  | 12 | 11 |  |
        # | DeMar DeRozan | 5 |  |  |  | 14 | 5 |  |
        # | Kyle Lowry | 8 |  |  |  | 24 | 4 |  |
        # | Terrence Ross |  |  | 11 | 8 | 22 |  |  |
        team_and_player = output.strip().split('\nPlayer:\n') + [""]
        team_str = team_and_player[0].replace('Team:\n', '')
        player_str = team_and_player[1]

        team_df = Rotowire.convert_text_to_df(team_str)
        player_df = Rotowire.convert_text_to_df(player_str)
        return team_df, player_df
