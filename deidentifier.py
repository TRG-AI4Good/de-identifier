from presidio_analyzer import (
    BatchAnalyzerEngine,
    DictAnalyzerResult,
    RecognizerResult,
    EntityRecognizer,
    AnalysisExplanation,
    AnalyzerEngine,
    RecognizerRegistry)
from presidio_analyzer.nlp_engine import NlpArtifacts
from presidio_anonymizer import BatchAnonymizerEngine

try:
    from flair.data import Sentence
    from flair.models import SequenceTagger
except ImportError:
    print("Flair is not installed")

from typing import List, Dict, Iterable, Optional, Tuple, Set
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



        
class FlairRecognizer(EntityRecognizer):
    """
    Wrapper for a flair model, if needed to be used within Presidio Analyzer.

    :example:
    >from presidio_analyzer import AnalyzerEngine, RecognizerRegistry

    >flair_recognizer = FlairRecognizer()

    >registry = RecognizerRegistry()
    >registry.add_recognizer(flair_recognizer)

    >analyzer = AnalyzerEngine(registry=registry)

    >results = analyzer.analyze(
    >    "My name is Christopher and I live in Irbid.",
    >    language="en",
    >    return_decision_process=True,
    >)
    >for result in results:
    >    print(result)
    >    print(result.analysis_explanation)


    """

    ENTITIES = [
        "LOCATION",
        "PERSON",
        "ORGANIZATION",
        # "MISCELLANEOUS"   # - There are no direct correlation with Presidio entities.
    ]

    DEFAULT_EXPLANATION = "Identified as {} by Flair's Named Entity Recognition"

    CHECK_LABEL_GROUPS = [
        ({"LOCATION"}, {"LOC", "LOCATION"}),
        ({"PERSON"}, {"PER", "PERSON"}),
        ({"ORGANIZATION"}, {"ORG"}),
        # ({"MISCELLANEOUS"}, {"MISC"}), # Probably not PII
    ]

    MODEL_LANGUAGES = {
        "en": "flair/ner-english-large",
        "es": "flair/ner-spanish-large",
        "de": "flair/ner-german-large",
        "nl": "flair/ner-dutch-large",
    }

    PRESIDIO_EQUIVALENCES = {
        "PER": "PERSON",
        "LOC": "LOCATION",
        "ORG": "ORGANIZATION",
        # 'MISC': 'MISCELLANEOUS'   # - Probably not PII
    }

    def __init__(
        self,
        supported_language: str = "en",
        supported_entities: Optional[List[str]] = None,
        check_label_groups: Optional[Tuple[Set, Set]] = None,
        model: SequenceTagger = None,
    ):
        self.check_label_groups = (
            check_label_groups if check_label_groups else self.CHECK_LABEL_GROUPS
        )

        supported_entities = supported_entities if supported_entities else self.ENTITIES
        self.model = (
            model
            if model
            else SequenceTagger.load(self.MODEL_LANGUAGES.get(supported_language))
        )

        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            name="Flair Analytics",
        )

    def load(self) -> None:
        """Load the model, not used. Model is loaded during initialization."""
        pass

    def get_supported_entities(self) -> List[str]:
        """
        Return supported entities by this model.

        :return: List of the supported entities.
        """
        return self.supported_entities

    # Class to use Flair with Presidio as an external recognizer.
    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """
        Analyze text using Text Analytics.

        :param text: The text for analysis.
        :param entities: Not working properly for this recognizer.
        :param nlp_artifacts: Not used by this recognizer.
        :param language: Text language. Supported languages in MODEL_LANGUAGES
        :return: The list of Presidio RecognizerResult constructed from the recognized
            Flair detections.
        """

        results = []

        sentences = Sentence(text)
        self.model.predict(sentences)

        # If there are no specific list of entities, we will look for all of it.
        if not entities:
            entities = self.supported_entities

        for entity in entities:
            if entity not in self.supported_entities:
                continue

            for ent in sentences.get_spans("ner"):
                if not self.__check_label(
                    entity, ent.labels[0].value, self.check_label_groups
                ):
                    continue
                textual_explanation = self.DEFAULT_EXPLANATION.format(
                    ent.labels[0].value
                )
                explanation = self.build_flair_explanation(
                    round(ent.score, 2), textual_explanation
                )
                flair_result = self._convert_to_recognizer_result(ent, explanation)

                results.append(flair_result)

        return results

    def _convert_to_recognizer_result(self, entity, explanation) -> RecognizerResult:

        entity_type = self.PRESIDIO_EQUIVALENCES.get(entity.tag, entity.tag)
        flair_score = round(entity.score, 2)

        flair_results = RecognizerResult(
            entity_type=entity_type,
            start=entity.start_position,
            end=entity.end_position,
            score=flair_score,
            analysis_explanation=explanation,
        )

        return flair_results

    def build_flair_explanation(
        self, original_score: float, explanation: str
    ) -> AnalysisExplanation:
        """
        Create explanation for why this result was detected.

        :param original_score: Score given by this recognizer
        :param explanation: Explanation string
        :return:
        """
        explanation = AnalysisExplanation(
            recognizer=self.__class__.__name__,
            original_score=original_score,
            textual_explanation=explanation,
        )
        return explanation

    @staticmethod
    def __check_label(
        entity: str, label: str, check_label_groups: Tuple[Set, Set]
    ) -> bool:
        return any(
            [entity in egrp and label in lgrp for egrp, lgrp in check_label_groups]
        )