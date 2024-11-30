from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivvyhide.utils.stegano_wrapper import hide_message, reveal_message
from plyer import filechooser
import base64
import os
import threading
from kivy.utils import platform
from kivy.uix.slider import Slider
from kivvyhide.utils.settings import SteganoSettings
from cryptography.fernet import Fernet
import zlib
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
import py7zr
import tempfile
from kivy.uix.popup import Popup
from PIL import Image as PILImage
from PIL.ExifTags import TAGS
import imghdr
from kivy.uix.image import Image as KivyImage
from kivy.metrics import dp
from PIL import Image
import os
from stegano import lsb
import base64
import zlib
import magic
import exifread
from typing import Dict, Any
from kivvyhide.utils.image_analyzer import ImageAnalyzer
from kivy.graphics import Color, Line
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel

# Platform-specific imports
ANDROID_PERMISSIONS = []
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        # Define permissions only if we successfully imported android modules
        ANDROID_PERMISSIONS = [
            'android.permission.READ_EXTERNAL_STORAGE',
            'android.permission.WRITE_EXTERNAL_STORAGE'
        ]
    except ImportError:
        # Android modules not available, skip permissions
        pass

class HighlightButton(Button):
    def on_press(self):
        self.background_color = [0.8, 0.8, 0.8, 1]
    
    def on_release(self):
        self.background_color = [1, 1, 1, 1]

