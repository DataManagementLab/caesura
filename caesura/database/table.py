from pathlib import Path
import os
from typing import List
import pandas as pd

class Table():
    def __init__(self, name:str, data: pd.DataFrame, description: str, text_columns=(), image_columns=(), parent=None):
        """Initializes a table."""
        self.name = name
        self.description = description
        self.data_frame = data
        self.links = []
        if parent is not None:
            text_columns = text_columns or parent.text_columns
            image_columns = image_columns or parent.image_columns
        self.text_columns = text_columns
        self.image_columns = image_columns

    
    def get_columns(self):
        """Gets the columns of a table."""
        return self.data_frame.columns

    def get_datatype_for_column(self, column_name):
        """Gets the datatype of a column."""
        if column_name in self.text_columns:
            return "TEXT"
        if column_name in self.image_columns:
            return "IMAGE"
        result = self.data_frame[column_name].dtype
        if result == "object":
            return "str"
        return result

    def get_values(self, column_name):
        """Gets the values of a column."""
        return self.data_frame[column_name]
    
    def create_image_table(name: str, path: Path, description: str, file_paths: List[str]):
        """Creates an image table."""
        data = []
        file_paths_dict = {}
        for p in file_paths:  # files in table
            p = Path(p)
            file_paths_dict[p.name] = file_paths_dict.get(p.name, []) + [p]
        for img_path in os.listdir(path):  # files in dir
            full_path = Path(path) / img_path

            # Only add rows where image path is in table and image file exists
            if full_path.name not in file_paths_dict:
                continue
            if file_paths_dict and not any(Path.samefile(full_path, Path(p)) for p in file_paths_dict[full_path.name]):
                continue
            data.append({"img_path": str(full_path), "image": f"<IMAGE stored at '{full_path}'>"})
        data = pd.DataFrame(data)
        return Table(name, data, description, image_columns=("image",))

    def create_text_table(name: str, path: Path, description: str):
        """Creates a text table."""
        data = []
        if Path(path).is_dir():
            for txt_path in os.listdir(path):
                with open(txt_path) as f:
                    data.append({"txt_path": str(Path(path) / txt_path), "text": f.read()})
            data = pd.DataFrame(data)
            return Table(name, data, description, text_columns=("text",))
        else:
            data = pd.DataFrame(pd.read_csv(path))
            return Table(name, data, description, text_columns=(data.columns[-1],))

    def create_tabular_table(name: str, path: Path, description: str, path_columns=()):
        """Creates a tabular table."""
        data = pd.read_csv(path)
        for p in path_columns:
            data[p] = data[p].apply(lambda x: str(Path(path).parent / x))
        data = pd.DataFrame(data)
        return Table(name, data, description)

    def describe(self, skip_minus=False):
        """Describes the table."""
        special_cols = {**{img_column: "IMAGE" for img_column in self.image_columns},
                        **{txt_column: "TEXT" for txt_column in self.text_columns}}
        column_string = {str(c): str(special_cols.get(c, t if t != 'object' else 'str'))
                         for c, t in zip(self.data_frame.columns, self.data_frame.dtypes)}
        return f" {'' if skip_minus else '- '}{self.name} = table(num_rows={len(self.data_frame)}, columns=" \
               f"{column_string}, primary_key='{self.data_frame.columns[0]}', " \
               f"description='{self.description}', foreign_keys={self.links})".replace("{", "[").replace("}", "]")

    def add_link(self, link):
        """Adds a link to the table."""
        self.links.append(link)