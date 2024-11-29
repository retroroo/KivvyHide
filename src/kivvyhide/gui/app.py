from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivvyhide.utils.stegano_wrapper import hide_message, reveal_message
from plyer import filechooser
import base64
import os

class SteganoApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carrier_file = None  # Image file to hide data in
        self.payload_file = None  # File to be hidden
        
    def build(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
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
        hide_btn = Button(text='Hide')
        hide_btn.bind(on_press=self.hide_data)
        reveal_btn = Button(text='Reveal')
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
    
    def hide_data(self, instance):
        if not self.carrier_file:
            self.message_input.text = "Please select a carrier image first"
            return
        
        try:
            if self.text_mode.state == 'down':
                # Text mode
                message = self.message_input.text
                hide_message(self.carrier_file, message)
                self.message_input.text = "Message hidden successfully!"
            else:
                # File mode
                if not self.payload_file:
                    self.message_input.text = "Please select a file to hide"
                    return
                    
                with open(self.payload_file, 'rb') as f:
                    file_content = f.read()
                    
                # Create a header with filename and content
                filename = os.path.basename(self.payload_file)
                file_data = f"FILE:{filename}:{base64.b64encode(file_content).decode()}"
                
                hide_message(self.carrier_file, file_data)
                self.message_input.text = "File hidden successfully!"
                
        except Exception as e:
            self.message_input.text = f"Error: {str(e)}"
    
    def reveal_data(self, instance):
        if not self.carrier_file:
            self.message_input.text = "Please select a carrier image first"
            return
        
        try:
            revealed_data = reveal_message(self.carrier_file)
            
            if revealed_data.startswith("FILE:"):
                # Handle file data
                _, filename, content = revealed_data.split(":", 2)
                save_path = os.path.join(os.path.dirname(self.carrier_file), f"revealed_{filename}")
                
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(content))
                
                self.message_input.text = f"File revealed and saved as: {save_path}"
            else:
                # Handle text data
                self.message_input.text = f"Revealed message: {revealed_data}"
                
        except Exception as e:
            self.message_input.text = f"Error: {str(e)}"
