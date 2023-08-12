# de-identifier
This package includes a Python class for removing Personal Identifiable Information (PII) from a given CSV file via two steps of scrubbing.

- The analyzer and anonymizer are defined based on [Microsoft Presidio](https://github.com/microsoft/presidio).
- Two Named entity recognitions (NER) are used including:
  1. The existing [spaCy](https://spacy.io/api/entityrecognizer) NER within Presidio package.
  2. [Flair](https://github.com/flairNLP/flair) NER.

- The final output is itself a CSV file. You may see the example Jupyter Notebook for reference.
