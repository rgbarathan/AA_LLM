import requests

# Google Gemini API endpoint
API_KEY = "AIzaSyCTCIjTodpzZ7KxFQgNtr_8qIwU7ppw3bs"  # Replace with your Google API key
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"


def get_architecture_advice(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    
    # Combine system message and user prompt for Gemini
    full_prompt = "You are an expert telecom architect.\n\n" + prompt
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        # Handle different response structures
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate:
                if "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0]["text"]
                elif "text" in candidate["content"]:
                    return candidate["content"]["text"]
        return f"Unexpected response structure: {result}"
    else:
        return f"Error: {response.status_code}, {response.text}"


# Example usage
prompt = "Compare microservices and monolithic architecture for telecom billing."
print(get_architecture_advice(prompt))
