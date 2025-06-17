# 📚 Flashcard Generator using FLAN-T5

This project is a web-based **Flashcard Generator** powered by the `google/flan-t5-large` model. Users can input raw text or upload `.txt`/`.pdf` files, and the app will extract content to generate **concise flashcards** (question-answer pairs) with difficulty ratings.

---

## ✨ Features

- 🧠 Uses FLAN-T5 for generating meaningful flashcards
- 📁 Upload `.txt` or `.pdf` files
- 🖊️ Custom text input also supported
- 🔖 Flashcards tagged with `Easy`, `Medium`, or `Hard` difficulty
- 💾 Saves flashcards as `.csv`, `.json`, and `.txt`
- 💻 Simple web UI using Flask

---

## 📂 Project Structure

```

LLMFlashGenerator/
│
├── app.py # Main Flask backend
├── templates/
│ ├── index.html # Upload & input page
│ └── flashcards.html # Display generated flashcards
│
├── static/
│ └── style.css # Basic UI styling
│
├── uploads/ # Uploaded files (.txt/.pdf)
├── output/ # Output flashcards (CSV, JSON, TXT)
├── requirements.txt # Python dependencies
└── README.md # You're here!

```

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/LLMFlashGenerator.git
cd LLMFlashGenerator
```

### 2. Create a Python Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate       # On Linux/macOS
venv\Scripts\activate          # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you don’t have a `requirements.txt`, create one with:

```txt
flask
transformers
torch
pandas
PyPDF2
```

Then install with:

```bash
pip install flask transformers torch pandas PyPDF2
```

---

### 4. Run the App

```bash
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000
```

---

## 🧪 Sample Usage

You can enter text like:

```text
Binary trees are a type of data structure where each node has at most two children. Stacks and queues are used for linear data organization.
```

Or upload a `.pdf` file with educational content.

---

## 📤 Output

Flashcards will be saved in the `output/` folder in:

- `flashcards_<subject>.csv`
- `flashcards_<subject>.json`
- `flashcards_<subject>.txt`

Example `.txt` output:

```
Question: What is a binary tree?
Answer: A data structure where each node has at most two children.
```

---

## 🛠️ Notes

- Default model: `google/flan-t5-large`
- Requires ~13GB VRAM (if using CUDA GPU)
- If no GPU, performance may be slower (CPU fallback enabled)

---

```

```
