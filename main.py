import os
import cv2
import json
import numpy as np
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
from ultralytics import YOLO

# Paths
INPUT_FOLDER = "dataset/cheques"
CROPS_FOLDER = "detected_fields"
OCR_FOLDER = "ocr_results"
JSON_FOLDER = "final_output_json"
MODEL_PATH = "runs/detect/train3/weights/best.pt"

FIELD_CLASSES = ['Cheque_Number', 'Account_Number', 'IFSC_Code', 'Date', 'Amount', 'Payee_Name']

# Initialize models with proper device handling
def initialize_models():
    """Initialize models with proper device handling"""
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")

        # Ensure model weights exist before trying to load
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"YOLO weights not found at: {MODEL_PATH}")

        yolo_model = YOLO(MODEL_PATH)

        # Load TrOCR and move to device
        trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-large-handwritten').to(device)
        processor_local = TrOCRProcessor.from_pretrained('microsoft/trocr-large-handwritten')

        return yolo_model, trocr_model, processor_local, device

    except ImportError as ie:
        raise ImportError(f"Missing package required for models: {ie}") from ie
    except Exception as e:
        raise RuntimeError(f"Failed to initialize models: {e}") from e

def enhance_image(image):
    """Enhance image for better OCR results"""
    try:
        # Check image size
        height, width = image.shape[:2]
        if height * width > 4000 * 4000:
            # Resize to more manageable size
            scale = min(4000/height, 4000/width)
            image = cv2.resize(image, None, fx=scale, fy=scale)
        
        # Resize (2x)
        image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Convert to LAB and apply CLAHE
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    except Exception as e:
        print(f"Enhancement failed: {str(e)}")
        return image  # Return original if enhancement fails

    return enhanced

def extract_text_trocr(image, device):
    """Extract text using TrOCR. `device` must be same device used to load the model."""
    # Convert CV2 image to PIL
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)

    # Prepare image for model
    inputs = processor(pil_image, return_tensors="pt")
    pixel_values = inputs.pixel_values.to(device)

    # Generate text in no_grad for memory/speed
    with torch.no_grad():
        generated_ids = trocr_model.generate(pixel_values, max_length=256, num_beams=4)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return generated_text.strip()

def run_pipeline(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        image_name = os.path.splitext(os.path.basename(image_path))[0]
        results = model(image_path)
        if len(results) == 0:
            print(f"⚠️ No inference results for {image_path}")
            return True

        detections = results[0].boxes
        if detections is None or len(detections) == 0:
            print(f"⚠️ No boxes detected for {image_path}")
            return True

        # Ensure output dirs exist
        os.makedirs(CROPS_FOLDER, exist_ok=True)
        os.makedirs(OCR_FOLDER, exist_ok=True)
        os.makedirs(JSON_FOLDER, exist_ok=True)

        output_json = {}

        for i, box in enumerate(detections):
            # robust class id extraction
            cls_val = getattr(box, "cls", None)
            try:
                if isinstance(cls_val, (list, tuple)):
                    cls_id = int(cls_val[0])
                elif hasattr(cls_val, "item"):
                    cls_id = int(cls_val.item())
                else:
                    cls_id = int(cls_val)
            except Exception:
                continue

            if cls_id < 0 or cls_id >= len(FIELD_CLASSES):
                continue
            class_name = FIELD_CLASSES[cls_id]

            # robust xy extraction
            xy = getattr(box, "xyxy", None)
            if xy is None:
                continue

            # xy could be tensor shape (4,) or (1,4) or numpy
            try:
                coords = xy[0] if len(xy) > 1 else xy
            except Exception:
                coords = xy

            # convert to list of floats/ints
            try:
                coords_arr = coords.cpu().numpy() if hasattr(coords, "cpu") else np.array(coords)
                x1, y1, x2, y2 = map(int, coords_arr.flatten().tolist()[:4])
            except Exception:
                continue

            # clamp to image bounds
            h, w = image.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x2 <= x1 or y2 <= y1:
                continue

            cropped = image[y1:y2, x1:x2]
            if cropped is None or cropped.size == 0:
                continue

            enhanced_crop = enhance_image(cropped)

            # Save cropped and enhanced image
            crop_path = os.path.join(CROPS_FOLDER, f"{image_name}_{class_name}.jpg")
            cv2.imwrite(crop_path, enhanced_crop)

            # Extract text using TrOCR (ensure device variable is available)
            text = extract_text_trocr(enhanced_crop, DEVICE)
            print(f"✅ {class_name}: {text}")

            # Save to text file
            ocr_txt_path = os.path.join(OCR_FOLDER, f"{image_name}_{class_name}.txt")
            safe_write_file(ocr_txt_path, text)

            output_json[class_name.lower()] = text

        # Save to final JSON
        json_path = os.path.join(JSON_FOLDER, f"{image_name}.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(output_json, jf, indent=4)

        print(f"✅ Processed: {image_path}")
        return True
    except Exception as e:
        print(f"❌ Error processing {image_path}: {str(e)}")
        return False

def safe_write_file(file_path, content, mode='w'):
    """Safely write content to file"""
    try:
        dirname = os.path.dirname(file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
    except PermissionError:
        print(f"❌ Permission denied: Cannot write to {file_path}")
        return False
    except Exception as e:
        print(f"❌ Error writing file {file_path}: {str(e)}")
        return False
    return True

def process_all():
    total_images = len([f for f in os.listdir(INPUT_FOLDER) 
                       if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif"))])
    processed = 0
    failed = 0
    
    try:
        validate_paths()
        for img_file in os.listdir(INPUT_FOLDER):
            if img_file.lower().endswith((".jpg", ".jpeg", ".png", ".tif")):
                success = run_pipeline(os.path.join(INPUT_FOLDER, img_file))
                processed += 1
                if not success:
                    failed += 1
                print(f"Progress: {processed}/{total_images}")
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
    finally:
        print(f"📊 Summary: Processed {processed} images, {failed} failed")

def validate_paths():
    """Validate all required paths and files"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    if not os.path.exists(INPUT_FOLDER):
        raise FileNotFoundError(f"Input folder not found: {INPUT_FOLDER}")
    
    if not os.listdir(INPUT_FOLDER):
        raise ValueError(f"Input folder is empty: {INPUT_FOLDER}")

def cleanup():
    """Clean up resources"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# remove global initialization at top:
# model, trocr_model, processor = initialize_models()

# declare globals
model = None
trocr_model = None
processor = None
DEVICE = None

if __name__ == "__main__":
    try:
        validate_paths()  # check paths before loading models

        # initialize models after checks so errors are clearer
        model, trocr_model, processor, DEVICE = initialize_models()

        process_all()
        print("🎯 All images processed.")
    except Exception as e:
        print(f"❌ Program failed: {str(e)}")
    finally:
        cleanup()