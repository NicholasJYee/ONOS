import ollama

class NoteGenerationService:
    @staticmethod
    def generate_note(transcript, model='deepseek-r1:1.5b'):
        try:
            response = ollama.chat(model=model, 
                messages=[
                    {
                        'role': 'system',
                        'content': "You are a medical scribe assistant. Convert the following doctor-patient conversation into a structured medical note following standard SOAP format (don't include any pre-amble)."
                    },
                    {
                        'role': 'user',
                        'content': transcript
                    }
                ])
            note_content = response['message']['content']
            
            # Remove reasoning tokens for deepseek models
            if "deepseek" in model and "</think>" in note_content:
                note_content = note_content.split("</think>", 1)[1].strip()
                
            return note_content
        except Exception as e:
            raise Exception(f"Note generation failed: {str(e)}") 