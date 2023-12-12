class Capability():
    def __init__(self, name, description):
        self.name = name
        self.description = description


class Capabilities():
    Look = Capability(
        name="Look",
        description="You are able to look at images (columns of type IMAGE). For example, you are able to do things like:\n"
            " - Recognize the objects depicted in images. E.g. You can determine in which images a skateboard is depicted.\n"
            " - Recognize the style of the image. E.g. You can determine whether the image is a photograph or pixel art or ...\n"
            " - You can count the number of objects of a certain type. E.g. You can count all marbles depicted in an image.\n"
            " - You can look at images both to add new columns to a table (e.g. num_marbles) or to select rows based on images (e.g. all rows where image depicts a skateboard).\n"
            " - ...\n"
            " Template 1: Extract <what to extract from each individual image, e.g. the number of marbles depicted> for each image in <column, e.g. images>.\n"
            " Template 2: Select all rows where <column, e.g. images> depicts <description about what should be depicted>.\n"
    )
    Read = Capability(
        name="Read",
        description="You are able to read and understand longer texts (columns of type TEXT). For example, you are able to do things like:\n"
            " - Extract relevant information from texts. E.g. in a patient report, you can extract the patient, diagnosis, treatment, ...\n"
            " - You can read texts both to add new columns to a table (e.g. diagnosis) or to select rows based on the text (e.g. all rows where diagnosis is fever).\n"
            " - ...\n"
            "Template: Extract <what to extract from each individual text, e.g. the age / diagnosis / treatment> for each <class of entity, e.g. patient> from <column, e.g. patient_report in table joined_patient_table>.\n"
    )
    Transform = Capability(
        name="Transform",
        description="You are able to transform the values in a column. For example, you are able to do things like:\n"
            " - In a column containing dates, you are able to extract the day, month, year etc.\n"
            " - In a column containing names, you are able to transform all strings to upper case, lower case etc.\n"
            " - ....\n"
            "Template 1: Extract <what to extract from each individual value, e.g. the year> from each value in <column, e.g. date_of_birth>.\n"
            "Template 2: Transform the values in <column, e.g. name> to <description of transformation, e.g. lower case>\n"
    )
    Plot = Capability(
        name="Plot",
        description="You are able to produce plots if the user requests one. You can produce bar plots, scatter plots and line plots.\n"
            "In order to produce a plot, the data must be prepared using the other tools. The input for plotting is a table with two "
            "columns and one of those columns will be plotted on the X-Axis and the other on the Y-Axis.\n"
            "Template: Plot the <table name, e.g. result_table> table in a bar plot. The <column X, e.g. diagnosis> should be on the X-axis and the <column Y, e.g. mean_age> on the Y-Axis.\n"
    )
    DataProcessing = Capability(
        name="Data Processing",
        description="You are able to manipulate the tables in a SQL like manner. For example you are able to:\n"
            "- Select rows that match a certain criterion. E.g. You can select all rows where the value of a column is larger than a threshold, an image column depicts a skateboard or the text is a patient report. Per step, you are only allowed to select based on a single column.\n"
            "- Project columns to dismiss irrelevant columns.\n"
            "- Join two tables to combine them. You can do all typical joins, like inner joins, left joins, right joins etc.\n"
            "- Aggregate rows. E.g. You can group a patients table based on their diagnosis to compute the average age for each diagnosis.\n"
            "Template: <Select/Project/Join/Group> <description of operation>\n"
    )


ALL_CAPABILITIES = [Capabilities.Look, Capabilities.Read, Capabilities.Transform,
                    Capabilities.DataProcessing, Capabilities.Plot]
