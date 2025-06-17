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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

model_name = "google/flan-t5-large"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)

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
            content = extract_text_from_pdf(file_path) if file.filename.endswith(".pdf") else open(file_path, "r", encoding="utf-8").read()
        else:
            content = text_input

        if not content.strip():
            return render_template("index.html", error="Input content is empty.")

        chunk_size = 1000
        content_chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
        
        all_flashcards = []
        for chunk in content_chunks[:3]:  # Use first 3 chunks to get ~10+ cards
            flashcards = generate_flash(chunk, subject)
            all_flashcards.extend(flashcards)

        # Deduplicate based on questions
        seen_questions = set()
        unique_flashcards = []
        for card in all_flashcards:
            if card["question"] not in seen_questions:
                unique_flashcards.append(card)
                seen_questions.add(card["question"])

        save_flashcards(unique_flashcards, subject)
        return render_template("flashcards.html", flashcards=unique_flashcards, subject=subject)
    return render_template("index.html")

def extract_text_from_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return " ".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def generate_flash(content, subject):
    prompt = f"""
You are a helpful AI that generates study flashcards from educational text. Based on the topic "{subject}", extract exactly 5 flashcards from the following content.

Each flashcard must strictly follow this format:
Question: <Your question>
Answer: <Concise and accurate answer>
Difficulty: <Easy/Medium/Hard>

Only output the 5 flashcards, no explanations or introductions.

Content:
\"\"\"
{content.strip()[:800]}
\"\"\"
"""

    try:
        inputs = tokenizer(prompt, return_tensors="pt", max_length=768, truncation=True).to(device)
        outputs = model.generate(
            inputs["input_ids"],
            max_length=1024,
            num_beams=4,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            early_stopping=True
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("\n===== FLAN-T5 OUTPUT =====\n" + response)

        flashcards = []
        blocks = response.strip().split("\n\n")
        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            question = answer = difficulty = ""
            for line in lines:
                if line.lower().startswith("question:"):
                    question = line.split(":", 1)[1].strip()
                elif line.lower().startswith("answer:"):
                    answer = line.split(":", 1)[1].strip()
                elif line.lower().startswith("difficulty:"):
                    diff = line.split(":", 1)[1].strip().capitalize()
                    if diff in ["Easy", "Medium", "Hard"]:
                        difficulty = diff
            if question and answer:
                flashcards.append({
                    "question": question,
                    "answer": answer,
                    "topic": subject,
                    "difficulty": difficulty or "Medium"
                })

        # If still none parsed, return fallback
        return flashcards if flashcards else fallback_card(content, subject)

    except Exception as e:
        print(f"Model error: {str(e)}")
        return fallback_card(content, subject)


def fallback_card(content, subject):
    fallback_question = "What is a key point mentioned in the content?"
    fallback_answer = content.strip().split(".")[0] + "." if "." in content else content.strip()
    return [{
        "question": fallback_question,
        "answer": fallback_answer,
        "topic": subject,
        "difficulty": "Medium"
    }]

def save_flashcards(flashcards, subject):
    df = pd.DataFrame(flashcards)
    df.to_csv(f"{OUTPUT_FOLDER}/flashcards_{subject}.csv", index=False)
    with open(f"{OUTPUT_FOLDER}/flashcards_{subject}.json", "w") as f:
        json.dump(flashcards, f, indent=2)
    with open(f"{OUTPUT_FOLDER}/flashcards_{subject}.txt", "w") as f:
        for card in flashcards:
            f.write(f"{card['question']}\t{card['answer']}\n")

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
