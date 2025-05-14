import os
import streamlit as st
import base64
from PIL import Image
from io import BytesIO
import json
import requests
from openai import AzureOpenAI
import time
import uuid
from utils import (display_image, get_catalog_items, save_uploaded_file, 
                  load_image_as_base64, get_catalog_items_with_thumbnails,
                  preload_catalog_images)

# Set page configuration
st.set_page_config(
    page_title="Virtual Try-On - AI Powered Fashion",
    page_icon="👔",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'clothing_page' not in st.session_state:
    st.session_state.clothing_page = 1
    
if 'accessories_page' not in st.session_state:
    st.session_state.accessories_page = 1
    
if 'selected_items' not in st.session_state:
    st.session_state.selected_items = []

# Preload catalog images in the background for faster loading
preload_catalog_images()

# Load environment variables for Azure OpenAI
def load_config():
    try:
        # Use absolute path to config.json
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        with open(config_path, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        # Use environment variables as fallback
        return {
            "imagegen_aoai_resource": os.getenv("imagegen_aoai_resource", ""),
            "imagegen_aoai_endpoint": os.getenv("imagegen_aoai_endpoint", ""),
            "imagegen_aoai_deployment": os.getenv("imagegen_aoai_deployment", ""),
            "imagegen_aoai_api_key": os.getenv("imagegen_aoai_api_key", "")
        }

# Load configuration
config = load_config()

# Initialize Azure OpenAI client
def get_aoai_client():
    return AzureOpenAI(
        azure_endpoint=config["imagegen_aoai_endpoint"],
        api_version="2025-04-01-preview",
        api_key=config["imagegen_aoai_api_key"]
    )

# Function to generate try-on images
def generate_try_on_image(user_image_path, item_images, prompt_addon=""):
    # Prepare URL for image edits
    url = f"https://{config['imagegen_aoai_resource']}.openai.azure.com/openai/deployments/{config['imagegen_aoai_deployment']}/images/edits?api-version=2025-04-01-preview"
    
    # Prepare headers with API key
    headers = {
        "api-key": config["imagegen_aoai_api_key"]
    }
    
    # Prepare the files
    files = []
    try:
        files.append(("image[]", open(user_image_path, "rb")))
        for item_path in item_images:
            files.append(("image[]", open(item_path, "rb")))
        
        # Base prompt for try-on
        base_prompt = """
        Generate a high-quality, photorealistic image of the first person wearing the clothing/accessories shown in the other reference images. 
        Maintain the exact facial features, skin tone, hairstyle, and body type of the first person. 
        Only change their outfit to match the provided catalog items while keeping their identity intact.
        The image should look natural and realistic, with appropriate lighting and background.
        """
        
        if prompt_addon:
            base_prompt += f"\n{prompt_addon}"
        
        data = {
            "prompt": base_prompt,
            "n": 1,
            "size": "1024x1536",  # Portrait orientation
            "quality": "high",
        }
        
        with st.spinner("Generating your virtual try-on image... Please wait, this may take a moment."):
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            
            # Get the image data
            result = response.json()
            b64_image = result["data"][0]["b64_json"]
            
            # Save the generated image
            image_filename = f"generated_{str(uuid.uuid4())[:8]}.png"
            # Make sure the directory exists
            os.makedirs("generated_images", exist_ok=True)
            image_path = os.path.join("generated_images", image_filename)
            
            # Decode and save the image
            image_data = base64.b64decode(b64_image)
            image = Image.open(BytesIO(image_data))
            image.save(image_path)
            
            return image_path, b64_image
            
    except Exception as e:
        st.error(f"Error in image generation: {str(e)}")
        raise
    finally:
        # Ensure all file handles are closed
        for _, file_obj in files:
            if hasattr(file_obj, 'close'):
                file_obj.close()

# Helper function to show pagination controls
def pagination_controls(category_type):
    """
    Show pagination controls for a category
    
    Parameters:
    - category_type: 'clothing' or 'accessories'
    """
    col1, col2, col3, col4, col5 = st.columns([1, 1, 3, 1, 1])
    
    page_key = f"{category_type}_page"
    current_page = getattr(st.session_state, page_key)
    
    # Get catalog data to determine total pages
    catalog_data = get_catalog_items_with_thumbnails(
        f"catalog/{category_type}", 
        current_page, 
        6  # items per page
    )
    total_pages = catalog_data["pagination"]["total_pages"]
    
    # Previous page button
    with col1:
        if current_page > 1:
            if st.button("← Prev", key=f"prev_{category_type}"):
                setattr(st.session_state, page_key, current_page - 1)
                st.rerun()
    
    # Next page button
    with col5:
        if current_page < total_pages:
            if st.button("Next →", key=f"next_{category_type}"):
                setattr(st.session_state, page_key, current_page + 1)
                st.rerun()
    
    # Page indicator
    with col3:
        st.write(f"Page {current_page} of {total_pages}")

# Helper function to toggle item selection
def toggle_item_selection(item_path):
    """
    Toggle an item's selection status
    
    Parameters:
    - item_path: Path to the item to toggle
    """
    if item_path in st.session_state.selected_items:
        st.session_state.selected_items.remove(item_path)
    else:
        st.session_state.selected_items.append(item_path)

# Main app UI
def main():
    st.title("🧥 Virtual Try-On Experience")
    st.markdown("### Try on clothing and accessories without leaving your home!")
    
    # Sidebar for user options
    st.sidebar.title("Options")
    
    # User profile section
    with st.sidebar.expander("📷 Your Profile Photo", expanded=True):
        user_image = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"])
        if user_image:
            user_image_path = save_uploaded_file(user_image, "uploads/user_images")
            st.success(f"Image uploaded successfully!")
            st.sidebar.image(user_image_path, caption="Your Profile Photo", use_column_width=True)
            st.session_state.user_image_path = user_image_path
        elif 'sample_user_image' not in st.session_state:
            # Use a default image if no user image is provided
            st.sidebar.warning("Please upload your photo or use a sample")
            if st.sidebar.button("Use Sample Photo"):
                # Look for any image in the user_images folder to use as sample
                sample_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "user_images")
                sample_images = []
                
                # Try to create the directory if it doesn't exist
                os.makedirs(sample_images_dir, exist_ok=True)
                
                if os.path.exists(sample_images_dir):
                    for filename in os.listdir(sample_images_dir):
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            sample_images.append(os.path.join(sample_images_dir, filename))
                
                if sample_images:
                    # Use the first image found as sample
                    sample_path = sample_images[0]
                    st.session_state.user_image_path = sample_path
                    st.session_state.sample_user_image = True
                    st.rerun()
                else:
                    st.sidebar.error("No sample images found. Please upload an image first.")

    # Show selected items count in sidebar
    if st.session_state.selected_items:
        st.sidebar.success(f"{len(st.session_state.selected_items)} items selected for try-on")

    # Main content area
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("## Select items to try on")
        
        # Categories tabs
        tab1, tab2, tab3 = st.tabs(["Clothing", "Accessories", "Upload Your Item"])
        
        with tab1:
            st.markdown("### Clothing Items")
            # Get paginated clothing items with thumbnails
            clothing_data = get_catalog_items_with_thumbnails(
                "catalog/clothing", 
                st.session_state.clothing_page, 
                6  # items per page
            )
            
            if not clothing_data["items"]:
                st.info("No clothing items found in the catalog. Sample items will be added soon.")
            else:
                # Display pagination controls
                pagination_controls("clothing")
                
                # Display clothing items in a grid
                cols = st.columns(3)
                for idx, item in enumerate(clothing_data["items"]):
                    with cols[idx % 3]:
                        # Use thumbnail for faster loading
                        thumbnail_path = item.get("thumbnail_path", item["path"])
                        st.image(thumbnail_path, caption=item["name"], use_column_width=True)
                        
                        # Check if item is already selected
                        is_selected = item["path"] in st.session_state.selected_items
                        button_label = "✓ Selected" if is_selected else "Select"
                        button_type = "primary" if is_selected else "secondary"
                        
                        if st.button(button_label, key=f"clothing_btn_{idx}", type=button_type):
                            toggle_item_selection(item["path"])
                            st.rerun()
        
        with tab2:
            st.markdown("### Accessories")
            # Get paginated accessories items with thumbnails
            accessories_data = get_catalog_items_with_thumbnails(
                "catalog/accessories", 
                st.session_state.accessories_page, 
                6  # items per page
            )
            
            if not accessories_data["items"]:
                st.info("No accessory items found in the catalog. Sample items will be added soon.")
            else:
                # Display pagination controls
                pagination_controls("accessories")
                
                # Display accessories items in a grid
                cols = st.columns(3)
                for idx, item in enumerate(accessories_data["items"]):
                    with cols[idx % 3]:
                        # Use thumbnail for faster loading
                        thumbnail_path = item.get("thumbnail_path", item["path"])
                        st.image(thumbnail_path, caption=item["name"], use_column_width=True)
                        
                        # Check if item is already selected
                        is_selected = item["path"] in st.session_state.selected_items
                        button_label = "✓ Selected" if is_selected else "Select"
                        button_type = "primary" if is_selected else "secondary"
                        
                        if st.button(button_label, key=f"accessory_btn_{idx}", type=button_type):
                            toggle_item_selection(item["path"])
                            st.rerun()
        
        with tab3:
            st.markdown("### Upload Your Own Item")
            custom_item = st.file_uploader("Upload clothing or accessories", type=["jpg", "jpeg", "png"])
            
            if custom_item:
                custom_item_path = save_uploaded_file(custom_item, "uploads/user_items")
                st.success("Item uploaded successfully!")
                st.image(custom_item_path, caption="Your custom item", width=200)
                
                # Check if item is already selected
                is_selected = custom_item_path in st.session_state.selected_items
                button_label = "✓ Selected" if is_selected else "Select Item"
                button_type = "primary" if is_selected else "secondary"
                
                if st.button(button_label, type=button_type):
                    toggle_item_selection(custom_item_path)
                    st.rerun()
        
        # Additional prompt customization
        st.markdown("### Additional Instructions (Optional)")
        prompt_addon = st.text_area(
            "Add specific instructions for the AI (e.g., 'Make it a professional look', 'Add a casual background')",
            height=100
        )
        
        # Generate button - use selected items from session state
        if st.button(
            "Generate Try-On Image", 
            type="primary", 
            disabled=not st.session_state.selected_items or 'user_image_path' not in st.session_state
        ):
            if 'user_image_path' in st.session_state and st.session_state.selected_items:
                try:
                    # Generate the try-on image
                    result_path, b64_image = generate_try_on_image(
                        st.session_state.user_image_path, 
                        st.session_state.selected_items,
                        prompt_addon
                    )
                    
                    # Store the result in session state
                    st.session_state.result_path = result_path
                    st.session_state.result_b64 = b64_image
                    
                    # Display a success message
                    st.success("Try-on image generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating try-on image: {str(e)}")
            else:
                st.warning("Please upload your photo and select at least one item to try on.")
    
    # Result display column
    with col2:
        st.markdown("## Your Virtual Try-On Result")
        
        # Show selected items
        if st.session_state.selected_items:
            st.markdown("### Selected Items:")
            selected_cols = st.columns(3)
            for idx, item_path in enumerate(st.session_state.selected_items):
                with selected_cols[idx % 3]:
                    st.image(item_path, use_column_width=True)
                    
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state.selected_items.remove(item_path)
                        st.rerun()
        
        if 'result_path' in st.session_state:
            st.image(st.session_state.result_path, caption="Your Virtual Try-On", use_column_width=True)
            
            # Download button for the generated image
            with open(st.session_state.result_path, "rb") as file:
                btn = st.download_button(
                    label="Download Image",
                    data=file,
                    file_name=os.path.basename(st.session_state.result_path),
                    mime="image/png"
                )
                
            # Share option
            st.markdown("### Share Your Look")
            st.markdown("Copy the link below to share your virtual try-on:")
            share_url = f"https://yourdomain.com/share?image={os.path.basename(st.session_state.result_path)}"
            st.code(share_url)
        else:
            st.info("Your virtual try-on image will appear here after generation.")
            # Placeholder image
            st.image("https://via.placeholder.com/400x600?text=Try-On+Preview", caption="Preview Placeholder")

# Run the app
if __name__ == "__main__":
    main()