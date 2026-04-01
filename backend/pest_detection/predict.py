import onnxruntime as ort
import numpy as np
import io
import json
from PIL import Image

session = None
classes = {}

def load_model():
    global session, classes
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession("backend/models/best1.onnx", sess_options=opts)
    with open("backend/models/classes.json", "r") as f:
        classes = json.load(f)


def preprocess(image):
    image = image.resize((736, 736))
    img = np.array(image) / 255.0
    img = img.transpose(2, 0, 1)
    img = np.expand_dims(img, axis=0).astype(np.float32)
    return img


def predict(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    input_tensor = preprocess(image)
    
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: input_tensor})
    
    # YOLOv8 format: [1, 17, 8400] for 13 classes + 4 boxes
    # or similar. We extract the scores.
    output = outputs[0] 
    if output.shape[1] > output.shape[2]: # Transpose if 8400 is in Axis 1
        output = output.transpose(0, 2, 1)
    
    # Simple max score picker
    # Boxes: index 0-3, Classes: 4 onwards
    scores = output[0, 4:, :] # Shape [num_classes, 8400]
    
    max_scores = np.max(scores, axis=0) # [8400]
    best_idx = np.argmax(max_scores)
    
    best_score = max_scores[best_idx]
    best_class_idx = np.argmax(scores[:, best_idx])
    
    if best_score < 0.25:
        return {
            "pest": "No pest detected",
            "confidence": round(float(best_score), 4),
            "advice": "The plant looks healthy. Keep monitoring!"
        }

    pest_name = classes.get(str(best_class_idx), "Unknown Pest")
    
    advice_map = {
        "aphids": "Spray with neem oil or insecticidal soap.",
        "armyworm": "Use Bacillus thuringiensis (Bt) or Spinosad sprays.",
        "beetle": "Handpick beetles or use neem oil.",
        "bollworm": "Pheromone traps and Chlorantraniliprole spray.",
        "grasshopper": "Apply Metarhizium anisopliae or carbaryl bait.",
        "mites": "Mist water frequently; use miticides if severe.",
        "mosquito": "Clear stagnant water near the farm.",
        "sawfly": "Remove larvae by hand or use insecticidal soap.",
        "stem borer": "Cut affected stalks; apply Fipronil granules.",
        "caterpillar": "Use neem oil or mechanical removal.",
        "wasp": "Benefitial insects; generally no control needed.",
        "snails": "Use iron phosphate pellets or beer traps."
    }

    return {
        "pest": pest_name,
        "confidence": round(float(best_score), 4),
        "advice": advice_map.get(pest_name.lower(), "Consult local agri-expert for specific treatment.")
    }