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
    
    base_output_path = image_path.rsplit('.', 1)[0] + '_secret.png'
    output_path = base_output_path
    counter = 1
    while os.path.exists(output_path):
        name, ext = os.path.splitext(base_output_path)
        output_path = f"{name}_{counter}{ext}"
        counter += 1
    
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
