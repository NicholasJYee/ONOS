import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
import markdown
import re

def process_markdown(text: str) -> str:
    """Convert markdown text to HTML for reportlab."""
    # Convert markdown to HTML
    html = markdown.markdown(text)
    # Replace some HTML tags with reportlab-compatible tags
    html = html.replace('<strong>', '<b>').replace('</strong>', '</b>')
    html = html.replace('<em>', '<i>').replace('</em>', '</i>')
    return html

def get_transcription_and_notes(transcription_path: Path, notes_dir: Path) -> tuple[str, list[tuple[str, str]]]:
    """Get transcription and corresponding SOAP notes for a given transcription file."""
    # Read transcription
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription = f.read()
    
    # Get base filename without extension
    base_name = transcription_path.stem
    
    # Find corresponding SOAP notes
    soap_notes = []
    for note_file in notes_dir.rglob(f"{base_name}_*.txt"):
        # Extract model info from filename
        model_info = note_file.stem.split('_')
        model_name = model_info[2]
        model_size = model_info[3]
        
        with open(note_file, 'r', encoding='utf-8') as f:
            note_content = f.read()
            # Process the note content as markdown
            note_content = process_markdown(note_content)
            soap_notes.append((f"{model_name} ({model_size})", note_content))
    
    return transcription, soap_notes

def create_pdf(output_path: str, transcription: str, soap_notes: list[tuple[str, str]]):
    """Create a portrait PDF with transcription at top and 2x2 SOAP notes grid below."""
    # Setup document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        alignment=TA_LEFT
    )
    
    # Create content
    story = []
    
    # Add transcription at the top
    story.append(Paragraph("Medical Interview Transcription", title_style))
    story.append(Paragraph(transcription, normal_style))
    story.append(Spacer(1, 20))
    
    # Create 2x2 grid for SOAP notes
    story.append(Paragraph("SOAP Notes", title_style))
    
    # Prepare SOAP notes for 2x2 grid
    grid_data = []
    row = []
    for i, (model, note) in enumerate(soap_notes):
        cell_content = Paragraph(f"<b>{model}</b><br/><br/>{note}", normal_style)
        row.append(cell_content)
        
        if (i + 1) % 2 == 0 or i == len(soap_notes) - 1:
            # Pad the row if needed
            while len(row) < 2:
                row.append(Paragraph("", normal_style))
            grid_data.append(row)
            row = []
    
    # Create table with equal column widths
    col_width = (doc.width - doc.leftMargin - doc.rightMargin) / 2
    table = Table(grid_data, colWidths=[col_width, col_width])
    
    # Style the table
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)

def main():
    # Setup paths
    interviews_path = Path("interviews/data")
    notes_path = Path("notes/data")
    output_dir = Path("evaluations/pdf")
    output_dir.mkdir(exist_ok=True)
    
    # Process each transcription file
    for transcription_file in interviews_path.rglob("*.txt"):
        print(f"Processing {transcription_file}")
        
        # Get transcription and corresponding notes
        transcription, soap_notes = get_transcription_and_notes(transcription_file, notes_path)
        
        # Create output filename
        output_file = output_dir / f"{transcription_file.stem}_visualization.pdf"
        
        # Create PDF
        create_pdf(str(output_file), transcription, soap_notes)
        print(f"Created PDF: {output_file}")

if __name__ == "__main__":
    main()
