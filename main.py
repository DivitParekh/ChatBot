from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
import google.generativeai as genai 
import cx_Oracle
import hashlib
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle 
from kivymd.app import MDApp
from kivy.lang import Builder

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyA08lpke3pG_IwuJifzX4VNLgnF8eHSUls"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Database Connection Setup
dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")

try:
    conn = cx_Oracle.connect(user="divitparekh", password="pass123", dsn=dsn)
    cursor = conn.cursor()
    
    # Ensure the users table exists
    cursor.execute("""
    BEGIN
        EXECUTE IMMEDIATE 'CREATE TABLE users (
            id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            username VARCHAR2(50) UNIQUE NOT NULL,
            password VARCHAR2(255) NOT NULL
        )';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE != -955 THEN -- Table already exists error
                RAISE;
            END IF;
    END;
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
except cx_Oracle.DatabaseError as e:
    print("Database connection error:", str(e))

# Password Hashing Function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Login Screen Class
class LoginScreen(Screen):
    def login(self):
        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text.strip()

        if not username or not password:
            self.ids.error_label.text = "❌ Username and password required!"
            return

        try:
            conn = cx_Oracle.connect(user="divitparekh", password="pass123", dsn=dsn)
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = :1", (username,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0] == hash_password(password):
                self.manager.current = "chat"
            else:
                self.ids.error_label.text = "❌ Invalid username or password!"
        except cx_Oracle.DatabaseError as e:
            self.ids.error_label.text = f"❌ Database Error: {str(e)}"

    def register(self):
        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text.strip()

        if not username or not password:
            self.ids.error_label.text = "❌ Username and password required!"
            return

        try:
            conn = cx_Oracle.connect(user="divitparekh", password="pass123", dsn=dsn)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (:1, :2)", (username, hash_password(password)))
            conn.commit()
            cursor.close()
            conn.close()
            self.ids.error_label.text = "✅ User registered successfully!"
        except cx_Oracle.DatabaseError as e:
            self.ids.error_label.text = f"❌ Database Error: {str(e)}"



# Chat Screen Class
class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        self.scroll_view = ScrollView()
        self.chat_history = BoxLayout(orientation='vertical', size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))
        self.scroll_view.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_view)

        self.user_input = TextInput(size_hint_y=None, height=50, multiline=False)
        self.user_input.bind(on_text_validate=self.send_message)
        self.layout.add_widget(self.user_input)

        send_button = Button(text="Send", size_hint_y=None, height=50)
        send_button.bind(on_press=self.send_message)
        self.layout.add_widget(send_button)

        self.add_widget(self.layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def send_message(self, instance):
        user_text = self.user_input.text.strip()
        if not user_text:
            return
        
        self.add_message(f"You: {user_text}", 'black')
        bot_response = self.chat_with_gemini(user_text)
        self.add_message(f"Bot: {bot_response}", 'black')
        self.user_input.text = ""

    def chat_with_gemini(self, prompt):
        try:
            response = model.generate_content(prompt)
            return response.text.strip() if response.text else "Error: No response from AI"
        except Exception as e:
            return f"Error: {str(e)}"

    def add_message(self, text, text_color):
        label = Label(text=text, size_hint_y=None, height=30, color=(0, 0, 0, 1))
        self.chat_history.add_widget(label)
        self.scroll_view.scroll_y = 0

# Main ChatBot App Class
class ChatBotApp(MDApp):
    def build(self):
        # Load the .kv file
        Builder.load_file("chatbot.kv")  # This links the .kv file
        
        # Create Screen Manager
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(ChatScreen(name="chat"))
        return sm

# Run the App
if __name__ == "__main__":
    ChatBotApp().run()
