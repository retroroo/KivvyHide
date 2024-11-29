from stegano import lsb

def hide_message(image_path: str, message: str) -> None:
    """Hide a message in an image using LSB steganography"""
    secret = lsb.hide(image_path, message)
    output_path = image_path.rsplit('.', 1)[0] + '_secret.png'
    secret.save(output_path)

def reveal_message(image_path: str) -> str:
    """Reveal a message hidden in an image using LSB steganography"""
    return lsb.reveal(image_path)
