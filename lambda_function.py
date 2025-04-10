# lambda_function.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

model_id = "google/flan-t5-xl"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

def lambda_handler(event, context=None):
    input_text = event.get("text", "")
    if not input_text:
        return {"error": "No text provided"}

    inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=512)
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return {"summary": summary}
