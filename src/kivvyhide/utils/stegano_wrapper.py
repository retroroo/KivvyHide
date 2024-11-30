from stegano import lsb
import os
import zlib
import base64
from cryptography.fernet import Fernet
from .settings import SteganoSettings

def hide_message(image_path: str, message: str, settings: SteganoSettings = None) -> str:
    if settings is None:
        settings = SteganoSettings()
    
    # Process message based on settings
    data = message.encode(settings.encoding)
    
    if settings.compression:
        data = zlib.compress(data)
    
    if settings.encryption_key:
        f = Fernet(settings.encryption_key)
        data = f.encrypt(data)
    
    # Convert to string for LSB
    processed_message = base64.b64encode(data).decode()
    
    # Hide message using LSB
    secret = lsb.hide(image_path, processed_message)
    
    # Handle custom filename and path
    if settings.custom_filename:
        # Ensure filename ends with .png
        if not settings.custom_filename.lower().endswith('.png'):
            base_filename = settings.custom_filename + '.png'
        else:
            base_filename = settings.custom_filename
    else:
        base_filename = os.path.splitext(os.path.basename(image_path))[0] + '_secret.png'
    
    # Determine output directory
    if settings.custom_path:
        output_dir = settings.custom_path
    else:
        output_dir = os.path.dirname(image_path)
    
    # Combine path and filename
    output_path = os.path.join(output_dir, base_filename)
    
    # Handle file exists case
    counter = 1
    while os.path.exists(output_path):
        name, ext = os.path.splitext(base_filename)
        new_filename = f"{name}_{counter}{ext}"
        output_path = os.path.join(output_dir, new_filename)
        counter += 1
    
    # Save the image
    secret.save(output_path)
    return output_path

def reveal_message(image_path: str, settings: SteganoSettings = None) -> str:
    if settings is None:
        settings = SteganoSettings()
    
    # Reveal message
    revealed = lsb.reveal(image_path)
    data = base64.b64decode(revealed)
    
    if settings.encryption_key:
        f = Fernet(settings.encryption_key)
        data = f.decrypt(data)
    
    if settings.compression:
        data = zlib.decompress(data)
    
    return data.decode(settings.encoding)
