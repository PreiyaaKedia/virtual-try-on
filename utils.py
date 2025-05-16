import os
import base64
from io import BytesIO
from PIL import Image
import streamlit_custom as st
import uuid
import time
from functools import lru_cache

# Add display_image (singular) function to match the import in app.py
def display_image(image_data, width=None):
    """
    Display a single image in Streamlit from various formats
    
    Parameters:
    - image_data: Can be a base64 string, file path, or PIL Image object
    - width: Width to display the image (optional)
    """
    # Delegate to the plural version for consistent implementation
    display_images(image_data, width)

def display_images(image_data, width=None):
    """
    Display an image or multiple images in Streamlit from various formats
    
    Parameters:
    - image_data: Can be a base64 string, file path, PIL Image object or a list of these
    - width: Width to display the image (optional)
    """
    # Convert single image to list for uniform handling
    if not isinstance(image_data, list):
        images = [image_data]
    else:
        images = image_data
        
    # Process each image for display
    for img in images:
        if isinstance(img, str):
            if os.path.exists(img):
                # It's a file path
                img_obj = Image.open(img)
                if width:
                    # Calculate height based on aspect ratio
                    w, h = img_obj.size
                    new_h = int(width * h / w)
                    img_obj = img_obj.resize((width, new_h))
                st.image(img_obj)
            elif img.startswith('http'):
                # It's a URL
                st.image(img, width=width)
            else:
                # Try as base64
                try:
                    img_data = base64.b64decode(img)
                    img_obj = Image.open(BytesIO(img_data))
                    if width:
                        # Calculate height based on aspect ratio
                        w, h = img_obj.size
                        new_h = int(width * h / w)
                        img_obj = img_obj.resize((width, new_h))
                    st.image(img_obj)
                except Exception as e:
                    st.error(f"Could not display image: {str(e)}")
        elif isinstance(img, Image.Image):
            if width:
                # Calculate height based on aspect ratio
                w, h = img.size
                new_h = int(width * h / w)
                img = img.resize((width, new_h))
            st.image(img)
        else:
            st.error(f"Unsupported image format: {type(img)}")

@lru_cache(maxsize=100)
def get_catalog_items_cached(catalog_path):
    """
    Cached version of get_catalog_items to improve performance
    
    Parameters:
    - catalog_path: Path to the catalog directory
    
    Returns:
    - List of dictionaries with item information
    """
    return get_catalog_items(catalog_path)

def get_catalog_items(catalog_path):
    """
    Get a list of catalog items from a directory
    
    Parameters:
    - catalog_path: Path to the catalog directory
    
    Returns:
    - List of dictionaries with item information
    """
    items = []
    try:
        if not os.path.exists(catalog_path):
            os.makedirs(catalog_path, exist_ok=True)
            return items
            
        for filename in os.listdir(catalog_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(catalog_path, filename)
                name = os.path.splitext(filename)[0].replace('_', ' ').title()
                items.append({
                    "name": name,
                    "path": file_path,
                    "type": "clothing" if "clothing" in catalog_path else "accessory"
                })
    except Exception as e:
        st.error(f"Error loading catalog items: {str(e)}")
    
    return items

def create_thumbnail(image_path, max_size=(300, 300), thumbnail_dir=None):
    """
    Create a thumbnail of an image for faster loading
    
    Parameters:
    - image_path: Path to the original image
    - max_size: Maximum size of the thumbnail (width, height)
    - thumbnail_dir: Directory to save the thumbnail (default: create next to original)
    
    Returns:
    - Path to the thumbnail
    """
    try:
        if not os.path.exists(image_path):
            return None
            
        # Get the directory of the original image if thumbnail_dir not specified
        if thumbnail_dir is None:
            thumbnail_dir = os.path.join(os.path.dirname(image_path), "thumbnails")
            
        # Create the thumbnail directory if it doesn't exist
        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir, exist_ok=True)
            
        # Generate thumbnail filename
        filename = os.path.basename(image_path)
        thumbnail_path = os.path.join(thumbnail_dir, f"thumb_{filename}")
        
        # If thumbnail already exists, return its path
        if os.path.exists(thumbnail_path):
            return thumbnail_path
            
        # Create the thumbnail
        with Image.open(image_path) as img:
            img.thumbnail(max_size)
            img.save(thumbnail_path, optimize=True, quality=85)
            
        return thumbnail_path
    except Exception as e:
        st.error(f"Error creating thumbnail: {str(e)}")
        return image_path  # Fall back to original image on error

def get_catalog_items_with_thumbnails(catalog_path, page=1, items_per_page=6):
    """
    Get a paginated list of catalog items from a directory with thumbnails
    
    Parameters:
    - catalog_path: Path to the catalog directory
    - page: Current page number (1-indexed)
    - items_per_page: Number of items per page
    
    Returns:
    - Dictionary with items and pagination info
    """
    all_items = get_catalog_items_cached(catalog_path)
    total_items = len(all_items)
    
    # Calculate pagination
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    current_page = min(max(1, page), total_pages)
    
    # Get items for the current page
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    page_items = all_items[start_idx:end_idx]
    
    # Create thumbnails for the items
    for item in page_items:
        thumbnail_path = create_thumbnail(item["path"])
        item["thumbnail_path"] = thumbnail_path if thumbnail_path else item["path"]
    
    return {
        "items": page_items,
        "pagination": {
            "current_page": current_page,
            "total_pages": total_pages,
            "total_items": total_items
        }
    }

def save_uploaded_file(uploaded_file, save_dir):
    """
    Save an uploaded file to the specified directory
    
    Parameters:
    - uploaded_file: File object from st.file_uploader
    - save_dir: Directory to save the file
    
    Returns:
    - Path to the saved file
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    
    # Generate a unique filename
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    filename = f"{str(uuid.uuid4())[:8]}{file_ext}"
    file_path = os.path.join(save_dir, filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def load_image_as_base64(image_path):
    """
    Load an image file and convert it to base64
    
    Parameters:
    - image_path: Path to the image file
    
    Returns:
    - Base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Add a function to preload images in background
def preload_catalog_images():
    """
    Preload catalog images in the background to improve performance
    """
    # Start preloading clothing catalog
    get_catalog_items_cached("catalog/clothing")
    
    # Start preloading accessories catalog
    get_catalog_items_cached("catalog/accessories")
    
    # Create thumbnails for all catalog items
    preload_thumbnails("catalog/clothing")
    preload_thumbnails("catalog/accessories")
    
def preload_thumbnails(catalog_path):
    """
    Create thumbnails for all images in a catalog path
    
    Parameters:
    - catalog_path: Path to the catalog directory
    """
    try:
        items = get_catalog_items(catalog_path)
        for item in items:
            create_thumbnail(item["path"])
    except Exception as e:
        st.error(f"Error preloading thumbnails: {str(e)}")