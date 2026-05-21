# GP-Maker 🎓

A web tool for **Saveetha University students** to automate the weekly **Guru Padigam (GP)** mentor presentation process — saving time by automatically processing mentor-sent PPTs and generating a filled PDF ready to submit.

---

## What is Guru Padigam (GP)?

**Guru Padigam** is a weekly mentorship activity at Saveetha University where:

- The **mentor** sends a PowerPoint presentation (PPTX) to their mentees each week.
- The **student (mentee)** is required to:
  1. Delete all slides **except the last 3**.
  2. Fill in the last slide with their **own response** (what they want from this mentorship).
  3. Fill in a **parent/guardian response** as well.
  4. Submit the final document as a **PDF** to the mentor.

This process is **repetitive and time-consuming** when done manually every week. **GP-Maker automates it entirely.**

---

## What GP-Maker Does

1. **Upload** — The student uploads the PPTX file sent by their mentor.
2. **Select Responses** — The student selects quick-response tags (or types custom responses) for:
   - Their own mentee response (e.g., *Exam Prep*, *Better Marks*, *Job Skills*)
   - Their parent's response (e.g., *Happy*, *Good Change*, *Check Marks*)
3. **Generate** — GP-Maker automatically:
   - Removes all slides except the **last 3**
   - Fills the last slide with the selected mentee and parent responses
   - Exports the result as a **PDF** — the format required by mentors

---

## Tech Stack

| File | Purpose |
|------|---------|
| `app.py` | Flask web application — handles routing and file uploads |
| `ppt_processor.py` | Core logic — strips slides, fills response fields, exports PDF |
| `Dockerfile` | Containerized deployment configuration |
| `render.yaml` | Deployment config for [Render.com](https://render.com) |
| `requirements.txt` | Python dependencies |

---

## How to Run Locally

### Prerequisites

- Python 3.9+
- LibreOffice (for PPTX → PDF conversion)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/dharanigovardhan2008/GP-Maker.git
cd GP-Maker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Then open your browser at `http://localhost:5000`.

---

## How to Use

1. Open the web app.
2. **Step 1 — Upload** your mentor's PPTX file (max 50MB).
3. **Step 2 — Student Response** — Click a quick-response tag or type your own response in the box.
4. **Step 3 — Parent Feedback** — Click a quick-response tag or type your parent's response.
5. Click **Generate** — your filled PDF will be ready to download and submit to your mentor.

---

## Deployment

This project is configured for deployment on **Render.com** using the included `render.yaml` and `Dockerfile`.

To deploy:

1. Push your code to GitHub.
2. Connect your GitHub repo to [Render.com](https://render.com).
3. Render will auto-detect the `render.yaml` config and deploy.

---

## Contributing

Pull requests are welcome! If you find a bug or want to add features (e.g., support for more response categories, multi-language support), feel free to open an issue or PR.

---

## Author

**Dharani Govardhan** — [@dharanigovardhan2008](https://github.com/dharanigovardhan2008)

---

## License

This project is open source and available under the [MIT License](LICENSE).
