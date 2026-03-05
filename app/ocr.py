import cv2
import numpy as np
import math
import os
import json
import google.generativeai as genai
from app.models import InvoiceData, LineItem

def preprocess_image(image_bytes: bytes):
    """
    Handles blurry or slightly tilted images using OCR preprocessing techniques.
    """
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    gray = cv2.medianBlur(gray, 3)
    
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
    
    if lines is not None:
        for rho, theta in lines[0]:
            angle = math.degrees(theta)
            if angle > 45 and angle < 135:
                angle = angle - 90
            
            if angle != 0:
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                
    return gray

def process_document(file_bytes: bytes, filename: str) -> InvoiceData:
    """
    Uses Google's Gemini Vision AI to extract JSON details from an invoice image.
    """
    API_KEY = os.environ.get("GEMINI_API_KEY", "") 
    
    if not API_KEY:
        try:
            text = ""
            if filename.lower().endswith('.pdf'):
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    text += page.get_text() + "\n"
            else:
                import requests
                res = requests.post('https://api.ocr.space/parse/image', 
                                  data={'apikey':'helloworld'}, 
                                  files={'file': (filename, file_bytes)})
                data = res.json()
                text = data['ParsedResults'][0]['ParsedText'] if data.get('ParsedResults') else ""
            
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if not lines:
                raise ValueError("No text extracted.")
                
            vendor = lines[0]
            date = lines[1].replace('Invoice Date:', '').strip()

            items = []
            idx = 2
            while idx < len(lines) and 'Line Total' not in lines[idx]:
                idx += 1
            idx += 1 
            
            while idx < len(lines) and not (lines[idx].startswith('Subtotal') or lines[idx].startswith('Total')):
                try:
                    desc = lines[idx]
                    qty = int(lines[idx+1])
                    price = float(lines[idx+2].replace('$',''))
                    items.append(LineItem(description=desc, quantity=qty, unit_price=price))
                    idx += 4
                except:
                    break
                    
            ext_total_str = "0"
            for l in lines[::-1]:
                if l.startswith('Total:'):
                    ext_total_str = l
                    break
            
            extracted_total = float(ext_total_str.replace('Total:', '').replace('$', '').strip())
            
            return InvoiceData(vendor=vendor, date=date, items=items, extracted_total=extracted_total)
        except Exception as e:
            print(f"Fallback Parse Error: {e}")
            return InvoiceData(
                vendor="Fallback Data Error",
                date="2026-03-05",
                items=[],
                extracted_total=0.0
            )
        
    genai.configure(api_key=API_KEY)
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = """
    Extract the invoice details from this image and output ONLY raw JSON.
    Use this exact schema (no markdown formatting, just the raw braces):
    {
      "vendor": "String",
      "date": "YYYY-MM-DD",
      "items": [
        {
          "description": "String",
          "quantity": Integer,
          "unit_price": Float
        }
      ],
      "extracted_total": Float
    }
    """
    
    mime_type = "image/jpeg"
    if filename.lower().endswith('.png'):
        mime_type = "image/png"
    elif filename.lower().endswith('.pdf'):
        mime_type = "application/pdf"
        
    image_part = {
        "mime_type": mime_type,
        "data": file_bytes
    }
    
    response = model.generate_content([prompt, image_part])
    
    text_content = response.text.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(text_content)
        return InvoiceData(**data)
    except Exception as e:
        raise ValueError(f"AI Failed to parse the invoice properly: {str(e)}\nRaw Output: {text_content}")
