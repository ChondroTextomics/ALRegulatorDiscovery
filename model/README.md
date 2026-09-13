# Model

The trained PubMedBERT classifier for chondrogenesis regulator identification is hosted on the Hugging Face Hub (not committed to this repository):

🤗 **[pubmedbert-chondrogenesis-classifier](https://huggingface.co/amav/pubmedbert-chondrogenesis-classifier)**

Load it directly with `transformers`:

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model = AutoModelForSequenceClassification.from_pretrained("amav/pubmedbert-chondrogenesis-classifier")
tokenizer = AutoTokenizer.from_pretrained("amav/pubmedbert-chondrogenesis-classifier")
```

See the model card on the Hugging Face page for details on training, intended use, and performance.
