from collections import OrderedDict
from os import linesep
import six

COLUMN_LIMIT = 32767 - 10 # padding 10 for \'b and other formatting characters

def truncate_column(column):
    if isinstance(column, six.string_types):
        return column[0:COLUMN_LIMIT]
    else:
        return column

class MatchSummary(OrderedDict):
    @staticmethod
    def field_names():
        return OrderedDict([
            ("input_fp", "input file name"),
            ("matched_license", "matched license type"),
            ("score", "Score using whole input test"),
            ("start_line_ind", "Start line number"),
            ("end_line_ind", "End line number"),
            ("start_offset", "Start byte offset"),
            ("end_offset", "End byte offset"),
            ("region_score", "Score using only the license text portion"),
            ("found_region", "Found license text"),
            ("original_region", "Matched license text without context")
        ])

    def to_display_format(self):
        output_str = "Summary of the analysis" + linesep + linesep\
            + "Name of the input file: {}".format(self["input_fp"]) + linesep\
            + "Matched license type is {}".format(self["matched_license"]) + linesep\
            + "Score for the match is {:.3}".format(self["score"]) + linesep\
            + "License text beings at line {}.".format(self["start_line_ind"]) + linesep\
            + "License text ends at line {}.".format(self["end_line_ind"]) + linesep\
            + "Start byte offset for the license text is {}.".format(self["start_offset"]) + linesep\
            + "End byte offset for the license text is {}.".format(self["end_offset"]) +linesep\
            + "The found license text has the score of {:.3}".format(self["region_score"]) + linesep\
            + "The following text is found to be license text " + linesep\
            + "-----BEGIN-----" + linesep\
            + self["found_region"] \
            + "-----END-----" + linesep + linesep
        if self.has_key("original_region"):
            output_str = output_str[:-1] \
                         + "The following text is found to be original matched license text \
                         without context " + linesep\
                         + "-----BEGIN-----" + linesep\
                         + self["original_region"] \
                         + "-----END-----" + linesep + linesep
        return output_str

    def to_csv_row(self):
        csv_row = []
        for key in self.field_names().keys():
            if self.has_key(key):
                if key in ("input_fp", "found_region", "original_region"):
                    csv_row.append(truncate_column(self[key]).encode('utf8', 'surrogateescape'))
                else:
                    csv_row.append(truncate_column(self[key]))
        return csv_row
