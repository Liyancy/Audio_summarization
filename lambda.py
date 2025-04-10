from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_id = "google/flan-t5-xl"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

# Sample input (replace this with your transcription chunk)
input_text = "Summarize this: A long time ago, in a galaxy far far away, there lived a Jedi knight..."

# Prepare input for the model
inputs = tokenizer(input_text, return_tensors="pt", truncation=True)

# Generate summary (adjust max_new_tokens based on expected length)
outputs = model.generate(**inputs, max_new_tokens=512)

# Decode and print the summary
summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("Summary:\n", summary)


model_id = "google/flan-t5-xl"
config_file = cached_file(model_id, "config.json")
print("Model is cached at:", config_file)


