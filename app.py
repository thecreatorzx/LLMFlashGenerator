from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import PyPDF2
import os
import json
import pandas as pd
from transformers import T5Tokenizer, T5ForConditionalGeneration

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

model_name = "google/flan-t5-base"  
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        subject = request.form.get("subject", "General")
        text_input = request.form.get("text_input")
        file = request.files.get("file_input")

        if not text_input and not file:
            return render_template("index.html", error="Please provide text or a file.")
        if file and not (file.filename.endswith(".txt") or file.filename.endswith(".pdf")):
            return render_template("index.html", error="Only .txt and .pdf files are supported.")

        if file and file.filename:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            content = pdf_text_extract(file_path) if file.filename.endswith(".pdf") else file.read().decode("utf-8")
        else:
            content = text_input

        chunk_size = 1500
        content_chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
        all_flashcards = []
        for chunk in content_chunks[:2]:  
            flashcards = generate_flash(chunk, subject)
            all_flashcards.extend(flashcards)
        seen_questions = set()
        unique_flashcards = []
        for card in all_flashcards:
            if card['question'] not in seen_questions:
                unique_flashcards.append(card)
                seen_questions.add(card['question'])
        save_flash(unique_flashcards, subject)
        return render_template("flashcards.html", flashcards=unique_flashcards, subject=subject)
    return render_template("index.html")

def pdf_text_extract(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return " ".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def generate_flash(content, subject):
    prompt = f"""
    You are an expert educator creating flashcards for {subject}. Given the following educational content, generate 10-15 concise question-answer flashcards. Each flashcard should have:
    - A clear, concise question.
    - A factually correct, self-contained answer.
    - A difficulty level (Easy, Medium, Hard) based on complexity.
    - Group flashcards by detected topics if possible. If no clear topics are detected, use '{subject}' as the topic.
    Content: {content[:2000]}  # Limit to avoid memory issues
    Return the output as a JSON list of objects with 'question', 'answer', 'topic', and 'difficulty' fields. Ensure valid JSON format, wrapped in ```json\n...\n```.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            outputs = model.generate(
                inputs["input_ids"],
                max_length=1500,
                num_beams=4,
                early_stopping=True
            )
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            if response.startswith("```json") and response.endswith("```"):
                response = response[7:-3].strip()
            flashcards = json.loads(response)
            for card in flashcards:
                if 'topic' not in card or not card['topic']:
                    card['topic'] = subject
                if 'difficulty' not in card:
                    card['difficulty'] = 'Medium'
            return flashcards
        except json.JSONDecodeError:
            if attempt == max_retries - 1:
                return [{"question": "Error", "answer": "Failed to parse model response after retries", "topic": subject, "difficulty": "N/A"}]
            continue
        except Exception as e:
            return [{"question": "Error", "answer": f"Model error: {str(e)}", "topic": subject, "difficulty": "N/A"}]
def save_flash(flashcards, subject):
    df = pd.DataFrame(flashcards)
    df.to_csv(f"output/flashcards_{subject}.csv", index=False)
    with open(f"output/flashcards_{subject}.json", "w") as f:
        json.dump(flashcards, f, indent=2)
    with open(f"output/flashcards_{subject}.txt", "w") as f:
        for card in flashcards:
            f.write(f"{card['question']}\t{card['answer']}\n")

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)