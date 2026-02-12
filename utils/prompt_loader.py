import os
import json

class PromptLoader:
    """Handles the retrieval and templating of AI prompt files from disk.

    This class serves as a central repository for all text-based assets, 
    including system instructions, user wrappers, and few-shot examples. 
    It supports dynamic variable injection using Python's string formatting.

    Attributes:
        base_path (str): The root directory where prompt folders are located.
    """

    def __init__(self, base_path="prompts"):
        """Initializes the loader with a target directory.

        Args:
            base_path (str): The folder containing 'system_prompts', 'templates', 
                and 'few_shot_examples'. Defaults to "prompts".
        """
        self.base_path = base_path

    def get_system_prompt(self, name: str, **variables) -> str:
        """Retrieves and renders a core system instruction file.

        System prompts define the 'Identity' and 'Persona' of the assistant.

        Args:
            name (str): The filename (without extension) in 'system_prompts/'.
            **variables: Arbitrary keyword arguments (e.g., current_time) 
                to inject into the template's {braces}.

        Returns:
            str: The fully rendered system instruction string.
        """
        # Automatically targets the system_prompts folder
        path = os.path.join(self.base_path, "system_prompts", f"{name}.txt")
        with open(path, "r", encoding="utf-8") as f:
            template = f.read()

        # This replaces {current_time} etc. with the values you pass in
        return template.format(**variables)

    def get_template(self, name: str, **kwargs) -> str:
        """Retrieves and renders a user-turn wrapper template.

        Templates are typically used to wrap raw user input with specific 
        instructions or constraints before sending to the model.

        Args:
            name (str): The filename in 'templates/'.
            **kwargs: Variables to inject (e.g., 'message').

        Returns:
            str: The rendered template string.
        """
        path = os.path.join(self.base_path, "templates", f"{name}.txt")
        with open(path, "r", encoding="utf-8") as f:
            template_content = f.read()
        
        # .format(**kwargs) maps variables to the {braces} in the file
        return template_content.format(**kwargs)
    
    def get_few_shot(self, name: str):
        """Loads a set of 'Golden Examples' for few-shot prompting.

        Args:
            name (str): The filename in 'few_shot_examples/'.

        Returns:
            list: A list of dictionaries representing 'user' and 'model' turns.
        """
        # Targets the few_shot_examples folder and parses JSON
        path = os.path.join(self.base_path, "few_shot_examples", f"{name}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def load_history(self, filename: str):
        """Legacy helper for loading raw history files. 
        
        Note:
            Usage is deprecated in favor of HistoryManager.load_history().
        """
        path = os.path.join(self.base_path, "history")