# Virtual Try-On E-commerce Application

A Streamlit web application that allows users to virtually try on clothing and accessories from an e-commerce catalog using Azure OpenAI image generation capabilities.

## Features

- Upload your own photo to see how you'd look in different outfits
- Browse a catalog of clothing and accessories
- Upload your own items to try on
- Generate high-quality virtual try-on images
- Download and share your virtual try-on results

## Prerequisites

- Python 3.8 or higher
- An Azure subscription
- Azure OpenAI service with DALL-E 3 capabilities

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your Azure OpenAI settings in `config.json`:
   ```json
   {
       "imagegen_aoai_resource": "your-azure-openai-resource",
       "imagegen_aoai_endpoint": "https://your-azure-openai-resource.openai.azure.com",
       "imagegen_aoai_deployment": "your-image-generation-deployment-name",
       "imagegen_aoai_api_key": "your-azure-openai-api-key"
   }
   ```

## Running the Application

To run the application locally:

```
streamlit run app.py
```

## Directory Structure

- `app.py`: Main Streamlit application
- `utils.py`: Helper functions for image handling
- `config.json`: Configuration for Azure OpenAI
- `catalog/`: Contains sample catalog items
  - `clothing/`: Clothing items
  - `accessories/`: Accessories items
- `uploads/`: For user-uploaded content
  - `user_images/`: User profile photos
  - `user_items/`: User-uploaded clothing and accessories
- `generated_images/`: Storage for AI-generated try-on images

## Adding Catalog Items

To add new catalog items:
1. Place clothing images in the `catalog/clothing/` directory
2. Place accessories images in the `catalog/accessories/` directory
3. Use transparent PNG images for best results
4. Name files descriptively (e.g., `blue_dress.png`, `gold_necklace.png`)

## How It Works

1. User uploads their photo or uses a sample image
2. User selects clothing and accessories from the catalog
3. The app sends the images to Azure OpenAI's image generation service
4. A new image is generated showing the user wearing the selected items
5. User can download or share the resulting image

## Security Notes

- User images are stored locally and not shared
- API keys should be kept secure and not committed to version control
- For production use, implement proper authentication and secure storage