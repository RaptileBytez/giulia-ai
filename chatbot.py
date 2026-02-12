from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from utils import PromptLoader, HistoryManager
from datetime import datetime

# Load the variables from .env into the system environment
load_dotenv()

class Chatbot:
    """Orchestrates the interaction between the Gemini 3 LLM and local persistence.

    This class serves as the central hub for the assistant 'Giulia'. it manages 
    the stateful conversation by combining a static system persona with dynamic 
    session history and user input.

    Attributes:
        loader (PromptLoader): Utility for reading and rendering prompt templates.
        history_manager (HistoryManager): Utility for JSON-based session persistence.
        session_id (str): The unique identifier for the current chat session.
        messages (list[types.Content]): The in-memory list of conversation turns.
        client (genai.Client): The authenticated Google GenAI client.
    """
    def __init__(self, session_id="default_user"):
        """Initializes Giulia with her persona and re-establishes session history.

        Args:
            session_id (str): Determines the filename for history storage. 
                Defaults to "default_boss".
        """
        self.loader = PromptLoader()
        self.history_manager = HistoryManager()
        self.session_id = session_id

        now = datetime.now().strftime("%I:%M %p")
        # Load System Instruction from file
        self.system_instruction = self.loader.get_system_prompt(
            "giulia_assistant",
            current_time=now, 
            location="your private office"
        )

        # Load persistent history
        self.messages = self.history_manager.load_history(self.session_id)

        # Setup client
        self.client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    attempts=3,
                    initial_delay=2.0,
                    max_delay=60.0
                )
            )
        )
        self.model = "gemini-3-flash-preview"        

        # Define Safety Settings:
        safety_config = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            )
        ]

        # Create chat session
        self.chat = self.client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                safety_settings=safety_config 
            )
        )
        print(f"ℹ️\tChatbot initialized with {self.model}.")

    
    def get_response(self, message:str) -> str:
        """Processes user input and returns a persona-aligned response.

        The method wraps the raw message in a short directive, updates the 
        local history, and calls the Gemini API.

        Args:
            message (str): Raw text input from the terminal/user.

        Returns:
            str: Giulia's seductive and helpful response text.
        """
        # 1. Wrap the user message in your seductive template
        user_text = self.loader.get_template("boss_template", message=message)
        
        ## Create the user message as a formal Object
        user_msg = types.Content(
            role="user", 
            parts=[types.Part(text=user_text)]
        )
        self.messages.append(user_msg)

        try:
            # 3. Use 'generate_content' instead of 'start_chat'
            # In Gemini 3, sending the whole list is the most reliable way to maintain state
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.messages, # We pass the whole history here
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction
                )
            )
            
            # Capture the model's reply as a formal Object
            model_msg = types.Content(
                role="model",
                parts=[types.Part(text=response.text)]
            )
            self.messages.append(model_msg)
            
            # 5. Save the whole list back to your JSON file
            self.history_manager.save_history(self.session_id, self.messages)

            return str(response.text)
        
        except errors.ServerError:
            # Julia handles the "overload" gracefully
            return "I'm a bit overwhelmed with work right now, boss. Give me a moment to catch my breath?"
        
        except Exception as e:
            # Catch other unexpected errors
            print(f"❌ Unexpected Error: {e}")
            return "Something went wrong in the office. Check the logs?"