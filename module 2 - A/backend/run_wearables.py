import sys
import asyncio
import os
import json

# Ensure app is in path
sys.path.insert(0, '.')
from app.services.ocr_service import ocr_service

async def main():
    directory = r"C:\Users\Dell\Downloads\vort\wearables"
    files = os.listdir(directory)
    
    results = {}
    for f in files:
        if f.endswith(('.jpeg', '.jpg', '.png')):
            path = os.path.join(directory, f)
            print(f"\n--- Processing {f} ---")
            
            # Extract text
            text, conf = await ocr_service.process_image(path)
            
            # Parse smartwatch fields
            parsed = await ocr_service.parse_smartwatch_metrics(text)
            
            print(f"Confidence Score: {conf:.2f}")
            print(f"Extracted Text Snippet: {text[:100]}...")
            print(f"Parsed Health Metrics: {json.dumps(parsed, indent=2)}")
            
            results[f] = parsed

    print("\n--- Summary of Extracted Data ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
