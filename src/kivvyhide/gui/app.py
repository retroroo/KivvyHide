from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivvyhide.utils.stegano_wrapper import hide_message, reveal_message
from plyer import filechooser
import base64
import os
import threading

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
        
    def build(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Progress Bar
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=30)
        self.progress_bar.opacity = 0
        layout.add_widget(self.progress_bar)
        
        # Carrier file selection (image file)
        self.carrier_label = Label(text='No carrier image selected')
        layout.add_widget(self.carrier_label)
        
        carrier_btn = Button(
            text='Select Carrier Image',
            size_hint_y=None,
            height=50
        )
        carrier_btn.bind(on_press=self.choose_carrier)
        layout.add_widget(carrier_btn)
        
        # Toggle between text and file mode
        mode_layout = BoxLayout(size_hint_y=None, height=50)
        self.text_mode = ToggleButton(text='Text Mode', state='down', group='mode')
        self.file_mode = ToggleButton(text='File Mode', group='mode')
        mode_layout.add_widget(self.text_mode)
        mode_layout.add_widget(self.file_mode)
        layout.add_widget(mode_layout)
        
        # Text input for message
        self.message_input = TextInput(
            multiline=True,
            hint_text='Enter message to hide/reveal',
            size_hint_y=None,
            height=100
        )
        self.message_label = Label(text='Message:')
        layout.add_widget(self.message_label)
        layout.add_widget(self.message_input)
        
        # File selection for payload
        self.payload_label = Label(text='No payload file selected')
        self.payload_btn = Button(
            text='Select File to Hide',
            size_hint_y=None,
            height=50
        )
        self.payload_btn.bind(on_press=self.choose_payload)
        
        # Initially hide file selection widgets
        self.payload_label.opacity = 0
        self.payload_btn.opacity = 0
        self.payload_label.size_hint_y = None
        self.payload_btn.size_hint_y = None
        self.payload_label.height = 0
        self.payload_btn.height = 0
        
        layout.add_widget(self.payload_label)
        layout.add_widget(self.payload_btn)
        
        # Bind mode toggles
        self.text_mode.bind(state=self.on_mode_change)
        self.file_mode.bind(state=self.on_mode_change)
        
        # Action Buttons
        button_layout = BoxLayout(size_hint_y=None, height=50)
        hide_btn = HighlightButton(text='Hide')
        hide_btn.bind(on_press=self.hide_data)
        reveal_btn = HighlightButton(text='Reveal')
        reveal_btn.bind(on_press=self.reveal_data)
        
        button_layout.add_widget(hide_btn)
        button_layout.add_widget(reveal_btn)
        layout.add_widget(button_layout)
        
        return layout
    
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
            filechooser.open_file(
                on_selection=self.handle_carrier_selection,
                filters=[('Image Files', '*.png', '*.jpg', '*.jpeg')]
            )
        except Exception as e:
            self.message_input.text = f"Error opening file chooser: {str(e)}"
    
    def choose_payload(self, instance):
        try:
            filechooser.open_file(
                on_selection=self.handle_payload_selection,
            )
        except Exception as e:
            self.message_input.text = f"Error opening file chooser: {str(e)}"
    
    def handle_carrier_selection(self, selection):
        if selection:
            self.carrier_file = selection[0]
            self.carrier_label.text = f"Carrier: {os.path.basename(self.carrier_file)}"
    
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
                    hide_message(self.carrier_file, message)
                    Clock.schedule_once(lambda dt, msg="Message hidden successfully!": self.set_success_message(msg))
                else:
                    with open(self.payload_file, 'rb') as f:
                        file_content = f.read()
                    
                    filename = os.path.basename(self.payload_file)
                    file_data = f"FILE:{filename}:{base64.b64encode(file_content).decode()}"
                    
                    hide_message(self.carrier_file, file_data)
                    Clock.schedule_once(lambda dt, msg="File hidden successfully!": self.set_success_message(msg))
                    
            except Exception as error:
                Clock.schedule_once(lambda dt, err=str(error): self.set_error_message(err))
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
                revealed_data = reveal_message(self.carrier_file)
                
                if not revealed_data:
                    Clock.schedule_once(lambda dt: self.set_error_message("No hidden data found in image"))
                    return
                    
                if revealed_data.startswith("FILE:"):
                    try:
                        _, filename, content = revealed_data.split(":", 2)
                        save_path = os.path.join(os.path.dirname(self.carrier_file), f"revealed_{filename}")
                        
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
