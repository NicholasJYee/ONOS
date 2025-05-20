import ollama
from typing import List, Optional
from pathlib import Path

class NoteGenerationService:
    # Class variables for system messages and instructions
    SYSTEM_MESSAGE = {
        'role': 'system',
        'content': (
            "You are a medical scribe assistant. "
            "Convert the following doctor-patient conversation into a structured medical "
            "note following the clinical note format. Only include sections where relevant information "
            "is explicitly mentioned in the conversation. Each section should only appear if "
            "there is specific information for it.\n"
            "If it is a follow-up appointment, you should include fewer sections and focus on updates "
            "since their last visit and does not need to include medication history, family history, "
            "social history, or review of systems.\n\n"
            "Available sections and their components:\n\n"
            "- Patient information (Name, Age, Gender, Address, Contact information)\n"
            "- Chief complaint (CC) or duration of follow-up\n"
            "- History of Present Illness (HPI)\n"
            "- Review of Systems (ROS) relevant to the complaint\n"
            "- Past Medical History (PMHx)\n"
            "- Current medications and allergies\n"
            "- Family and Social history\n\n"
            "OBJECTIVE - Include only if physical findings/measurements are mentioned:\n"
            "- Vital signs\n"
            "- Physical examination findings\n"
            "- Laboratory or imaging results\n"
            "- Observable measurements or data\n\n"
            "ASSESSMENT - Include only if diagnoses/interpretations are discussed:\n"
            "- Primary diagnosis or differential diagnoses\n"
            "- Clinical reasoning and interpretation\n"
            "- Status of conditions\n\n"
            "PLAN - Include only if future actions are specified:\n"
            "- Ordered tests or procedures\n"
            "- Prescribed medications or treatments\n"
            "- Referrals or consultations\n"
            "- Follow-up instructions\n"
            "- Patient education\n\n"
            "Important:\n"
            "- Only include sections that have explicit information from the conversation\n"
            "- Omit any section entirely if no relevant information was discussed\n"
            "- Do not include placeholder text or assumptions\n"
            "- Do not include any pre-amble or commentary\n"
            "- Do not write your explanation for the note, only the note\n"
            "- Do not include any other text, only the note\n"
            "- Only include the note, no other text\n"
            "- You may use markdown formatting, but do not include any other text, only the note\n"
        )
    }

    CLEANING_INSTRUCTIONS = (
        "Please clean the following medical note by:\n"
        "1. Removing any incomplete sections\n"
        "2. Removing any preamble or commentary before 'Patient information'\n"
        "3. Ensuring the note starts with 'Patient information'\n"
        "4. Maintaining the clinical note format structure\n"
        "5. Only including sections with actual content\n"
        "6. Do not include any other text, only the note\n"
        "7. Do not write your explanation for the note or tell me that you are doing it, only give me the note\n"
        "If the note doesn't start with 'Patient information' or contains incomplete sections, "
        "please regenerate it following these requirements."
    )

    @staticmethod
    def generate_note(transcript: str, model: str, previous_note: str = None, is_complete: bool = True) -> str:
        """Generate a SOAP note from a medical transcript.
        
        Args:
            transcript: The medical conversation transcript
            model: The LLM model to use
            previous_note: Optional previous SOAP note to update
            is_complete: Whether this is a complete transcript (default: True)
        """
        try:
            system_message = NoteGenerationService.SYSTEM_MESSAGE.copy()

            if previous_note:
                system_message['content'] += (
                    "\n\nUpdate the existing clinical note with new information from the conversation. "
                    "Maintain the existing structure while adding or modifying relevant details. "
                    "Ensure consistency between old and new information. "
                    "Remove any sections that does not have any information."
                    "Do not include any other text, only the note"
                )

            if not is_complete:
                system_message['content'] += (
                    "\n\nNote: This is a partial conversation and the note will be updated with the new information afterwards."
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
    def clean_note(cleaned_note: str, model: str) -> str:
        """Clean a generated note by removing incomplete sections and ensuring proper format.
        
        Args:
            cleaned_note: The note to clean
            model: The LLM model to use for cleaning
            
        Returns:
            str: The cleaned note
        """
        
        # Remove reasoning tokens for deepseek models
        if "</think>" in cleaned_note:
            cleaned_note = cleaned_note.split("</think>", 1)[1].strip()
        
        # Strip formatting from the start of the note
        cleaned_note = cleaned_note.strip()
        if cleaned_note.startswith('```plaintext'):
            cleaned_note = cleaned_note[12:].strip()
        elif cleaned_note.startswith('```'):
            cleaned_note = cleaned_note[3:].strip()
        
        patient_info_index = cleaned_note.lower().find("patient information")
        if patient_info_index > 0:
            next_chars = cleaned_note[patient_info_index + len("patient information"):patient_info_index + len("patient information") + 4]
            if '**' in next_chars:
                cleaned_note = '**' + cleaned_note[patient_info_index:]
            else:
                cleaned_note = cleaned_note[patient_info_index:]
        
        # Check for issues and provide specific feedback
        issues = []
        
        # Normalize the start of the note for comparison
        normalized_start = cleaned_note.strip().lower()
        normalized_start = normalized_start.replace('*', '').replace('#', '').replace('**', '').replace('_', '')
        
        if not normalized_start.startswith("patient information"):
            issues.append(f"The note starts with '{cleaned_note[:50]}...' instead of 'Patient information'")
        
        if "[Incomplete]" in cleaned_note:
            incomplete_sections = [line for line in cleaned_note.split('\n') if "[Incomplete]" in line]
            issues.append(f"The following sections includes [Incomplete]. It should be removed: {', '.join(incomplete_sections)}")
        
        if issues:
            print(f"Found issues in note: {'; '.join(issues)}")
            feedback_message = (
                f"Please fix the following issues in the note:\n"
                f"{'; '.join(issues)}\n\n"
                f"Here is the current note:\n{cleaned_note}"
            )
            messages = [
                {'role': 'system', 'content': NoteGenerationService.CLEANING_INSTRUCTIONS},
                {'role': 'user', 'content': feedback_message}
            ]
            
            response = ollama.chat(
                model=model,
                messages=messages
            )
            
            cleaned_note = response['message']['content']
            
            # Remove reasoning tokens for deepseek models
            if "deepseek" in model and "</think>" in cleaned_note:
                cleaned_note = cleaned_note.split("</think>", 1)[1].strip()
            
            # Recursively check again
            return NoteGenerationService.clean_note(cleaned_note, model)
        
        return cleaned_note

    @staticmethod
    def generate_note_from_transcript(transcript: str, model: str) -> str:
        """Generate a complete SOAP note from a transcript, handling splitting and incremental updates.
        
        Args:
            transcript: The complete transcript text
            model: The model to use for generation
            
        Returns:
            str: The complete SOAP note
            
        Raises:
            Exception: If note generation fails
        """
        try:
            print(f"Generating note with model: {model}")

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
            
            return NoteGenerationService.clean_note(current_soap_note, model)
            
        except Exception as e:
            raise Exception(f"Failed to generate note from transcript: {str(e)}")