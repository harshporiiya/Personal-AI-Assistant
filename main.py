import os
import json
import datetime
import webbrowser
import subprocess
import requests
from typing import Dict, List, Any
import speech_recognition as sr
import pyttsx3
import schedule
import time
import threading

class PersonalAI:
    def __init__(self, name="Assistant"):
        self.name = name
        self.user_data = self.load_user_data()
        self.commands = {
            'time': self.get_time,
            'date': self.get_date,
            'weather': self.get_weather,
            'note': self.take_note,
            'notes': self.show_notes,
            'reminder': self.set_reminder,
            'search': self.web_search,
            'open': self.open_application,
            'calculate': self.calculate,
            'todo': self.manage_todo,
            'help': self.show_help,
            'quit': self.quit_assistant
        }
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self.setup_voice()
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        print(f"🤖 {self.name} initialized! Type 'help' for available commands or 'quit' to exit.")

    def setup_voice(self):
        """Configure text-to-speech settings"""
        voices = self.tts_engine.getProperty('voices')
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)  # Use first available voice
        self.tts_engine.setProperty('rate', 200)  # Speed of speech
        self.tts_engine.setProperty('volume', 0.9)  # Volume level

    def speak(self, text: str):
        """Convert text to speech"""
        print(f"🤖 {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self) -> str:
        """Listen for voice input and convert to text"""
        try:
            with self.microphone as source:
                print("🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=5)
            
            text = self.recognizer.recognize_google(audio).lower()
            print(f"🗣️ You said: {text}")
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            self.speak("Sorry, I couldn't understand that.")
            return ""
        except sr.RequestError:
            self.speak("Speech recognition service is unavailable.")
            return ""

    def load_user_data(self) -> Dict[str, Any]:
        """Load user data from file"""
        try:
            with open('user_data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'notes': [],
                'reminders': [],
                'todo_list': [],
                'preferences': {}
            }

    def save_user_data(self):
        """Save user data to file"""
        with open('user_data.json', 'w') as f:
            json.dump(self.user_data, f, indent=2)

    def get_time(self, args: List[str] = None) -> str:
        """Get current time"""
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}"

    def get_date(self, args: List[str] = None) -> str:
        """Get current date"""
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}"

    def get_weather(self, args: List[str] = None) -> str:
        """Get weather information (requires API key)"""
        # You'll need to get a free API key from OpenWeatherMap
        api_key = "YOUR_WEATHER_API_KEY"
        city = " ".join(args) if args else "New York"
        
        if api_key == "YOUR_WEATHER_API_KEY":
            return "Weather service not configured. Please add your OpenWeatherMap API key."
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                description = data['weather'][0]['description']
                return f"The weather in {city} is {temp}°C with {description}"
            else:
                return f"Sorry, couldn't get weather for {city}"
        except Exception as e:
            return "Weather service is currently unavailable"

    def take_note(self, args: List[str]) -> str:
        """Take a note"""
        if not args:
            return "Please provide a note to save"
        
        note = {
            'content': " ".join(args),
            'timestamp': datetime.datetime.now().isoformat(),
            'id': len(self.user_data['notes']) + 1
        }
        self.user_data['notes'].append(note)
        self.save_user_data()
        return f"Note saved: {note['content']}"

    def show_notes(self, args: List[str] = None) -> str:
        """Show all notes"""
        if not self.user_data['notes']:
            return "No notes found"
        
        notes_text = "Your notes:\n"
        for note in self.user_data['notes'][-5:]:  # Show last 5 notes
            timestamp = datetime.datetime.fromisoformat(note['timestamp']).strftime("%m/%d %H:%M")
            notes_text += f"• [{timestamp}] {note['content']}\n"
        return notes_text

    def set_reminder(self, args: List[str]) -> str:
        """Set a reminder"""
        if not args:
            return "Please provide a reminder message"
        
        reminder = {
            'message': " ".join(args),
            'created': datetime.datetime.now().isoformat(),
            'id': len(self.user_data['reminders']) + 1
        }
        self.user_data['reminders'].append(reminder)
        self.save_user_data()
        return f"Reminder set: {reminder['message']}"

    def web_search(self, args: List[str]) -> str:
        """Open web search"""
        if not args:
            return "Please provide a search query"
        
        query = "+".join(args)
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"Searching for: {' '.join(args)}"

    def open_application(self, args: List[str]) -> str:
        """Open an application"""
        if not args:
            return "Please specify an application to open"
        
        app = args[0].lower()
        try:
            if app in ['notepad', 'calculator', 'paint']:
                subprocess.run([app], check=True)
                return f"Opening {app}"
            elif app == 'browser':
                webbrowser.open('https://www.google.com')
                return "Opening browser"
            else:
                return f"Don't know how to open {app}"
        except Exception as e:
            return f"Couldn't open {app}: {str(e)}"

    def calculate(self, args: List[str]) -> str:
        """Perform basic calculations"""
        if not args:
            return "Please provide a calculation"
        
        try:
            expression = " ".join(args)
            # Basic safety check - only allow numbers and basic operators
            allowed_chars = set('0123456789+-*/.()')
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return "Invalid characters in calculation"
            
            result = eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return "Invalid calculation"

    def manage_todo(self, args: List[str]) -> str:
        """Manage todo list"""
        if not args:
            if not self.user_data['todo_list']:
                return "Your todo list is empty"
            
            todo_text = "Your todo list:\n"
            for i, item in enumerate(self.user_data['todo_list'], 1):
                status = "✓" if item.get('done', False) else "○"
                todo_text += f"{status} {i}. {item['task']}\n"
            return todo_text
        
        action = args[0].lower()
        
        if action == 'add' and len(args) > 1:
            task = " ".join(args[1:])
            self.user_data['todo_list'].append({'task': task, 'done': False})
            self.save_user_data()
            return f"Added to todo: {task}"
        
        elif action == 'done' and len(args) > 1:
            try:
                index = int(args[1]) - 1
                if 0 <= index < len(self.user_data['todo_list']):
                    self.user_data['todo_list'][index]['done'] = True
                    self.save_user_data()
                    return f"Marked task {args[1]} as done"
                else:
                    return "Invalid task number"
            except ValueError:
                return "Please provide a valid task number"
        
        return "Usage: todo [add <task>] | [done <number>] | [show all]"

    def show_help(self, args: List[str] = None) -> str:
        """Show available commands"""
        help_text = """
Available commands:
• time - Get current time
• date - Get current date
• weather [city] - Get weather info
• note <message> - Save a note
• notes - Show recent notes
• reminder <message> - Set a reminder
• search <query> - Web search
• open <app> - Open application
• calculate <expression> - Basic math
• todo [add/done/show] - Manage todo list
• help - Show this help
• quit - Exit assistant

Voice mode: Say 'listen' to use voice input!
        """
        return help_text.strip()

    def quit_assistant(self, args: List[str] = None) -> str:
        """Quit the assistant"""
        self.save_user_data()
        return "Goodbye! Have a great day!"

    def process_command(self, user_input: str) -> str:
        """Process user command"""
        if not user_input.strip():
            return "Please enter a command or say 'help' for available options"
        
        parts = user_input.lower().strip().split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.commands:
            try:
                result = self.commands[command](args)
                return result
            except Exception as e:
                return f"Error executing command: {str(e)}"
        else:
            return f"Unknown command: {command}. Type 'help' for available commands."

    def run(self):
        """Main loop"""
        try:
            while True:
                # Text input
                user_input = input("\n🎯 Enter command (or 'listen' for voice): ").strip()
                
                if user_input.lower() == 'listen':
                    voice_input = self.listen()
                    if voice_input:
                        user_input = voice_input
                    else:
                        continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    response = self.quit_assistant()
                    self.speak(response)
                    break
                
                response = self.process_command(user_input)
                self.speak(response)
                
        except KeyboardInterrupt:
            response = self.quit_assistant()
            self.speak(response)
        except Exception as e:
            print(f"An error occurred: {e}")

def main():
    # Create and run the personal AI assistant
    assistant = PersonalAI("Your Personal AI")
    assistant.run()

if __name__ == "__main__":
    # Required packages (install with pip):
    # pip install speechrecognition pyttsx3 requests schedule pyaudio
    
    print("🚀 Starting Personal AI Assistant...")
    print("Note: Install required packages with:")
    print("pip install speechrecognition pyttsx3 requests schedule pyaudio")
    print()
    
    main()