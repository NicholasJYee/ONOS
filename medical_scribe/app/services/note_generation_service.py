import ollama
from typing import List, Optional
from pathlib import Path

class NoteGenerationService:
    @staticmethod
    def generate_note(transcript: str, model: str = 'deepseek-r1:1.5b', previous_note: str = None, is_complete: bool = True) -> str:
        """Generate a SOAP note from a medical transcript.
        
        Args:
            transcript: The medical conversation transcript
            model: The LLM model to use (default: 'deepseek-r1:1.5b')
            previous_note: Optional previous SOAP note to update
            is_complete: Whether this is a complete transcript (default: True)
        """
        try:
            system_message = {
                'role': 'system',
                'content': "You are a medical scribe assistant. "
            }

            # Add SOAP format instructions
            system_message['content'] += (
                "Convert the following doctor-patient conversation into a structured medical "
                "note following the SOAP format. Only include sections where relevant information "
                "is explicitly mentioned in the conversation. Each section should only appear if "
                "there is specific information for it.\n\n"
                "Available sections and their components:\n\n"
                "- Chief complaint (CC) or duration of follow-up\n"
                "- History of Present Illness (HPI)\n"
                "- Review of Systems (ROS) relevant to the complaint\n"
                "- Past Medical History (PMHx)\n"
                "- Current medications and allergies\n"
                "- Family and Social history\n\n"
                "OBJECTIVE (O) - Include only if physical findings/measurements are mentioned:\n"
                "- Vital signs\n"
                "- Physical examination findings\n"
                "- Laboratory or imaging results\n"
                "- Observable measurements or data\n\n"
                "ASSESSMENT (A) - Include only if diagnoses/interpretations are discussed:\n"
                "- Primary diagnosis or differential diagnoses\n"
                "- Clinical reasoning and interpretation\n"
                "- Status of conditions\n\n"
                "PLAN (P) - Include only if future actions are specified:\n"
                "- Ordered tests or procedures\n"
                "- Prescribed medications or treatments\n"
                "- Referrals or consultations\n"
                "- Follow-up instructions\n"
                "- Patient education\n\n"
                "Important:\n"
                "- Only include sections that have explicit information from the conversation\n"
                "- Omit any section entirely if no relevant information was discussed\n"
                "- Do not include placeholder text or assumptions\n"
                "- Do not include any pre-amble or commentary"
            )

            if previous_note:
                system_message['content'] += (
                    "\n\nUpdate the existing SOAP note with new information from the conversation. "
                    "Maintain the existing structure while adding or modifying relevant details. "
                    "Ensure consistency between old and new information. "
                    "Remove any sections that does not have any information."
                )

            if not is_complete:
                system_message['content'] += (
                    "\n\nNote: This is a partial conversation. Mark sections that may be incomplete "
                    "with '[Incomplete]' at the end of the section."
                )

            messages = [system_message]

            if previous_note:
                messages.append({
                    'role': 'assistant',
                    'content': previous_note
                })

            messages.append({
                'role': 'user',
                'content': f"{'Update the note with this additional conversation: ' if previous_note else ''}{transcript}"
            })

            response = ollama.chat(
                model=model,
                messages=messages
            )
            
            note_content = response['message']['content']
            
            # Remove reasoning tokens for deepseek models
            if "deepseek" in model and "</think>" in note_content:
                note_content = note_content.split("</think>", 1)[1].strip()
                
            return note_content
        except Exception as e:
            raise Exception(f"Note generation failed: {str(e)}")

    @staticmethod
    def split_transcript(transcript: str, max_words: int = 600) -> List[str]:
        """Split transcript into chunks of maximum word length."""
        words = transcript.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        return chunks

    @staticmethod
    def generate_note_from_transcript(transcript: str, model: str = 'deepseek-r1:1.5b') -> str:
        """Generate a complete SOAP note from a transcript, handling splitting and incremental updates.
        
        Args:
            transcript: The complete transcript text
            model: The model to use for generation (default: 'deepseek-r1:1.5b')
            
        Returns:
            str: The complete SOAP note
            
        Raises:
            Exception: If note generation fails
        """
        try:
            # Split transcript into chunks
            transcript_chunks = NoteGenerationService.split_transcript(transcript)
            
            current_soap_note = None
            
            # Process each chunk sequentially
            for i, chunk in enumerate(transcript_chunks):
                is_last_chunk = i == len(transcript_chunks) - 1
                
                # Generate or update SOAP note
                current_soap_note = NoteGenerationService.generate_note(
                    transcript=chunk,
                    model=model,
                    previous_note=current_soap_note,
                    is_complete=is_last_chunk
                )
            
            return current_soap_note
            
        except Exception as e:
            raise Exception(f"Failed to generate note from transcript: {str(e)}")