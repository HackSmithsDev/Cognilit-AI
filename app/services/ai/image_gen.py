import os
import re
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageProvider:
    def generate(self, session_id, pro_prompt, user_text, upload_folder):
        """
        Generates/fetches an image with multi-layer fallback.
        1. Pollinations AI (Custom Gen)
        2. LoremFlickr (Keyword-based)
        3. Unsplash (Static High-Quality)
        """
        # --- 1. Setup Local Storage ---
        filename = f"gen_{session_id}_{datetime.now().strftime('%H%M%S')}.png"
        relative_path = os.path.join('images', filename)
        full_path = os.path.join(upload_folder, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # --- 2. Prepare Data for Providers ---
        # Clean the user_text to get 3 simple keywords for fallback tags
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', user_text)
        keywords = ",".join(clean_text.split()[:3]) or "research"
        
        # Encode the AI prompt (limited to 300 chars for URL stability)
        encoded_ai_prompt = requests.utils.quote(pro_prompt[:300])

        # The "Waterfall" list
        providers = [
            {
                "name": "Pollinations AI",
                "url": f"https://image.pollinations.ai/prompt/{encoded_ai_prompt}?width=1024&height=1024&nologo=true",
                "timeout": 45  # AI generation needs more time
            },
            {
                "name": "LoremFlickr (Dynamic)",
                "url": f"https://loremflickr.com/1024/1024/{keywords},research,abstract/all",
                "timeout": 15
            },
            {
                "name": "Unsplash (Topic-Based)",
                "url": f"https://source.unsplash.com/featured/1024x1024?{keywords}",
                "timeout": 10
            }
        ]

        # --- 3. Execution Loop ---
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

        for provider in providers:
            try:
                logger.info(f"DEBUG: Attempting {provider['name']}...")
                response = requests.get(
                    provider['url'], 
                    headers=headers, 
                    timeout=provider['timeout'],
                    stream=True # Better for large images
                )

                if response.status_code == 200:
                    # Double check we didn't get an error page wrapped in a 200
                    if "text/html" in response.headers.get("Content-Type", ""):
                        logger.warning(f"DEBUG: {provider['name']} returned HTML instead of image. Skipping...")
                        continue

                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    logger.info(f"SUCCESS: Image saved via {provider['name']}")
                    return f"/static/uploads/{relative_path}"
                
                logger.error(f"DEBUG: {provider['name']} failed with status {response.status_code}")

            except Exception as e:
                logger.error(f"DEBUG: Error with {provider['name']}: {str(e)}")
                continue # Move to next provider

        return None