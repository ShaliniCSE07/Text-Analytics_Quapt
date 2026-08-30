from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

print("Loading summarization model...")
model_name = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
print("Summarization model loaded.")

def generate_summary(reviews: list, max_reviews: int = 20) -> str:
    if not reviews:
        return "No reviews available to summarize."
        
    selected_reviews = reviews[:max_reviews]
    combined_text = ". ".join(selected_reviews)
    
    words = combined_text.split()
    if len(words) > 750:
        combined_text = " ".join(words[:750])
        
    try:
        inputs = tokenizer([combined_text], max_length=1024, return_tensors="pt", truncation=True)
        summary_ids = model.generate(
            inputs["input_ids"], 
            max_length=100, 
            min_length=30, 
            length_penalty=2.0, 
            num_beams=4, 
            early_stopping=True
        )
        return tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Summarization error: {e}")
        return "An error occurred during summarization. The input text might be too long."

