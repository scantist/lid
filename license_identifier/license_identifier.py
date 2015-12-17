from os import listdir, walk, getcwd, linesep
from os.path import isfile, join, isdir, dirname, exists
from collections import Counter, defaultdict
import sys
import argparse
import csv
import codecs

from . import license_match
from . import n_grams as ng
from . import location_identifier as loc_id


from future.utils.surrogateescape import register_surrogateescape

register_surrogateescape()

DEFAULT_THRESH_HOLD=0.04
DEFAULT_LICENSE_DIR=join(getcwd(), "..", 'data','license_dir')

class license_identifier:
    def __init__(self, license_dir=DEFAULT_LICENSE_DIR,
                 threshold=DEFAULT_THRESH_HOLD,
                 input_path=None,
                 output_format=None,
                 output_path=None):
        self.license_dir = license_dir
        self.custom_license_dir = join(self.license_dir, 'custom')

        # holds n gram models for each license type
        #  used for matching input vs. each license
        self.license_n_grams = defaultdict()
        self.license_file_name_list = []
        # holds n-gram models for all license types
        #  used for parsing input file words (only consider known words)
        self._universe_n_grams = ng.n_grams()
        self._build_n_gram_univ_license(self.license_dir)    
        if exists(self.custom_license_dir):
            self._build_n_gram_univ_license(self.custom_license_dir)    
        if input_path:
            result_obj = self.analyze_input_path(input_path, threshold)
            self.format_output(result_obj, output_format, output_path=output_path)

    def format_output(self, result_obj, output_format, output_path):
        print('we are in this output format:{}'.format(output_format))
        if output_format == ['csv']:
            self.write_csv_file(result_obj, output_path)
        elif output_format == ['easy_read']:
            self.display_easy_read(result_obj)

    # TODO: add unicode output from unicode input (if necessary).
    def write_csv_file(self, result_obj_list, output_path):
        if sys.version_info >= (3,0,0):
            f = open(output_path, 'w', newline='')
        else:
            f = open(output_path, 'wb')
        field_names = ['input file name',
                       "matched license type",
                       "Score using whole input test",
                       "Start line number",
                       "End line number",
                       "Start byte offset",
                       "End byte offset",
                       "Score using only the license text portion",
                       "Found license text"]
        writer = csv.writer(f)
        writer.writerow(field_names)
        for result_obj in result_obj_list:
            summary_obj = result_obj[1]
            writer.writerow(summary_obj)
        f.close()


    def _get_license_file_names(self, directory):
        file_fp_list = [ f for f in join(listdir(directory)) \
                           if isfile(join(directory,f)) and \
                           '.txt' in f ]
        return file_fp_list

    def _get_license_name(self, file_name):
        return file_name.split('.txt')[0]

    def _build_n_gram_univ_license(self, license_dir):
        '''
        parses the license text files and build n_gram models
        for each license type
          and
        for all license corpus combined
        '''
        license_file_name_list = self._get_license_file_names(license_dir)
        for license_file_name in license_file_name_list:
            list_of_license_str = self.get_str_from_file(join(license_dir, license_file_name))
            license_name = self._get_license_name(license_file_name)
            self._universe_n_grams.parse_text_list_items(list_of_license_str)
            new_license_ng = ng.n_grams(list_text_line=list_of_license_str)
            self.license_n_grams[license_name] = (new_license_ng, license_dir)
        self.license_file_name_list.extend(license_file_name_list)

    def display_easy_read(self, result_obj_list):
        for result_obj in result_obj_list:
            print(self.build_summary_list_str(result_obj[1]))


    def build_summary_list_str(self, summary_list):
        output_str = "Summary of the analysis" + linesep + linesep\
            + "Name of the input file: {}".format(summary_list[0]) + linesep\
            + "Matched license type is {}".format(summary_list[1]) + linesep\
            + "Score for the match is {:.3}".format(summary_list[2]) + linesep\
            + "License text beings at line {}.".format(summary_list[3]) + linesep\
            + "License text ends at line {}.".format(summary_list[4]) + linesep\
            + "Start byte offset for the license text is {}.".format(summary_list[5]) + linesep\
            + "End byte offset for the license text is {}.".format(summary_list[6]) +linesep\
            + "The found license text has the score of {:.3}".format(summary_list[7]) + linesep\
            + "The following text is found to be license text " + linesep\
            + "-----BEGIN-----" + linesep\
            + summary_list[8]\
            + "-----END-----" + linesep + linesep
        return output_str

    def analyze_file(self, input_fp, threshold=DEFAULT_THRESH_HOLD):
        input_dir = dirname(input_fp)
        list_of_src_str = self.get_str_from_file(input_fp)
        my_file_ng = ng.n_grams()
        my_file_ng.parse_text_list_items(list_text_line=list_of_src_str,
                                         universe_ng=self._universe_n_grams)
        similarity_score_dict = self.measure_similarity(my_file_ng)
        [matched_license, score] = self.find_best_match(similarity_score_dict)

        if score >= threshold:
            [start_ind, end_ind, start_offset, end_offset, region_score] = \
                self.find_license_region(matched_license, input_fp)
            found_region = list_of_src_str[start_ind:end_ind]
            found_region = ''.join(found_region)
            length = end_offset - start_offset + 1
            if region_score < threshold:
                matched_license = start_ind = start_offset = ''
                end_ind = end_offset = region_score = found_region = length = ''
        else:
            matched_license = start_ind = start_offset = ''
            end_ind = end_offset = region_score = found_region = length = ''
        lcs_match = license_match.LicenseMatch(file_name=input_fp,
                                file_path=input_fp,
                                license=matched_license,
                                start_byte=start_offset,
                                length = length)
        summary_list = [input_fp,
                        matched_license,
                        score,
                        start_ind,
                        end_ind,
                        start_offset,
                        end_offset,
                        region_score,
                        found_region]
        return lcs_match, summary_list

    def analyze_file_lcs_match_output(self, input_fp, threshold=DEFAULT_THRESH_HOLD):
        input_dir = dirname(input_fp)
        list_of_src_str = self.get_str_from_file(input_fp)
        my_file_ng = ng.n_grams()
        my_file_ng.parse_text_list_items(list_text_line=list_of_src_str,
                                         universe_ng=self._universe_n_grams)
        similarity_score_dict = self.measure_similarity(my_file_ng)
        [matched_license, score] = self.find_best_match(similarity_score_dict)

        if score >= threshold:
            [start_ind, end_ind, start_offset, end_offset, region_score] = \
                self.find_license_region(matched_license, input_fp)
            length = end_offset - start_offset + 1
            if region_score < threshold:
                matched_license = length = start_offset = ''
        else:
            matched_license = length = start_offset = ''
        lcs_match = license_match.LicenseMatch(file_name=input_fp,
                                file_path=input_fp,
                                license=matched_license,
                                start_byte=start_offset,
                                length = length)
        return lcs_match

    def analyze_input_path(self, input_path, threshold=DEFAULT_THRESH_HOLD):
        if isdir(input_path):
            return self.apply_function_on_all_files(self.analyze_file, input_path, threshold=threshold)
        elif isfile(input_path):
            return [self.analyze_file(input_path)]
        else:
            raise OSError('Neither file nor directory{}'.format(input_path))

    def analyze_input_path_lcs_match_output(self, input_path, threshold=DEFAULT_THRESH_HOLD):
        if isdir(input_path):
            return self.apply_function_on_all_files(self.analyze_file_lcs_match_output, input_path, threshold=threshold)
        elif isfile(input_path):
            return [self.analyze_file_lcs_match_output(input_path)]
        else:
            raise OSError('Neither file nor directory{}'.format(input_path))


    def apply_function_on_all_files(self, function_ptr, top_dir_name, *args, **kwargs):
        list_of_result = []
        for root, dirs, files in walk(top_dir_name):
            for file in files:
                list_of_result.append(function_ptr(join(root, file), *args, **kwargs))
        return list_of_result

    def find_license_region(self, license_name, input_fp):
        n_gram, license_dir = self.license_n_grams[license_name]
        license_fp = join(license_dir, license_name + '.txt')
        loc_finder = loc_id.Location_Finder()
        return loc_finder.main_process(license_fp, input_fp)

    def measure_similarity(self, input_ng):
        """
        Return the similarity measure.
        Assume that the license lookup is available.
        """
        similarity_dict = Counter()
        for license_name in self.license_n_grams:
            license_ng, license_dir = self.license_n_grams[license_name]
            similarity_score = license_ng.measure_similarity(input_ng)
            similarity_dict[license_name] = similarity_score
        return similarity_dict

    def find_best_match(self, scores):
        license_found = max(scores, key=scores.get)
        max_val = scores[max(scores, key=scores.get)]
        return license_found, max_val

    def get_str_from_file(self, file_path):
        fp = codecs.open(file_path, encoding='ascii', errors='surrogateescape')
        list_of_str = fp.readlines()
        fp.close()
        return list_of_str

def main():
    # threshold, license folder, input file, input folder, output format
    aparse = argparse.ArgumentParser(
        description="License text identification and license text region finder")
    aparse.add_argument("-T", "--threshold",
                        default=DEFAULT_THRESH_HOLD,
                        help="threshold hold for similarity measure (ranging from 0 to 1)")
    aparse.add_argument("-L", "--license_folder",
                        help="Specify directory path where the license text files are",
                        default=join(getcwd(), 'data', 'license_dir'))
    aparse.add_argument("-I", "--input_path",
                        help="Specify directory or file path where the input source code files are",
                        default=join(getcwd(), 'data', 'test', 'data'),
                        required=True)
    aparse.add_argument("-O", "--output_path",
                        help="Specify a file name path where the result will be saved for csv file.",
                        default=join(getcwd(), 'output.csv'))
    aparse.add_argument("-F", "--output_format",
        help="Format the output accordingly", action="append",
        choices=["csv", "easy_read"])
    args = aparse.parse_args()
    li_obj = license_identifier(license_dir=args.license_folder,
                                threshold=float(args.threshold),
                                input_path=args.input_path,
                                output_format=args.output_format,
                                output_path=args.output_path)

if __name__ == "__main__":
    main()
