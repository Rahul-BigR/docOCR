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
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    model = YOLO(MODEL_PATH)
    trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-large-handwritten').to(device)
    processor = TrOCRProcessor.from_pretrained('microsoft/trocr-large-handwritten')
    
    return model, trocr_model, processor

# Initialize YOLO model
model, trocr_model, processor = initialize_models()

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

def extract_text_trocr(image):
    """Extract text using TrOCR"""
    # Convert CV2 image to PIL
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    
    # Prepare image for model
    pixel_values = processor(pil_image, return_tensors="pt").pixel_values
    
    # Generate text
    generated_ids = trocr_model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return generated_text.strip()

def run_pipeline(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        results = model(image_path)
        detections = results[0].boxes
        output_json = {}

        for i, box in enumerate(detections):
            if not hasattr(box, 'cls') or box.cls is None:
                continue

            cls_id = int(box.cls[0].item())
            if cls_id >= len(FIELD_CLASSES):
                continue
            class_name = FIELD_CLASSES[cls_id]

            if not hasattr(box, 'xyxy') or box.xyxy is None or len(box.xyxy) == 0:
                continue

            xyxy_tensor = box.xyxy[0]
            if xyxy_tensor is None or len(xyxy_tensor) != 4:
                continue

            xyxy = xyxy_tensor.tolist()
            x1, y1, x2, y2 = map(int, xyxy)
            cropped = image[y1:y2, x1:x2]
            enhanced_crop = enhance_image(cropped)

            # Save cropped and enhanced image
            crop_path = os.path.join(CROPS_FOLDER, f"{image_name}_{class_name}.jpg")
            cv2.imwrite(crop_path, enhanced_crop)

            # Extract text using TrOCR
            text = extract_text_trocr(enhanced_crop)
            print(f"✅ {class_name}: {text}")

            # Save to text file
            ocr_txt_path = os.path.join(OCR_FOLDER, f"{image_name}_{class_name}.txt")
            safe_write_file(ocr_txt_path, text)

            output_json[class_name.lower()] = text

        # Save to final JSON
        json_path = os.path.join(JSON_FOLDER, f"{image_name}.json")
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(output_json, jf, indent=4)

        print(f"✅ Processed: {image_path}")
    except Exception as e:
        print(f"❌ Error processing {image_path}: {str(e)}")
        return False

def safe_write_file(file_path, content, mode='w'):
    """Safely write content to file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
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

if __name__ == "__main__":
    try:
        process_all()
        print("🎯 All images processed.")
    except Exception as e:
        print(f"❌ Program failed: {str(e)}")
    finally:
        cleanup()