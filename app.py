#!/usr/bin/env python3
import os
import io
import json
from datetime import datetime
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="templates")

DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

# Try to load HF image classifier (optional for demo)
classifier = None
try:
    if not DEMO_MODE:
        from transformers import pipeline  # type: ignore
        classifier = pipeline("image-classification", model="nateraw/plant-disease-model")
        print("[INFO] Loaded Hugging Face plant disease model.")
    else:
        print("[INFO] DEMO_MODE=1: Skipping model load; using rule-based stub.")
except Exception as e:
    print(f"[WARN] Could not load HF model, falling back to stub. Reason: {e}")

# Simple knowledge base for advice (quick, no-API)
KNOWLEDGE_BASE = {
    "Apple___Apple_scab": {
        "friendly": "Apple Scab",
        "advice": [
            "Remove and destroy fallen leaves to reduce spores.",
            "Apply a fungicide containing captan or sulfur at early season if permitted.",
            "Improve airflow by pruning to keep foliage dry."
        ]
    },
    "Apple___Black_rot": {
        "friendly": "Apple Black Rot",
        "advice": [
            "Prune out cankers during dormancy and destroy infected material.",
            "Avoid overhead irrigation; keep fruit dry.",
            "Use labeled fungicides (e.g., myclobutanil) if local guidance allows."
        ]
    },
    "Tomato___Early_blight": {
        "friendly": "Tomato Early Blight",
        "advice": [
            "Remove lower leaves touching soil; mulch to prevent splash.",
            "Spray mancozeb or chlorothalonil per label; rotate with copper for resistance management.",
            "Follow a 7–10 day spray interval during humid periods."
        ]
    },
    "Tomato___Late_blight": {
        "friendly": "Tomato Late Blight",
        "advice": [
            "Immediately remove and destroy infected plants.",
            "Protect nearby plants with labeled fungicides (e.g., chlorothalonil).",
            "Avoid working plants when wet; sanitize tools."
        ]
    },
    "Powdery_Mildew": {
        "friendly": "Powdery Mildew (suspected)",
        "advice": [
            "Increase spacing and airflow; avoid overhead watering.",
            "Use potassium bicarbonate, sulfur, or neem oil as labeled.",
            "Rotate crops to break pathogen cycle."
        ]
    },
    "Nitrogen_Deficiency": {
        "friendly": "Nitrogen Deficiency (suspected)",
        "advice": [
            "Apply a balanced N fertilizer (e.g., urea 46-0-0) at recommended rates.",
            "Incorporate compost or green manure to improve soil health.",
            "Split applications to avoid leaching."
        ]
    },
    "Leaf_Spot": {
        "friendly": "Leaf Spot (general)",
        "advice": [
            "Remove infected leaves and debris; sanitize tools.",
            "Use copper-based fungicides as labeled if disease pressure is high.",
            "Water at soil level, not from above."
        ]
    },
    "Pest_Damage": {
        "friendly": "Chewing/Pest Damage (suspected)",
        "advice": [
            "Scout at dawn/dusk for caterpillars or beetles; hand-pick where possible.",
            "Apply Bacillus thuringiensis (Bt) for caterpillars or spinosad per label.",
            "Use sticky traps and encourage beneficial insects."
        ]
    },
    "Generic": {
        "friendly": "Issue detected",
        "advice": [
            "Isolate affected plants to limit spread.",
            "Improve irrigation timing (morning), and ensure good airflow.",
            "Consider sending a sample to an extension lab for confirmation."
        ]
    }
}

def classify_from_text(description: str):
    d = description.lower()
    if "powdery" in d or "white dust" in d:
        label = "Powdery_Mildew"
        score = 0.85
    elif "yellow" in d and "vein" in d:
        label = "Nitrogen_Deficiency"
        score = 0.8
    elif "holes" in d or "chew" in d or "eaten" in d:
        label = "Pest_Damage"
        score = 0.75
    elif "spots" in d or "specks" in d:
        label = "Leaf_Spot"
        score = 0.7
    else:
        label = "Generic"
        score = 0.6
    return {"label": label, "score": score}

def predict_from_image(image: Image.Image):
    if classifier is not None:
        preds = classifier(image)
        best = preds[0]
        return {"label": best["label"], "score": float(best["score"])}
    # Fallback stub when model unavailable
    return {"label": "Leaf_Spot", "score": 0.66}

def advice_for(label: str):
    item = KNOWLEDGE_BASE.get(label, KNOWLEDGE_BASE["Generic"])
    return {
        "title": item["friendly"],
        "steps": item["advice"]
    }

def next_actions():
    return [
        {"id": "treatment_steps", "label": "Show treatment steps"},
        {"id": "preventive_schedule", "label": "Preventive care schedule"},
        {"id": "find_store", "label": "Find nearby agri store"},
        {"id": "set_reminder", "label": "Set follow-up reminder (demo)"}
    ]

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    crop = request.form.get("crop") or "Crop"
    description = request.form.get("description", "").strip()
    file = request.files.get("file", None)

    pred = None
    if file and file.filename:
        try:
            image = Image.open(file.stream).convert("RGB")
            pred = predict_from_image(image)
        except Exception as e:
            pred = {"label": "Generic", "score": 0.5, "error": f"Image parse error: {e}"}
    elif description:
        pred = classify_from_text(description)
    else:
        return jsonify({"ok": False, "error": "Provide an image or description."}), 400

    label = pred["label"]
    info = advice_for(label)

    resp = {
        "ok": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "crop": crop,
        "prediction": {
            "label": label,
            "friendly": info["title"],
            "confidence": round(pred["score"], 3)
        },
        "advice": info["steps"],
        "actions": next_actions()
    }
    return jsonify(resp)

@app.route("/action", methods=["POST"])
def action():
    data = request.get_json(force=True)
    action_id = data.get("action")
    crop = data.get("crop", "Crop")
    disease = data.get("disease", "Issue")

    if action_id == "treatment_steps":
        info = advice_for(disease)
        return jsonify({
            "ok": True,
            "type": "treatment_steps",
            "title": f"Treatment for {info['title']}",
            "steps": info["steps"]
        })

    if action_id == "preventive_schedule":
        schedule = [
            "Week 1: Prune for airflow; remove debris.",
            "Week 2: Apply preventive spray if high humidity; mulch to reduce splash.",
            "Week 3: Scout twice weekly; water early morning at soil line.",
            "Week 4: Rotate with a different mode-of-action or switch to organic spray."
        ]
        return jsonify({
            "ok": True,
            "type": "preventive_schedule",
            "title": f"Preventive schedule for {crop}",
            "schedule": schedule
        })

    if action_id == "find_store":
        query = "agriculture input store pesticide fertilizer near me"
        maps_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        return jsonify({
            "ok": True,
            "type": "find_store",
            "title": "Nearby Agri Stores",
            "maps_url": maps_url
        })

    if action_id == "set_reminder":
        # Demo only: no persistence; frontend can simulate a toast/alert
        return jsonify({
            "ok": True,
            "type": "set_reminder",
            "title": "Reminder scheduled (demo)",
            "message": "We will remind you in 7 days to rescout your crop. (Demo only; no notifications)"
        })

    return jsonify({"ok": False, "error": "Unknown action"}), 400

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
