import ollama

class NoteGenerationService:
    @staticmethod
    def generate_note(transcript):
        try:
            # You can use different models like 'mistral', 'llama2', 'mixtral'
            # Run 'ollama pull mistral' first to download the model
            response = ollama.chat(model='mistral', 
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a medical scribe assistant. Convert the following doctor-patient conversation into a structured medical note following standard SOAP format.'
                    },
                    {
                        'role': 'user',
                        'content': transcript
                    }
                ])
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Note generation failed: {str(e)}") 