from datetime import datetime
import re
import logging
import dateparser


logger = logging.getLogger(__name__)

number_words = {
    "many": 50,
    "zero": 0,
    "a": 1,
    "one": 1,
    "first": 1,
    "once": 1,
    "two": 2,
    "second": 2,
    "twice": 2,
    "three": 3,
    "third": 3,
    "four": 4,
    "fourth": 4,
    "five": 5,
    "fifth": 5,
    "six": 6,
    "sixth": 6,
    "seven": 7,
    "seventh": 7,
    "eight": 8,
    "eights": 8,
    "nine": 9,
    "ninth": 9,
    "ten": 10,
    "tenth": 10,
    "eleven": 11,
    "eleventh": 11,
    "twelve": 12,
    "twelfth": 12,
    "yes": 1,
    "no": 0
}

def get_paths_from_images(images):
    """Returns the paths of the images."""
    # images = array(["<IMAGE stored at 'datasets/art/images/img_13.jpg'>", ...)
    paths = [re.search(r"'(.*)'", x).group(1) for x in images if x is not None]
    return paths

def convert(data, datatype):
    return [_convert(d, datatype) for d in data]

def _convert(data, datatype):
    if datatype in ("int", "float", "boolean") and data in number_words:
        data = number_words[data]
    if datatype == "boolean":
        try:
            return bool(data)
        except:
            return False
    if datatype == "int":
        try:
            return int(data)
        except:
            return 0
    if datatype == "float":
        try:
            return float(data)
        except:
            return 0.0
    if datatype == "date":
        try:
            return dateparser.parse(data)
        except:
            return datetime.min

    return data


def parse_args(step, query):
    if "```" in query:
        query = re.split("```\w*", query)[1].strip()
    if query.startswith("("):
        b = 1
        for i, c in enumerate(query):
            if c == "(":
                b += 1
            if c == ")":
                b -= 1
            if b == 0:
                break
        query = query[1:i]
    result = tuple(x.strip(" \"`") for x in query.split(";"))
    return result
