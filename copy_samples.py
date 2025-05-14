import os
import shutil
from PIL import Image

def copy_image_files():
    """Copy sample images from the image-generation project to the virtual try-on catalog"""
    # Source and destination paths
    source_dir = os.path.join('..', 'image-generation-using-aoai', 'images')
    clothing_dir = os.path.join('catalog', 'clothing')
    accessories_dir = os.path.join('catalog', 'accessories')
    user_images_dir = os.path.join('uploads', 'user_images')
    
    # Ensure directories exist
    for directory in [clothing_dir, accessories_dir, user_images_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Sample mapping - adjust based on what images you have
    clothing_images = ['woman-shirt.png', 'woman-jeans.png']
    accessory_images = ['woman-shoes.png']
    user_images = ['priya_1.png']
    
    # Copy clothing items
    print("Copying clothing items...")
    for image in clothing_images:
        source_path = os.path.join(source_dir, image)
        dest_path = os.path.join(clothing_dir, image)
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"Copied {image} to {clothing_dir}")
        else:
            print(f"Warning: {source_path} not found")
    
    # Copy accessory items
    print("\nCopying accessory items...")
    for image in accessory_images:
        source_path = os.path.join(source_dir, image)
        dest_path = os.path.join(accessories_dir, image)
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"Copied {image} to {accessories_dir}")
        else:
            print(f"Warning: {source_path} not found")
    
    # Copy user images
    print("\nCopying user images...")
    for image in user_images:
        source_path = os.path.join(source_dir, image)
        dest_path = os.path.join(user_images_dir, image)
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"Copied {image} to {user_images_dir}")
        else:
            print(f"Warning: {source_path} not found")
    
    print("\nSample image copying complete!")

if __name__ == "__main__":
    copy_image_files()