import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
import markdown
import re
import pandas as pd

def process_markdown(text: str) -> str:
    """Convert markdown text to HTML for reportlab."""
    # Convert markdown to HTML
    html = markdown.markdown(text)
    # Replace some HTML tags with reportlab-compatible tags
    html = html.replace('<strong>', '<br/><b>').replace('</strong>', '</b><br/>')
    html = html.replace('<em>', '<i>').replace('</em>', '</i>')
    return html

def get_transcription_and_notes(transcription_path: Path, notes_dir: Path) -> tuple[str, list[tuple[str, str]]]:
    """Get transcription and corresponding SOAP notes for a given transcription file."""
    # Read transcription
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription = f.read()
    
    # Define the expected order of models
    model_order = [
        "llama3.2:3b",
        "gemma3:4b",
        "qwen2.5:3b",
        "deepseek-r1:1.5b"
    ]
    
    # Load evaluation scores if available
    scores_dict = {}
    try:
        df = pd.read_csv('evaluations/soap_note_evaluations.csv')
        for _, row in df.iterrows():
            model_key = f"{row['model_used']}:{row['model_size']}"
            scores_dict[model_key] = {
                'completeness': row['completeness'],
                'conciseness': row['conciseness'],
                'hallucination': 'Yes' if row['hallucination'] == 1 else 'No'
            }
    except:
        print("Warning: Could not load evaluation scores")
    
    # Get base filename without extension
    base_name = transcription_path.stem
    
    # Find corresponding SOAP notes and store in a dictionary
    notes_dict = {}
    for note_file in notes_dir.rglob(f"{base_name}_*.txt"):
        # Extract model info from filename
        model_info = note_file.stem.split('_')
        model_name = f"{model_info[2]}:{model_info[3]}"  # Reconstruct full model name
        
        with open(note_file, 'r', encoding='utf-8') as f:
            note_content = f.read()
            note_content = process_markdown(note_content)
            
            # Create model header with scores on separate lines
            display_name = f"{model_info[2]} ({model_info[3]})"
            if model_name in scores_dict:
                scores = scores_dict[model_name]
                header = (f"{display_name}<br/>"
                         f"Completeness: {scores['completeness']}, "
                         f"Conciseness: {scores['conciseness']}, "
                         f"Hallucination: {scores['hallucination']}<br/>"
                         f"{'_' * 40}<br/><br/>")  # Add visible line separator
            else:
                header = f"{display_name}<br/>{'_' * 40}<br/><br/>"
                
            notes_dict[model_name] = (header, note_content)
    
    # Create ordered list of notes based on model_order
    soap_notes = []
    for model in model_order:
        if model in notes_dict:
            soap_notes.append(notes_dict[model])
    
    return transcription, soap_notes

def create_pdf(output_path: str, transcription: str, soap_notes: list[tuple[str, str]]):
    """Create a two-page PDF with dynamic font sizing and overflow handling."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=18,    # Reduced margins
        leftMargin=18,
        topMargin=18,
        bottomMargin=18
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        spaceAfter=6     # Reduced spacing
    )
    
    # Try different font sizes until content fits
    font_sizes = [8, 7, 6, 5, 4, 3]  # Added smaller sizes
    success = False
    
    for font_size in font_sizes:
        try:
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=font_size,
                leading=font_size + 1,  # Reduced leading
                alignment=TA_LEFT,
                wordWrap='LTR'        # Ensure word wrapping
            )
            
            story = []
            
            # First Page: Transcription
            story.append(Paragraph("Medical Interview Transcription", title_style))
            story.append(Paragraph(transcription, normal_style))
            story.append(PageBreak())
            
            # Second Page: SOAP Notes Grid
            story.append(Paragraph("SOAP Notes", title_style))
            
            # Prepare SOAP notes for 2x2 grid
            grid_data = []
            row = []
            for i, (model, note) in enumerate(soap_notes):
                cell_content = Paragraph(
                    f"<br/><b>{model}</b><br/><br/>{note}",  # Added line break before model name
                    normal_style
                )
                row.append(cell_content)
                
                if (i + 1) % 2 == 0:
                    grid_data.append(row)
                    row = []
            
            # Handle any remaining notes
            if row:
                while len(row) < 2:
                    row.append(Paragraph("", normal_style))
                grid_data.append(row)
            
            # Create table with equal column widths
            col_width = (doc.width - doc.leftMargin - doc.rightMargin) / 2
            table = Table(grid_data, colWidths=[col_width, col_width])
            
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),  # Reduced padding
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ]))
            
            story.append(table)
            
            # Try to build PDF
            doc.build(story)
            success = True
            break
            
        except:
            continue
    
    if not success:
        print(f"Warning: Content may be truncated in {output_path}")

def main():
    # Setup paths
    interviews_path = Path("interviews/data")
    notes_path = Path("notes/data")
    output_base_path = Path("evaluations/pdf")
    
    # Process each transcription file
    for transcription_file in interviews_path.rglob("*.txt"):
        print(f"Processing {transcription_file}")
        
        # Get the pathology and visit type from the directory structure
        pathology = transcription_file.parent.name
        visit_type = transcription_file.parent.parent.name
        
        # Create output directory structure mirroring the input
        output_dir = output_base_path / visit_type / pathology
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get transcription and corresponding notes
        transcription, soap_notes = get_transcription_and_notes(transcription_file, notes_path)
        
        # Create output filename in the appropriate directory
        output_file = output_dir / f"{transcription_file.stem}_visualization.pdf"
        
        # Create PDF
        create_pdf(str(output_file), transcription, soap_notes)
        print(f"Created PDF: {output_file}")

if __name__ == "__main__":
    main()