class SteganoApp(MDApp):
    progress = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "StegKivy"
        self.carrier_file = None
        self.payload_file = None
        
        # Initialize settings attributes
        self.settings_panel = None
        self.settings_popup = None
        self.encoding_spinner = Spinner(
            text='utf-8',
            values=('utf-8', 'ascii', 'latin1'),
            size_hint_x=0.7
        )
        self.compression_spinner = Spinner(
            text='None',
            values=('None', 'Fast', 'Default', 'Best'),
            size_hint_x=0.7
        )
        self.encryption_input = TextInput(
            multiline=False,
            size_hint_x=0.7
        )
        self.seven_zip_spinner = Spinner(
            text='Disabled',
            values=('Disabled', 'AES256'),
            size_hint_x=0.7
        )
        self.seven_zip_password_input = TextInput(
            multiline=False,
            password=True,
            size_hint_x=0.7
        )
        self.custom_filename_input = TextInput(
            multiline=False,
            size_hint_x=0.7,
            hint_text='Leave empty for default'
        )
        self.custom_path_input = TextInput(
            multiline=False,
            size_hint_x=0.7
        )
        self.seven_zip_filename_input = TextInput(
            multiline=False,
            size_hint_x=0.7,
            hint_text='Leave empty for encrypted.7z'
        )
        
        if platform == 'android' and ANDROID_PERMISSIONS:
            self.request_android_permissions()
        
    def request_android_permissions(self):
        if platform == 'android' and ANDROID_PERMISSIONS:
            try:
                request_permissions(ANDROID_PERMISSIONS)
            except Exception as e:
                print(f"Error requesting permissions: {e}")
    
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Dark"
        return self._create_main_page()
    
    def _create_main_page(self):
        # Create main page with vertical layout
        main_page = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Create and add the analysis button
        self.analysis_btn = self.create_analysis_button()
        main_page.add_widget(self.analysis_btn)
        
        # Create a container for main content and buttons
        content_and_buttons = BoxLayout(
            orientation='vertical',
            spacing=10,
            size_hint_y=0.8
        )
        
        # Create scrollable content
        main_scroll = ScrollView(size_hint=(1, 1))
        main_content = BoxLayout(
            orientation='vertical', 
            spacing=10, 
            size_hint_y=None
        )
        main_content.bind(minimum_height=main_content.setter('height'))
        
        # Image preview layout (side by side)
        image_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=200, spacing=10)
        
        # Input Image Preview
        self.input_image = KivyImage(
            source='',
            size_hint=(1, 1),
            fit_mode='contain'
        )
        self.input_image.opacity = 0
        
        # Output Image Preview
        self.output_image = KivyImage(
            source='',
            size_hint=(1, 1),
            fit_mode='contain'
        )
        self.output_image.opacity = 0
        
        image_layout.add_widget(self.input_image)
        image_layout.add_widget(self.output_image)
        main_content.add_widget(image_layout)
        
        # Mode selection
        mode_layout = BoxLayout(size_hint_y=None, height=50)
        self.text_mode = ToggleButton(text='Text Mode', state='down', group='mode')
        self.file_mode = ToggleButton(text='File Mode', group='mode')
        self.text_mode.bind(state=self.toggle_mode)
        self.file_mode.bind(state=self.toggle_mode)
        mode_layout.add_widget(self.text_mode)
        mode_layout.add_widget(self.file_mode)
        main_content.add_widget(mode_layout)
        
        # Carrier image selection
        carrier_layout = BoxLayout(size_hint_y=None, height=50)
        self.carrier_label = Label(text='Carrier Image:')
        carrier_layout.add_widget(self.carrier_label)
        self.carrier_btn = HighlightButton(text='Choose Image', size_hint_x=0.7)
        self.carrier_btn.bind(on_release=self.choose_carrier)
        carrier_layout.add_widget(self.carrier_btn)
        main_content.add_widget(carrier_layout)
        
        # Message input
        self.message_label = Label(text='Message:', size_hint_y=None, height=50)
        main_content.add_widget(self.message_label)
        self.message_input = TextInput(multiline=True, size_hint_y=None, height=100)
        main_content.add_widget(self.message_input)
        
        # File payload selection
        self.payload_label = Label(text='File to Hide:', size_hint_y=None, height=0, opacity=0)
        main_content.add_widget(self.payload_label)
        self.payload_btn = HighlightButton(text='Choose File', size_hint_y=None, height=0, opacity=0)
        self.payload_btn.bind(on_release=self.choose_payload)
        main_content.add_widget(self.payload_btn)
        
        main_scroll.add_widget(main_content)
        content_and_buttons.add_widget(main_scroll)
        
        # Create buttons and progress layout with fixed height
        button_and_progress = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=90,
            spacing=10
        )
        
        # Progress bar
        progress_layout = BoxLayout(size_hint_y=None, height=30)
        self.progress_bar = ProgressBar(max=100, value=0)
        progress_layout.add_widget(self.progress_bar)
        
        # Buttons layout
        button_layout = BoxLayout(
            size_hint_y=None, 
            height=50,
            spacing=10
        )
        hide_btn = HighlightButton(text='Hide Data')
        hide_btn.bind(on_release=self.hide_data)
        self.reveal_btn = HighlightButton(text='Reveal Data')
        self.reveal_btn.bind(on_release=self.reveal_data)
        button_layout.add_widget(hide_btn)
        button_layout.add_widget(self.reveal_btn)
        
        # Add progress and buttons to their container
        button_and_progress.add_widget(progress_layout)
        button_and_progress.add_widget(button_layout)
        content_and_buttons.add_widget(button_and_progress)
        
        # Create settings button
        settings_btn = HighlightButton(
            text='Advanced Settings',
            size_hint_y=None,
            height=50
        )
        settings_btn.bind(on_release=self.toggle_settings)
        
        # Add all containers to main page
        main_page.add_widget(content_and_buttons)
        main_page.add_widget(settings_btn)
        
        return main_page
    
    def on_mode_change(self, instance, value):
        if instance == self.file_mode and value == 'down':
            # Switch to file mode
            self.message_input.opacity = 0
            self.message_label.opacity = 0
            self.message_input.height = 0
            self.message_label.height = 0
            self.payload_label.opacity = 1
            self.payload_btn.opacity = 1
            self.payload_label.height = 50
            self.payload_btn.height = 50
        else:
            # Switch to text mode
            self.message_input.opacity = 1
            self.message_label.opacity = 1
            self.message_input.height = 100
            self.message_label.height = 50
            self.payload_label.opacity = 0
            self.payload_btn.opacity = 0
            self.payload_label.height = 0
            self.payload_btn.height = 0
    
    def choose_carrier(self, instance):
        try:
            # Show all image files with case-insensitive extensions
            filters = [["*.png", "*.PNG", "*.jpg", "*.JPG", "*.jpeg", "*.JPEG"]]
            filechooser.open_file(
                on_selection=lambda x: self.handle_carrier_selection(x) if x else None,
                filters=filters,
                title="Select Image",
                multiple=False
            )
        except NotImplementedError:
            self.message_input.text = "File chooser not supported on this platform"
        except Exception as e:
            self.message_input.text = f"Error opening file chooser: {str(e)}"
    
    def choose_payload(self, instance):
        try:
            filechooser.open_file(
                on_selection=self.handle_payload_selection,
                title="Select File to Hide",
                multiple=False
            )
        except NotImplementedError:
            # Fallback for platforms where filechooser is not implemented
            self.message_input.text = "File chooser not supported on this platform"
        except Exception as e:
            self.message_input.text = f"Error opening file chooser: {str(e)}"
    
    def handle_carrier_selection(self, selection):
        if selection:
            self.carrier_file = selection[0]
            self.carrier_label.text = f"Carrier: {os.path.basename(self.carrier_file)}"
            self.input_image.source = self.carrier_file
            self.input_image.opacity = 1
            self.output_image.opacity = 0
            self.output_image.source = ''
            
            # Show analysis button
            if hasattr(self, 'analysis_btn'):
                self.analysis_btn.opacity = 1
    
    def handle_payload_selection(self, selection):
        if selection:
            self.payload_file = selection[0]
            self.payload_label.text = f"Payload: {os.path.basename(self.payload_file)}"
    
    def update_progress(self, dt):
        if self.progress < 90:
            self.progress += 10
        self.progress_bar.value = self.progress

    def reset_progress(self):
        self.progress = 0
        self.progress_bar.value = 0
        self.progress_bar.opacity = 0

    def start_progress(self):
        self.progress = 0
        self.progress_bar.opacity = 1
        Clock.schedule_interval(self.update_progress, 0.1)

    def hide_data(self, instance):
        if not self.carrier_file:
            self.set_error_message("Please select a carrier image first")
            return
        if self.text_mode.state == 'down' and not self.message_input.text.strip():
            self.set_error_message("Please enter a message to hide")
            return
        if self.file_mode.state == 'down' and not self.payload_file:
            self.set_error_message("Please select a file to hide")
            return

        # Disable buttons
        instance.disabled = True
        self.carrier_btn.disabled = True
        self.payload_btn.disabled = True

        self.start_progress()
        def process():
            try:
                if self.text_mode.state == 'down':
                    message = self.message_input.text
                    settings = self.get_current_settings()
                    output_path = hide_message(self.carrier_file, message, settings)
                    if output_path and os.path.exists(output_path):
                        Clock.schedule_once(lambda dt, path=output_path: self.show_output_image(path))
                        Clock.schedule_once(lambda dt: self.set_success_message("Message hidden successfully!"))
                else:
                    settings = self.get_current_settings()
                    
                    # Handle 7z encryption if enabled
                    if self.seven_zip_spinner.text != 'Disabled':
                        if not self.seven_zip_password_input.text:
                            Clock.schedule_once(lambda dt: self.set_error_message("7z password is required"))
                            return
                        
                        # Create temporary 7z file with encrypted headers
                        with tempfile.NamedTemporaryFile(suffix='.7z', delete=False) as temp_7z:
                            with py7zr.SevenZipFile(temp_7z.name, 'w', 
                                                  password=self.seven_zip_password_input.text,
                                                  header_encryption=True) as archive:
                                archive.write(self.payload_file, os.path.basename(self.payload_file))
                        
                        # Read the 7z file
                        with open(temp_7z.name, 'rb') as f:
                            file_content = f.read()
                        
                        # Clean up temp file
                        os.unlink(temp_7z.name)
                        
                        if self.seven_zip_filename_input.text.strip():
                            filename = self.seven_zip_filename_input.text.strip()
                            if not filename.lower().endswith('.7z'):
                                filename += '.7z'
                        else:
                            filename = "encrypted.7z"
                    else:
                        with open(self.payload_file, 'rb') as f:
                            file_content = f.read()
                        filename = os.path.basename(self.payload_file)
                    
                    file_data = f"FILE:{filename}:{base64.b64encode(file_content).decode()}"
                    output_path = hide_message(self.carrier_file, file_data, settings)
                    
                    if output_path and os.path.exists(output_path):
                        Clock.schedule_once(lambda dt, path=output_path: self.show_output_image(path))
                        Clock.schedule_once(lambda dt: self.set_success_message("File hidden successfully!"))
                        Clock.schedule_once(lambda dt: self.reset_file_selection())
                    
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self.set_error_message(err))
            finally:
                Clock.schedule_once(lambda dt: self.complete_progress())
                Clock.schedule_once(lambda dt: self.enable_buttons(instance))
        
        threading.Thread(target=process).start()

    def reveal_data(self, instance):
        if not self.carrier_file:
            self.set_error_message("Please select a carrier image first")
            return
        
        # Disable UI during processing
        instance.disabled = True
        self.carrier_btn.disabled = True
        
        self.start_progress()
        
        def process():
            try:
                settings = self.get_current_settings()
                revealed_data = reveal_message(self.carrier_file, settings)
                
                # Update UI on main thread
                Clock.schedule_once(lambda dt: self.update_revealed_data(revealed_data))
            except Exception as e:
                # Store error message in a variable that can be accessed by the lambda
                error_msg = str(e)
                Clock.schedule_once(lambda dt: self.set_error_message(error_msg))
            finally:
                # Re-enable UI on main thread
                Clock.schedule_once(lambda dt: self.enable_buttons(instance))
                Clock.schedule_once(lambda dt: self.complete_progress())
        
        threading.Thread(target=process, daemon=True).start()

    def update_revealed_data(self, data):
        if self.text_mode.state == 'down':
            self.message_input.text = data
        else:
            # Check if the data starts with FILE: prefix
            if data.startswith('FILE:'):
                try:
                    # Split the data into filename and content
                    _, filename, encoded_content = data.split(':', 2)
                    file_content = base64.b64decode(encoded_content)
                    
                    # Generate unique filename in the same directory as carrier
                    base_path = os.path.join(os.path.dirname(self.carrier_file), filename)
                    output_path = self.get_unique_filename(base_path)
                    
                    # Write the file directly, whether it's 7z or not
                    with open(output_path, 'wb') as f:
                        f.write(file_content)
                    
                    self.message_input.text = f"File extracted successfully: {os.path.basename(output_path)}"
                except Exception as e:
                    self.message_input.text = f"Error extracting file: {str(e)}"
            else:
                self.message_input.text = "No valid file data found in image"

    def set_success_message(self, message):
        self.message_input.text = message
        self.progress = 100
        self.progress_bar.value = 100

    def set_error_message(self, error):
        self.message_input.text = f"Error: {error}"
        self.progress = 100
        self.progress_bar.value = 100

    def complete_progress(self):
        Clock.unschedule(self.update_progress)
        Clock.schedule_once(lambda dt: self.reset_progress(), 1)

    def show_output_image(self, path):
        if path and os.path.exists(path):
            self.output_image.source = path
            self.output_image.opacity = 1
        else:
            self.output_image.opacity = 0

    def get_unique_filename(self, base_path):
        """Generate a unique filename by appending a number if file exists"""
        if not os.path.exists(base_path):
            return base_path
        
        directory = os.path.dirname(base_path)
        filename = os.path.basename(base_path)
        name, ext = os.path.splitext(filename)
        
        counter = 1
        while os.path.exists(base_path):
            new_name = f"{name}_{counter}{ext}"
            base_path = os.path.join(directory, new_name)
            counter += 1
        
        return base_path

    def toggle_settings(self, instance):
        if not hasattr(self, 'settings_popup') or self.settings_popup is None:
            self.settings_popup = self.create_settings_popup()
        self.settings_popup.open()

    def get_current_settings(self):
        settings = SteganoSettings()
        settings.encoding = self.encoding_spinner.text
        settings.compression = self.compression_spinner.text
        if self.encryption_input.text:
            key = base64.b64encode(self.encryption_input.text.encode()[:32].ljust(32, b'\0'))
            settings.encryption_key = key
        if self.seven_zip_spinner.text == 'AES256':
            settings.seven_zip_encryption = True
        settings.custom_filename = self.custom_filename_input.text if self.custom_filename_input.text.strip() else None
        settings.custom_path = self.custom_path_input.text if self.custom_path_input.text.strip() else None
        return settings

    def toggle_mode(self, instance, value):
        if value == 'down':  # Only handle the button that's being pressed down
            if instance == self.text_mode:
                # Switch to text mode
                self.message_input.opacity = 1
                self.message_label.opacity = 1
                self.message_input.height = 100
                self.message_label.height = 50
                self.payload_label.opacity = 0
                self.payload_btn.opacity = 0
                self.payload_label.height = 0
                self.payload_btn.height = 0
            else:  # file_mode
                # Switch to file mode
                self.message_input.opacity = 0
                self.message_label.opacity = 0
                self.message_input.height = 0
                self.message_label.height = 0
                self.payload_label.opacity = 1
                self.payload_btn.opacity = 1
                self.payload_label.height = 50
                self.payload_btn.height = 50

    def on_seven_zip_change(self, instance, value):
        if value == 'AES256':
            self.seven_zip_password_layout.height = 40
            self.seven_zip_password_layout.opacity = 1
            self.seven_zip_password_input.disabled = False
            self.seven_zip_filename_layout.height = 40
            self.seven_zip_filename_layout.opacity = 1
            self.seven_zip_filename_input.disabled = False
            self.settings_popup.height = self.settings_popup.height + 80
        else:
            self.seven_zip_password_layout.height = 0
            self.seven_zip_password_layout.opacity = 0
            self.seven_zip_password_input.disabled = True
            self.seven_zip_filename_layout.height = 0
            self.seven_zip_filename_layout.opacity = 0
            self.seven_zip_filename_input.disabled = True
            self.settings_popup.height = self.settings_popup.height - 80

    def create_settings_popup(self):
        # Create popup content
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Create scrollview for settings
        scroll = ScrollView(size_hint=(1, 1))
        settings_layout = BoxLayout(
            orientation='vertical',
            spacing=5,
            size_hint_y=None
        )
        settings_layout.bind(minimum_height=settings_layout.setter('height'))
        
        # Add all settings widgets to the layout
        self.settings_panel = settings_layout
        self.create_settings_widgets()
        
        # Add close button
        close_button = HighlightButton(
            text='Close',
            size_hint=(1, None),
            height=50
        )
        
        # Create and setup popup
        self.settings_popup = Popup(
            title='Advanced Settings',
            content=content,
            size_hint=(0.8, 0.9),
            auto_dismiss=True
        )
        
        # Bind close button
        close_button.bind(on_release=self.settings_popup.dismiss)
        
        # Add widgets to content
        scroll.add_widget(settings_layout)
        content.add_widget(scroll)
        content.add_widget(close_button)
        
        return self.settings_popup

    def create_settings_widgets(self):
        # Add encoding selection
        encoding_layout = BoxLayout(size_hint_y=None, height=40)
        encoding_layout.add_widget(Label(text='Text Encoding:'))
        self.encoding_spinner = Spinner(
            text='utf-8',
            values=('utf-8', 'ascii', 'latin1', 'utf-16'),
            size_hint_x=0.7
        )
        encoding_layout.add_widget(self.encoding_spinner)
        self.settings_panel.add_widget(encoding_layout)

        # Add compression spinner
        compression_layout = BoxLayout(size_hint_y=None, height=40)
        compression_layout.add_widget(Label(text='Compression:'))
        self.compression_spinner = Spinner(
            text='None',
            values=('None', 'Fast', 'Default', 'Best'),
            size_hint_x=0.7
        )
        compression_layout.add_widget(self.compression_spinner)
        self.settings_panel.add_widget(compression_layout)

        # Add encryption key input
        encryption_layout = BoxLayout(size_hint_y=None, height=40)
        encryption_layout.add_widget(Label(text='Encryption Key:'))
        self.encryption_input = TextInput(
            multiline=False,
            size_hint_x=0.7
        )
        encryption_layout.add_widget(self.encryption_input)
        self.settings_panel.add_widget(encryption_layout)

        # Add 7z settings
        seven_zip_layout = BoxLayout(size_hint_y=None, height=40)
        seven_zip_layout.add_widget(Label(text='7z Encryption:'))
        self.seven_zip_spinner = Spinner(
            text='Disabled',
            values=('Disabled', 'AES256'),
            size_hint_x=0.7
        )
        self.seven_zip_spinner.bind(text=self.on_seven_zip_change)
        seven_zip_layout.add_widget(self.seven_zip_spinner)
        self.settings_panel.add_widget(seven_zip_layout)

        # Add 7z password input
        self.seven_zip_password_layout = BoxLayout(size_hint_y=None, height=0, opacity=0)
        self.seven_zip_password_layout.add_widget(Label(text='7z Password:'))
        self.seven_zip_password_input = TextInput(
            multiline=False,
            password=True,
            size_hint_x=0.7
        )
        self.seven_zip_password_layout.add_widget(self.seven_zip_password_input)
        self.settings_panel.add_widget(self.seven_zip_password_layout)

        # Add 7z filename input right after the password input
        self.seven_zip_filename_layout = BoxLayout(size_hint_y=None, height=0, opacity=0)
        self.seven_zip_filename_layout.add_widget(Label(text='7z Filename:'))
        self.seven_zip_filename_input = TextInput(
            multiline=False,
            size_hint_x=0.7,
            hint_text='Leave empty for encrypted.7z'
        )
        self.seven_zip_filename_layout.add_widget(self.seven_zip_filename_input)
        self.settings_panel.add_widget(self.seven_zip_filename_layout)

        # Add custom filename input
        filename_layout = BoxLayout(size_hint_y=None, height=40)
        filename_layout.add_widget(Label(text='Custom Filename:'))
        self.custom_filename_input = TextInput(
            multiline=False,
            size_hint_x=0.7,
            hint_text='Leave empty for default'
        )
        filename_layout.add_widget(self.custom_filename_input)
        self.settings_panel.add_widget(filename_layout)

        # Add custom path input with choose button
        path_layout = BoxLayout(size_hint_y=None, height=40)
        path_inner_layout = BoxLayout(size_hint_x=0.7)
        
        self.custom_path_input = TextInput(
            multiline=False,
            size_hint_x=0.7,
            hint_text='Leave empty for same folder'
        )
        path_choose_btn = HighlightButton(
            text='...',
            size_hint_x=0.3
        )
        path_choose_btn.bind(on_release=self.choose_custom_path)
        
        path_layout.add_widget(Label(text='Custom Path:'))
        path_inner_layout.add_widget(self.custom_path_input)
        path_inner_layout.add_widget(path_choose_btn)
        path_layout.add_widget(path_inner_layout)
        self.settings_panel.add_widget(path_layout)

    def reset_file_selection(self):
        self.payload_file = None
        self.payload_label.text = "File to Hide:"

    def enable_buttons(self, hide_reveal_btn):
        hide_reveal_btn.disabled = False
        self.carrier_btn.disabled = False
        self.payload_btn.disabled = False

    def choose_custom_path(self, instance):
        try:
            filechooser.choose_dir(
                on_selection=self.handle_path_selection,
                title="Select Output Directory"
            )
        except NotImplementedError:
            self.message_input.text = "Directory chooser not supported on this platform"
        except Exception as e:
            self.message_input.text = f"Error opening directory chooser: {str(e)}"

    def handle_path_selection(self, selection):
        if selection and len(selection) > 0:
            self.custom_path_input.text = selection[0]

    def on_reveal_press(self, instance):
        # Immediately disable to prevent double clicks
        instance.disabled = True
        # Re-enable after a short delay
        Clock.schedule_once(lambda dt: setattr(instance, 'disabled', False), 0.1)

    def create_analysis_button(self):
        analysis_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={'right': 0.98, 'top': 0.98},
            theme_icon_color="Custom",
            icon_color=(0, 0.7, 0.9, 1),  # Light blue color
            md_bg_color=(0.2, 0.2, 0.2, 0.9),  # Dark background
            opacity=0
        )
        analysis_btn.bind(on_release=self.show_analysis)
        return analysis_btn

    def show_analysis(self, instance):
        if not self.carrier_file:
            return
        
        # Create loading popup
        loading = Popup(
            title='Analyzing Image',
            content=Label(text='Please wait...'),
            size_hint=(0.4, 0.2),
            auto_dismiss=False
        )
        loading.open()
        
        def analyze_process():
            try:
                analyzer = ImageAnalyzer(self.carrier_file)
                results = analyzer.analyze()
                
                # Update UI on main thread
                Clock.schedule_once(lambda dt: self.show_analysis_results(results))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.set_error_message(f"Analysis error: {str(e)}"))
            finally:
                Clock.schedule_once(lambda dt: loading.dismiss())
        
        threading.Thread(target=analyze_process, daemon=True).start()

    def show_analysis_results(self, results):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        scroll = ScrollView(size_hint=(1, 0.9))
        info_layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            size_hint_y=None
        )
        info_layout.bind(minimum_height=info_layout.setter('height'))
        
        sections = [
            ('Basic Information', [
                f"Filename: {results['filename']}",
                f"Format: {results['basic_info']['format']}",
                f"Size: {results['basic_info']['size'][0]}x{results['basic_info']['size'][1]}",
                f"Mode: {results['basic_info']['mode']}",
                f"File Size: {results['basic_info']['file_size']}"
            ]),
            ('Steganography Analysis', [
                f"Hidden Data Detected: {'Yes' if results['steganography']['has_hidden_data'] else 'No'}",
                f"Confidence Level: {results['steganography']['confidence']}",
                "Detected Methods:" if results['steganography']['detected_methods'] else "No methods detected",
                *[f"• {method}" for method in results['steganography']['detected_methods']]
            ]),
            ('Statistical Analysis', [
                f"LSB Distribution: {results['statistical_analysis']['lsb_distribution']}",
                f"Randomness Test P-value: {results['statistical_analysis']['chi_square_p_value']}",
                f"Statistical Anomalies: {'Yes' if results['statistical_analysis']['randomness_suspicious'] else 'No'}"
            ]),
            ('Compression', [
                f"Type: {results['compression']['compression']}",
                f"Level: {results['compression']['compression_level']}",
                *results['compression']['details']
            ]),
            ('File Type Details', [
                results['file_type']
            ]),
            ('Metadata', [
                f"{k}: {v}" for k, v in results['metadata'].items()
            ])
        ]
        
        for section_title, items in sections:
            # Create section container
            section_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                padding=10,
                spacing=5
            )
            section_box.bind(minimum_height=section_box.setter('height'))
            
            # Create a unique update function for each section box
            def create_update_rect(box):
                def update_rect(instance, value):
                    box.rect.rectangle = (instance.x, instance.y, instance.width, instance.height)
                return update_rect
            
            # Add outline
            with section_box.canvas.before:
                Color(0.5, 0.5, 0.5, 1)  # Gray outline
                section_box.rect = Line(rectangle=(section_box.x, section_box.y, section_box.width, section_box.height), width=1.5)
            
            # Bind the update function specific to this section box
            update_rect = create_update_rect(section_box)
            section_box.bind(pos=update_rect, size=update_rect)
            
            # Add section title
            section_label = Label(
                text=f"[b]{section_title}[/b]",
                markup=True,
                size_hint_y=None,
                height=30,
                halign='left'
            )
            section_box.add_widget(section_label)
            
            # Add items
            for item in items:
                item_label = Label(
                    text=item,
                    size_hint_y=None,
                    height=25,
                    text_size=(None, 25),
                    halign='left'
                )
                section_box.add_widget(item_label)
            
            # Add section to main layout with spacing
            info_layout.add_widget(section_box)
            info_layout.add_widget(Widget(size_hint_y=None, height=10))
        
        scroll.add_widget(info_layout)
        content.add_widget(scroll)
        
        close_btn = HighlightButton(
            text='Close',
            size_hint_y=None,
            height=50
        )
        
        popup = Popup(
            title=f'Image Analysis - {results["filename"]}',
            content=content,
            size_hint=(0.8, 0.9),
            auto_dismiss=True
        )
        
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def on_filetype_change(self, instance, value):
        if value == 'JPEG':
            # Update compression options for JPEG
            self.compression_spinner.values = ('None', 'Optimized')
            self.compression_spinner.text = 'None'
        else:  # PNG
            # Update compression options for PNG
            self.compression_spinner.values = ('None', 'Fast', 'Default', 'Best')
            self.compression_spinner.text = 'None'
