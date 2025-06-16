# Flashcard Generator

The **Flashcard Generator** project utilizes a BART-based NLP model to automatically generate flashcards (question-answer pairs) from a given text. It provides a RESTful API endpoint to create flashcards based on user input. The project leverages natural language processing and deep learning techniques (NLTK, Transformers, Sentence-BERT) to extract relevant information and produce high-quality flashcards for efficient learning.

---

## Features

- Tokenize the input text into sentences using the `nltk` library.
- Generate questions from each sentence using the `text2text-generation` pipeline (T5-based language models).
- Rank the generated questions based on their relevance using **Sentence-BERT** (sentence embeddings).
- Select the most significant questions based on the ranking.
- Find accurate answers to the selected questions within the input text using a **BART-based** model.
- Create a set of flashcards, each containing a generated question and its corresponding answer.

---

## Requirements

- Python 3.x
- `nltk` – Natural Language Toolkit for text processing and tokenization
- `transformers` – Hugging Face Transformers library (to load BART and tokenizer)
- `torch` – PyTorch (deep learning framework)
- `sentence-transformers` – Sentence Transformer library (for encoding questions and computing similarity scores)
- `flask` – Flask web framework (for API endpoint)

---

## Setup Instructions

1. **Clone the repository:**

   bash
   git clone https://github.com/your-username/Flashcard-Generator.git
   cd Flashcard-Generator

2. **Install dependencies:**

   bash
   pip install flask transformers sentence-transformers nltk

3. **Download NLTK data (if needed):**

   bash
   python -m nltk.downloader punkt

   The NLTK `punkt` tokenizer data is required for sentence tokenization.

---

## Usage

1. **Run the API:**

   bash
   python app.py

   This starts the Flask server on `http://localhost:5000`.

2. **Send a POST request** to the `/generate_flashcards` endpoint with a JSON payload.

   - **Endpoint:**  
     `http://localhost:5000/generate_flashcards`

   - **Request Body (JSON):**

     json
     {
     "num_flashcards_limit": 5,
     "text": "Enter your text here."
     }

   - Replace `"Enter your text here."` with the content you want to generate flashcards from.
   - Set `num_flashcards_limit` to the number of flashcards you wish to receive.

3. **Parameters:**

   - `text` (string): The input text from which flashcards will be generated.
   - `num_flashcards_limit` (integer): The number of flashcards to create.

4. **Example Response:**

   json
   {
   "flashcards": [
   {
   "question": "Question 1",
   "answer": "Answer 1"
   },
   {
   "question": "Question 2",
   "answer": "Answer 2"
   }
   ]
   }

---

## Example Flashcard

Question: What is the capital of France?
Answer: Paris

---

## Project Structure

.
├── app.py # Flask API for flashcard generation
├── main.py # Core functionality (question/answer generation)
├── BulletPoints.py # (Additional script, e.g. for preprocessing)
├── requirements.txt # Python dependencies
└── README.md # This documentation

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
