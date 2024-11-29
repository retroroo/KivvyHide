from stegano import lsb
import os

def hide_message(image_path: str, message: str) -> str:
    """Hide a message in an image using LSB steganography"""
    secret = lsb.hide(image_path, message)
    base_output_path = image_path.rsplit('.', 1)[0] + '_secret.png'
    
    # Generate unique filename
    output_path = base_output_path
    counter = 1
    while os.path.exists(output_path):
        name, ext = os.path.splitext(base_output_path)
        output_path = f"{name}_{counter}{ext}"
        counter += 1
    
    secret.save(output_path)
    return output_path

def reveal_message(image_path: str) -> str:
    """Reveal a message hidden in an image using LSB steganography"""
    return lsb.reveal(image_path)
