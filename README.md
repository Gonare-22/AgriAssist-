# AgriAssist Agent 

Diagnose crop issues from a **leaf photo or text symptoms**, then get **treatment steps** and **agentic follow-ups** like preventive schedules, store finder, and reminders.

## Features
- Image-based diagnosis using a pre-trained Plant Disease model (Hugging Face).
- Text symptom fallback (works even without the model).
- Built-in knowledge base for **offline/quick** advice (no API keys needed).
- Agentic actions: treatment steps, preventive care schedule, open Maps for nearby agri stores, demo reminders.
- Clean single-command run.

## Quickstart
```bash
# 1) Create & activate venv (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2) Install deps (Torch download may take time on first install)
pip install -r requirements.txt

# 3) (Optional) Faster demo without model load:
#    export DEMO_MODE=1   # Windows PowerShell: $env:DEMO_MODE="1"

# 4) Run
python app.py
```

Open http://localhost:5000 in your browser.

> If Torch installation is slow, set `DEMO_MODE=1` to skip the model and still get a working demo (text + rule-based stub). You can later unset it to enable the real classifier.

## Usage
- Provide **either** a leaf image **or** a text description of symptoms.
- The app returns a predicted issue, confidence, advice steps, and action buttons.
- Click **Find nearby agri store** to open a Google Maps search.
- **Preventive schedule** gives a 4-week plan.
- **Set reminder** shows a demo message (no background jobs).

## API (for Postman/cURL)
**Predict**
```bash
# Image
curl -F "file=@/path/to/leaf.jpg" -F "crop=Tomato" http://localhost:5000/predict

# Text description
curl -X POST -F "description=white powder on leaves" -F "crop=Cucumber" http://localhost:5000/predict
```

**Action**
```bash
curl -X POST http://localhost:5000/action \
  -H "Content-Type: application/json" \
  -d '{"action":"preventive_schedule", "crop":"Tomato", "disease":"Tomato___Early_blight"}'
```

## Notes
- The Hugging Face `nateraw/plant-disease-model` loads automatically when `DEMO_MODE` is not set.
- Advice is illustrative; always follow local labels and agricultural extension recommendations.
- You can customize `KNOWLEDGE_BASE` inside `app.py` to add more crops/diseases.
```

