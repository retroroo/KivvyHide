from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image
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

class SteganoApp(App):
    progress = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carrier_file = None
        self.payload_file = None
        if platform == 'android' and ANDROID_PERMISSIONS:
            self.request_android_permissions()
        
    def request_android_permissions(self):
        if platform == 'android' and ANDROID_PERMISSIONS:
            try:
                request_permissions(ANDROID_PERMISSIONS)
            except Exception as e:
                print(f"Error requesting permissions: {e}")
    
    def build(self):
        # Create a main layout that will contain everything
        root_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Create a scrollable content layout for the main interface
        content_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        content_layout.bind(minimum_height=content_layout.setter('height'))
        
        # Image preview layout (side by side)
        image_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=200, spacing=10)
        
        # Input Image Preview
        self.input_image = Image(
            source='',
            size_hint=(1, 1),
            fit_mode='contain'
        )
        self.input_image.opacity = 0
        
        # Output Image Preview
        self.output_image = Image(
            source='',
            size_hint=(1, 1),
            fit_mode='contain'
        )
        self.output_image.opacity = 0
        
        image_layout.add_widget(self.input_image)
        image_layout.add_widget(self.output_image)
        content_layout.add_widget(image_layout)
        
        # Mode selection
        mode_layout = BoxLayout(size_hint_y=None, height=50)
        self.text_mode = ToggleButton(text='Text Mode', state='down', group='mode')
        self.file_mode = ToggleButton(text='File Mode', group='mode')
        self.text_mode.bind(state=self.toggle_mode)
        self.file_mode.bind(state=self.toggle_mode)
        mode_layout.add_widget(self.text_mode)
        mode_layout.add_widget(self.file_mode)
        content_layout.add_widget(mode_layout)
        
        # Carrier image selection
        carrier_layout = BoxLayout(size_hint_y=None, height=50)
        self.carrier_label = Label(text='Carrier Image:')
        carrier_layout.add_widget(self.carrier_label)
        self.carrier_btn = HighlightButton(text='Choose Image', size_hint_x=0.7)
        self.carrier_btn.bind(on_release=self.choose_carrier)
        carrier_layout.add_widget(self.carrier_btn)
        content_layout.add_widget(carrier_layout)
        
        # Message input
        self.message_label = Label(text='Message:', size_hint_y=None, height=50)
        content_layout.add_widget(self.message_label)
        self.message_input = TextInput(multiline=True, size_hint_y=None, height=100)
        content_layout.add_widget(self.message_input)
        
        # File payload selection
        self.payload_label = Label(text='File to Hide:', size_hint_y=None, height=0, opacity=0)
        content_layout.add_widget(self.payload_label)
        self.payload_btn = HighlightButton(text='Choose File', size_hint_y=None, height=0, opacity=0)
        self.payload_btn.bind(on_release=self.choose_payload)
        content_layout.add_widget(self.payload_btn)
        
        # Progress bar
        self.progress_bar = ProgressBar(max=100, size_hint_y=None, height=20)
        content_layout.add_widget(self.progress_bar)
        
        # Add the advanced settings at the bottom
        settings_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        settings_layout.bind(minimum_height=settings_layout.setter('height'))

        # Create toggle button in its own layout (always enabled)
        self.settings_toggle = ToggleButton(
            text='Advanced Settings',
            size_hint_y=None,
            height=50
        )
        self.settings_toggle.bind(state=self.toggle_settings)
        settings_layout.add_widget(self.settings_toggle)

        # Settings panel with dropdowns (separate from toggle button)
        self.settings_panel = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            height=0,
            opacity=0
        )

        # Add encoding spinner
        encoding_layout = BoxLayout(size_hint_y=None, height=40)
        encoding_layout.add_widget(Label(text='Encoding:'))
        self.encoding_spinner = Spinner(
            text='utf-8',
            values=('utf-8', 'ascii', 'latin1'),
            size_hint_x=0.7
        )
        encoding_layout.add_widget(self.encoding_spinner)
        self.settings_panel.add_widget(encoding_layout)

        # Add compression spinner
        compression_layout = BoxLayout(size_hint_y=None, height=40)
        compression_layout.add_widget(Label(text='Compression:'))
        self.compression_spinner = Spinner(
            text='Disabled',
            values=('Enabled', 'Disabled'),
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

        settings_layout.add_widget(self.settings_panel)
        content_layout.add_widget(settings_layout)
        
        # Create a ScrollView to contain the content
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(content_layout)
        root_layout.add_widget(scroll_view)
        
        # Action buttons
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        hide_btn = HighlightButton(text='Hide Data')
        hide_btn.bind(on_release=self.hide_data)
        reveal_btn = HighlightButton(text='Reveal Data')
        reveal_btn.bind(on_release=self.reveal_data)
        button_layout.add_widget(hide_btn)
        button_layout.add_widget(reveal_btn)
        root_layout.add_widget(button_layout)
        
        return root_layout
    
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
                    with open(self.payload_file, 'rb') as f:
                        file_content = f.read()
                    
                    filename = os.path.basename(self.payload_file)
                    file_data = f"FILE:{filename}:{base64.b64encode(file_content).decode()}"
                    
                    settings = self.get_current_settings()
                    output_path = hide_message(self.carrier_file, file_data, settings)
                    if output_path and os.path.exists(output_path):
                        Clock.schedule_once(lambda dt, path=output_path: self.show_output_image(path))
                        Clock.schedule_once(lambda dt: self.set_success_message("File hidden successfully!"))
                    
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self.set_error_message(err))
            finally:
                Clock.schedule_once(lambda dt: self.complete_progress(), 1)
        
        threading.Thread(target=process).start()

    def reveal_data(self, instance):
        if not self.carrier_file:
            self.set_error_message("Please select a carrier image first")
            return
        
        self.start_progress()
        
        def process():
            try:
                settings = self.get_current_settings()
                revealed_data = reveal_message(self.carrier_file, settings)
                
                if not revealed_data:
                    Clock.schedule_once(lambda dt: self.set_error_message("No hidden data found in image"))
                    return
                    
                if revealed_data.startswith("FILE:"):
                    try:
                        _, filename, content = revealed_data.split(":", 2)
                        base_save_path = os.path.join(os.path.dirname(self.carrier_file), f"revealed_{filename}")
                        save_path = self.get_unique_filename(base_save_path)
                        
                        with open(save_path, 'wb') as f:
                            f.write(base64.b64decode(content))
                        
                        Clock.schedule_once(lambda dt, msg=f"File revealed and saved as: {save_path}": self.set_success_message(msg))
                    except Exception as error:
                        Clock.schedule_once(lambda dt, err=f"Error extracting file: {str(error)}": self.set_error_message(err))
                else:
                    Clock.schedule_once(lambda dt, msg=f"Revealed message: {revealed_data}": self.set_success_message(msg))
                    
            except Exception as error:
                Clock.schedule_once(lambda dt, err=str(error): self.set_error_message(err))
            finally:
                Clock.schedule_once(lambda dt: self.complete_progress(), 1)
        
        threading.Thread(target=process).start()

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

    def toggle_settings(self, instance, value):
        if value == 'down':
            # Show and enable settings
            self.settings_panel.height = 160
            self.settings_panel.opacity = 1
            # Enable only the settings widgets, not the toggle button
            self.encoding_spinner.disabled = False
            self.compression_spinner.disabled = False
            self.encryption_input.disabled = False
        else:
            # Hide and disable settings
            self.settings_panel.height = 0
            self.settings_panel.opacity = 0
            # Disable only the settings widgets, not the toggle button
            self.encoding_spinner.disabled = True
            self.compression_spinner.disabled = True
            self.encryption_input.disabled = True
        
        # Force layout update
        self.settings_panel.parent.minimum_height = self.settings_toggle.height + self.settings_panel.height

    def get_current_settings(self):
        settings = SteganoSettings()
        settings.encoding = self.encoding_spinner.text
        settings.compression = self.compression_spinner.text == 'Enabled'
        if self.encryption_input.text:
            key = base64.b64encode(self.encryption_input.text.encode()[:32].ljust(32, b'\0'))
            settings.encryption_key = key
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
