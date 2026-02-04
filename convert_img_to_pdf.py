from PIL import Image
import os

# Source image path
image_path = r"C:/Users/khaoula/.gemini/antigravity/brain/45947a3a-e490-490f-8bc6-24aec9506acb/uploaded_media_1769626439654.png"
# Output PDF path (saving in current directory)
output_path = "NetGuardian_Dashboard.pdf"

try:
    if os.path.exists(image_path):
        # Open the image
        image = Image.open(image_path)
        
        # Convert to RGB (standard for PDF, handles removing alpha channel if present)
        # PNGs often have transparency (RGBA) which can sometimes cause issues in simple PDF saves, 
        # treating it as a visible layer is usually desired.
        if image.mode == 'RGBA':
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3]) # 3 is the alpha channel
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Save as PDF
        image.save(output_path, "PDF", resolution=100.0, save_all=True)
        print(f"SUCCESS: Image converted to {os.path.abspath(output_path)}")
    else:
        print(f"ERROR: Image file not found at {image_path}")
except Exception as e:
    print(f"ERROR: Failed to convert image. Reason: {e}")
