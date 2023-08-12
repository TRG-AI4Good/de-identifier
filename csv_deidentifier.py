from presidio_analyzer import (
    BatchAnalyzerEngine,
    DictAnalyzerResult,
    AnalyzerEngine,
    RecognizerRegistry)
from presidio_anonymizer import BatchAnonymizerEngine
from flair_recognizer import FlairRecognizer

from typing import List, Dict, Iterable, Optional
import csv


class CSVDeidentifier(BatchAnalyzerEngine, BatchAnonymizerEngine):

    def __init__(self,
                 input_csv_path: str,
                 output_csv_path: str,
                 language: str,
                 entities: List[str] = None,
                 add_flair= False,
                 lower_case= False, *args, **kwargs):

        if add_flair:
            flair_recognizer = (
            FlairRecognizer()
            )  # This would download a very large (+2GB) model on the first run

            registry = RecognizerRegistry()
            registry.add_recognizer(flair_recognizer)
            analyzer_spaCy_flair = AnalyzerEngine(registry=registry)

            BatchAnalyzerEngine.__init__(self, analyzer_engine=analyzer_spaCy_flair)
        else:
            BatchAnalyzerEngine.__init__(self)

        BatchAnonymizerEngine.__init__(self)
        self.input_csv_path = input_csv_path
        self.output_csv_path = output_csv_path
        self.language = language
        self.lower_case = lower_case
        self.entities = entities

    def analyze_csv(
        self,
        keys_to_skip: Optional[List[str]] = None
    ) -> Iterable[DictAnalyzerResult]:

        with open(self.input_csv_path, 'r') as csv_file:
            csv_list = list(csv.reader(csv_file))
            if self.lower_case:
                csv_list = [[element.lower() if "<" not in element else element for element in csv_row] for csv_row in csv_list]
            
            csv_dict = {header: list(map(str, values)) for header, *values in zip(*csv_list)}
            analyzer_results = self.analyze_dict(csv_dict, self.language, keys_to_skip, entities = self.entities)
            return list(analyzer_results)
        
    def anonymize_csv(
            self,
            **kwargs) -> Dict[str, str]:
        anonymizer_results = self.anonymize_dict(self.analyze_csv(), **kwargs)
        return anonymizer_results


    def write_output(
            self) -> None:
        
        anonymizer_results = self.anonymize_csv()

        # Get the headers
        headers = list(anonymizer_results.keys())

        # Convert the dictionary to a list of dictionaries (rows)
        rows = [dict(zip(headers, row)) for row in zip(*anonymizer_results.values())]

        with open(self.output_csv_path, 'w') as csv_output_file:
            writer = csv.DictWriter(csv_output_file, headers)
            writer.writeheader()  # Writing headers
            writer.writerows(rows)
            
    def run(self) -> None:
        self.write_output()
