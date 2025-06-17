from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import PyPDF2
import os
import json
import pandas as pd
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create directories if they don't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Set device (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")  # Debug: Confirm device

# Load Flan-T5 model and tokenizer
model_name = "google/flan-t5-small"  # Lightweight model
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        subject = request.form.get("subject", "General")
        text_input = request.form.get("text_input")
        file = request.files.get("file_input")

        # Input validation
        if not text_input and not file:
            return render_template("index.html", error="Please provide text or a file.")
        if file and not (file.filename.endswith(".txt") or file.filename.endswith(".pdf")):
            return render_template("index.html", error="Only .txt and .pdf files are supported.")

        # Extract content
        if file and file.filename:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            content = extract_text_from_pdf(file_path) if file.filename.endswith(".pdf") else open(file_path, "r", encoding="utf-8").read()
        else:
            content = text_input

        if not content.strip():
            return render_template("index.html", error="Input content is empty.")

        # Chunk content for Flan-T5
        chunk_size = 1000
        content_chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
        all_flashcards = []
        for chunk in content_chunks[:2]:  # Limit to 2 chunks
            flashcards = generate_flash(chunk, subject)
            all_flashcards.extend(flashcards)
        # Remove duplicates based on question
        seen_questions = set()
        unique_flashcards = []
        for card in all_flashcards:
            if card['question'] not in seen_questions:
                unique_flashcards.append(card)
                seen_questions.add(card['question'])

        save_flashcards(unique_flashcards, subject)
        return render_template("flashcards.html", flashcards=unique_flashcards, subject=subject)
    return render_template("index.html")

# Extract text from a PDF file using PyPDF2
def extract_text_from_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return " ".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

# Generate flashcards using Flan-T5
def generate_flash(content, subject):
    prompt = f"""
Generate 5-10 flashcards for {subject} from this content: {content[:1000]}. Each flashcard should have a question, answer, and difficulty (Easy, Medium, Hard). Use '{subject}' as the topic for all flashcards. Return valid JSON in ```json\n...\n```.
Example:
```json
[{{"question": "What is X?", "answer": "X is Y.", "topic": "{subject}", "difficulty": "Easy"}}]
```
"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True).to(device)
            outputs = model.generate(
                inputs["input_ids"],
                max_length=800,
                num_beams=4,
                early_stopping=True
            )
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"Flan-T5 response: {response}")  # Debug: Inspect model output
            # Extract JSON from response
            if response.startswith("```json") and response.endswith("```"):
                response = response[7:-3].strip()
            flashcards = json.loads(response)
            # Ensure all flashcards have required fields
            for card in flashcards:
                if 'topic' not in card or not card['topic']:
                    card['topic'] = subject
                if 'difficulty' not in card:
                    card['difficulty'] = 'Medium'
            return flashcards[:10]
        except json.JSONDecodeError:
            if attempt == max_retries - 1:
                # Fallback: Generate minimal flashcard
                return [
                    {
                        "question": "What is the main topic of the content?",
                        "answer": f"The content focuses on {subject}.",
                        "topic": subject,
                        "difficulty": "Easy"
                    }
                ]
        except Exception as e:
            return [{"question": "Error", "answer": f"Model error: {str(e)}", "topic": subject, "difficulty": "N/A"}]

# Save flashcards to CSV, JSON, and Anki-compatible text
def save_flashcards(flashcards, subject):
    # Save as CSV
    df = pd.DataFrame(flashcards)
    df.to_csv(f"output/flashcards_{subject}.csv", index=False)
    # Save as JSON
    with open(f"output/flashcards_{subject}.json", "w") as f:
        json.dump(flashcards, f, indent=2)
    # Save as Anki (tab-separated)
    with open(f"output/flashcards_{subject}.txt", "w") as f:
        for card in flashcards:
            f.write(f"{card['question']}\t{card['answer']}\n")

# Route for downloading files
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)