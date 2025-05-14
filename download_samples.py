import os
import requests
from PIL import Image
from io import BytesIO

# Sample items with URLs for clothing and accessories
SAMPLE_ITEMS = {
    "clothing": [
        {
            "name": "blue_tshirt",
            "url": "https://i.imgur.com/7UEi8WL.png"
        },
        {
            "name": "red_dress",
            "url": "https://i.imgur.com/JA5H93L.png"
        },
        {
            "name": "black_jacket",
            "url": "https://i.imgur.com/hD1cF92.png"
        },
        {
            "name": "floral_blouse",
            "url": "https://i.imgur.com/L7J8SsH.png"
        },
        {
            "name": "striped_sweater",
            "url": "https://i.imgur.com/2YVc7FZ.png"
        }
    ],
    "accessories": [
        {
            "name": "gold_necklace",
            "url": "https://i.imgur.com/Rj8GQXk.png"
        },
        {
            "name": "leather_bag",
            "url": "https://i.imgur.com/K5SIReY.png"
        },
        {
            "name": "sunglasses",
            "url": "https://i.imgur.com/xpe82X7.png"
        },
        {
            "name": "silver_bracelet",
            "url": "https://i.imgur.com/VQBSgrj.png"
        },
        {
            "name": "wristwatch",
            "url": "https://i.imgur.com/g98wNzM.png"
        }
    ]
}

# Sample person image
SAMPLE_PERSON = {
    "name": "sample_person",
    "url": "https://i.imgur.com/ZqMN3bB.jpg"
}

def download_image(url, save_path):
    """Download an image from URL and save it to the specified path"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path)
        print(f"Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def download_all_samples():
    """Download all sample images"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure directories exist
    os.makedirs(os.path.join(base_dir, "catalog", "clothing"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "catalog", "accessories"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "uploads", "user_images"), exist_ok=True)
    
    # Download sample person
    person_path = os.path.join(base_dir, "uploads", "user_images", f"{SAMPLE_PERSON['name']}.jpg")
    download_image(SAMPLE_PERSON["url"], person_path)
    
    # Download clothing items
    for item in SAMPLE_ITEMS["clothing"]:
        path = os.path.join(base_dir, "catalog", "clothing", f"{item['name']}.png")
        download_image(item["url"], path)
    
    # Download accessories
    for item in SAMPLE_ITEMS["accessories"]:
        path = os.path.join(base_dir, "catalog", "accessories", f"{item['name']}.png")
        download_image(item["url"], path)
    
    print("Sample download completed!")

if __name__ == "__main__":
    download_all_samples()