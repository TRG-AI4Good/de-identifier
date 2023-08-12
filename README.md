# De-identifier
This package includes a Python class for removing Personally Identifiable Information (PII) from a given CSV file using two levels of scrubbing.

- The analyzer and anonymizer are defined based on [Microsoft Presidio](https://github.com/microsoft/presidio).
- Two Named Entity Recognition (NER) methods are used, including:
  1. The existing [spaCy](https://spacy.io/api/entityrecognizer) NER within the Presidio package.
  2. [Flair](https://github.com/flairNLP/flair) NER.

- The `CSVDeidentifier` class is a modified version of the [sample code](https://github.com/microsoft/presidio/blob/main/docs/samples/python/process_csv_file.py) provided by Presidio. The constructor of the class accepts the following arguments:

  1. `input_csv_path`: The path to the input CSV file.
  2. `output_csv_path`: The path to the output CSV file.
  3. `language`: Supported languages are 'en', 'es', 'de', 'nl'.
  4. `entities` (optional): A list of entities.
  5. `add_flair` (optional): A boolean indicating whether to use Flair for NER or not.
  6. `lower_case` (optional): A boolean indicating whether to convert words to lowercase before analysis or not.

- The  `FlairRecognizer` class is based on the [sample code](https://github.com/microsoft/presidio/blob/main/docs/samples/python/flair_recognizer.py) provided by Presidio without much modification.
- The final output is a CSV file. You can refer to the example Jupyter Notebook for guidance.
