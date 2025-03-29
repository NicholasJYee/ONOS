import ollama

class NoteGenerationService:
    @staticmethod
    def generate_note(transcript, model='deepseek-r1:1.5b'):
        try:
            response = ollama.chat(model=model, 
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a medical scribe assistant. Convert the following doctor-patient conversation into a structured medical note following standard SOAP format. Only include the assessment and plan.'
                    },
                    {
                        'role': 'user',
                        'content': transcript
                    }
                ])
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Note generation failed: {str(e)}") 