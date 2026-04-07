import os
import cv2
import json
import numpy as np
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
from ultralytics import YOLO
from post_processing import post_process

# Paths
INPUT_FOLDER = "dataset/cheques"
CROPS_FOLDER = "detected_fields"
OCR_FOLDER = "ocr_results"
JSON_FOLDER = "final_output_json"
MODEL_PATH = "runs/detect/train3/weights/best.pt"

FIELD_CLASSES = ['Cheque_Number', 'Account_Number', 'IFSC_Code',  'Amount', 'Date', 'Payee_Name']

import re


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

def enhance_micr(image):
    """
    Specialised preprocessing for MICR-encoded fields (cheque number).
    MICR digits are printed in a high-contrast magnetic ink font -- aggressive
    binarisation and upscaling help TrOCR read them more completely.
    """
    # 4x upscale for more pixels per digit
    image = cv2.resize(image, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Sharpen before thresholding
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)

    # Otsu binarisation -- best for MICR high-contrast ink
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Small dilation to reconnect broken strokes in MICR font
    kernel_d = np.ones((2, 2), np.uint8)
    binary = cv2.dilate(binary, kernel_d, iterations=1)

    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

def extract_text_trocr(image, trocr_model, processor, device):
    """Extract text using TrOCR. `device` must be same device used to load the model."""
    # Convert CV2 image to PIL
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)

    # Prepare image for model
    inputs = processor(pil_image, return_tensors="pt")
    pixel_values = inputs.pixel_values.to(device)

    # Generate text in no_grad for memory/speed
    with torch.no_grad():
        generated_ids = trocr_model.generate(
            pixel_values,
            max_length=64,
            num_beams=2
        )
        # generated_ids = trocr_model.generate(pixel_values, max_length=256, num_beams=4)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return generated_text.strip()

def run_pipeline(image_path, model, trocr_model, processor, DEVICE):
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
        detections = sorted(detections, key=lambda x: x.xyxy[0][0])
        # detections = sorted(detections, key=lambda x: x.xyxy[0][1])
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


            # clamp to image bounds + padding
            padding = 3
            h, w = image.shape[:2]

            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)

            # # clamp to image bounds
            # h, w = image.shape[:2]
            # x1, y1 = max(0, x1), max(0, y1)
            # x2, y2 = min(w, x2), min(h, y2)
            if x2 <= x1 or y2 <= y1:
                continue

            cropped = image[y1:y2, x1:x2]
            if cropped is None or cropped.size == 0:
                continue

            if class_name == 'Cheque_Number':
                enhanced_crop = enhance_micr(cropped)
            else:
                enhanced_crop = enhance_image(cropped)

            # Save cropped and enhanced image
            crop_path = os.path.join(CROPS_FOLDER, f"{image_name}_{class_name}.jpg")
            cv2.imwrite(crop_path, enhanced_crop)

            # Extract text using TrOCR (ensure device variable is available)
            text = extract_text_trocr(enhanced_crop, trocr_model, processor, DEVICE)

            # Apply post-processing
            text = post_process(class_name, text)

            print(f"✅ {class_name}: {text}")

            # Save to text file
            ocr_txt_path = os.path.join(OCR_FOLDER, f"{image_name}_{class_name}.txt")
            safe_write_file(ocr_txt_path, text)

            output_json[class_name.lower()] = {
                "text": text,
                "y": y1
            }

        # Save to final JSON
        json_path = os.path.join(JSON_FOLDER, f"{image_name}.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        # remove position info before saving
        clean_json = {k:v["text"] for k,v in output_json.items()}

        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(clean_json, jf, indent=4)

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

def process_all(model, trocr_model, processor, device):
    """Process all images in INPUT_FOLDER using the provided models"""
    total_images = len([f for f in os.listdir(INPUT_FOLDER) 
                       if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif"))])
    processed = 0
    failed = 0
    
    try:
        validate_paths()
        for img_file in os.listdir(INPUT_FOLDER):
            if img_file.lower().endswith((".jpg", ".jpeg", ".png", ".tif")):
                # Pass all required arguments to run_pipeline
                success = run_pipeline(
                    os.path.join(INPUT_FOLDER, img_file),
                    model, trocr_model, processor, device
                )
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
    # Check MODEL_PATH
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    # Create input/output directories if they don't exist
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(CROPS_FOLDER, exist_ok=True)
    os.makedirs(OCR_FOLDER, exist_ok=True)
    os.makedirs(JSON_FOLDER, exist_ok=True)
    
    # Check if input folder has any valid images
    valid_extensions = ('.jpg', '.jpeg', '.png', '.tif')
    if not any(f.lower().endswith(valid_extensions) for f in os.listdir(INPUT_FOLDER)):
        raise ValueError(f"No valid images found in input folder: {INPUT_FOLDER}")

def cleanup():
    """Clean up resources"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    # Add any other cleanup steps here

# Update the main block to pass models to process_all
if __name__ == "__main__":
    try:
        validate_paths()  # check paths before loading models

        # initialize models after checks so errors are clearer
        model, trocr_model, processor, DEVICE = initialize_models()

        # Pass all required arguments to process_all
        process_all(model, trocr_model, processor, DEVICE)
        print("🎯 All images processed.")
    except Exception as e:
        print(f"❌ Program failed: {str(e)}")
    finally:
        cleanup()