from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import json
from datetime import datetime

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    spaceAfter=30,
    alignment=TA_CENTER,
    textColor=colors.darkblue
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    spaceAfter=12,
    spaceBefore=20,
    textColor=colors.darkblue
)

question_style = ParagraphStyle(
    'Question',
    parent=styles['Normal'],
    fontSize=12,
    spaceAfter=6,
    spaceBefore=12,
    fontName='Helvetica-Bold',
    textColor=colors.black
)

answer_style = ParagraphStyle(
    'Answer',
    parent=styles['Normal'],
    fontSize=11,
    spaceAfter=12,
    spaceBefore=6,
    leftIndent=20,
    textColor=colors.black
)

metrics_style = ParagraphStyle(
    'Metrics',
    parent=styles['Normal'],
    fontSize=10,
    spaceAfter=6,
    textColor=colors.darkgray
)

def build_pdf_report(session_data, filename):
    """Build PDF report content"""
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("AI Interview Coach - Performance Report", title_style))
        story.append(Spacer(1, 20))
        
        # Session Info
        session_info = [
            ['Session Title:', str(session_data.get('session_title', 'Interview Session'))],
            ['Session Mode:', str(session_data.get('session_mode', 'topic')).replace('_', ' ').title()],
            ['Topic:', str(session_data.get('topic', 'N/A'))],
            ['Session ID:', str(session_data.get('session_id', 'N/A'))],
            ['Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Final Score:', f"{session_data.get('final_score', 0)}/100"]
        ]
        
        session_table = Table(session_info, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ]))
        
        story.append(session_table)
        story.append(Spacer(1, 30))
        
        # Questions and Answers
        questions = session_data.get('questions', [])
        session_mode = str(session_data.get('session_mode', 'topic'))
        
        for i, q_data in enumerate(questions, 1):
            story.append(Paragraph(f"Question {i}", heading_style))
            
            # Question
            question_text = str(q_data.get('question', 'N/A'))
            story.append(Paragraph(f"<b>Q:</b> {question_text}", question_style))
            
            # Answer with fillers highlighted
            answer_text = str(q_data.get('answer', 'N/A'))
            filler_words = q_data.get('filler_words', [])
            
            # Handle different filler_words formats
            if isinstance(filler_words, int):
                # If filler_words is a number, convert to empty array
                filler_words = []
            elif isinstance(filler_words, str):
                # If filler_words is a string, split by commas
                filler_words = [f.strip() for f in filler_words.split(',') if f.strip()]
            elif not isinstance(filler_words, list):
                # If filler_words is not a list, convert to empty array
                filler_words = []
            
            # Highlight fillers in answer
            highlighted_answer = answer_text
            if filler_words:
                for filler in filler_words:
                    if filler and isinstance(filler, str):  # Ensure filler is not empty and is string
                        highlighted_answer = highlighted_answer.replace(
                            filler, f"<font color='red'><b>[{filler}]</b></font>"
                        )
            
            story.append(Paragraph(f"<b>A:</b> {highlighted_answer}", answer_style))
            
            # Metrics
            filler_count = len(filler_words) if isinstance(filler_words, list) else 0
            filler_display = ', '.join(str(f) for f in filler_words) if isinstance(filler_words, list) else str(filler_words)
            
            metrics_data = [
                ['Confidence:', f"{q_data.get('confidence', 0)}%"],
                ['Speaking Rate:', f"{q_data.get('wpm', 0)} WPM"],
                ['Duration:', f"{q_data.get('duration', 0)} seconds"],
                ['Filler Words:', f"{filler_count} ({filler_display})"]
            ]

            if session_mode == "custom":
                metrics_data.extend([
                    ['Question Weight:', str(q_data.get('weight', 0))],
                    ['Target Time:', f"{q_data.get('target_seconds', 0)} seconds"],
                    ['Timing Delta:', f"{q_data.get('time_target_delta_seconds', 0)} seconds"],
                    ['Timing Status:', str(q_data.get('time_target_status', 'not_set')).replace('_', ' ')],
                ])
            
            metrics_table = Table(metrics_data, colWidths=[1.5*inch, 2.5*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 20))
        
        # Overall Summary
        story.append(Paragraph("Overall Summary", heading_style))
        
        # Calculate averages
        if questions:
            avg_confidence = sum(q.get('confidence', 0) for q in questions) / len(questions)
            avg_wpm = sum(q.get('wpm', 0) for q in questions) / len(questions)
            total_duration = sum(q.get('duration', 0) for q in questions)
            
            # Handle filler_words properly in summary calculation
            total_fillers = 0
            for q in questions:
                filler_words = q.get('filler_words', [])
                if isinstance(filler_words, list):
                    total_fillers += len(filler_words)
                elif isinstance(filler_words, int):
                    total_fillers += filler_words
                # If it's a string or other type, ignore it
            
            summary_data = [
                ['Average Confidence:', f"{avg_confidence:.1f}%"],
                ['Average Speaking Rate:', f"{avg_wpm:.1f} WPM"],
                ['Total Speaking Time:', f"{total_duration:.1f} seconds"],
                ['Total Filler Words:', f"{total_fillers}"],
                ['Questions Answered:', f"{len(questions)}/{session_data.get('questions_total', len(questions))}"]
            ]

            if session_mode == "custom":
                time_deltas = session_data.get('time_delta_history', [])
                if not time_deltas:
                    time_deltas = [q.get('time_target_delta_seconds', 0) for q in questions if isinstance(q, dict)]
                average_delta = sum(abs(float(delta or 0)) for delta in time_deltas) / max(1, len(time_deltas))
                summary_data.append(['Average Time Delta:', f"{average_delta:.1f} seconds"])
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ]))
            
            story.append(summary_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated by AI Interview Coach", metrics_style))
        
        # Build PDF
        doc.build(story)
        return filename
        
    except Exception as e:
        print(f"Error in build_pdf_report: {e}")
        import traceback
        traceback.print_exc()
        raise e

def generate_interview_pdf(session_data, filename=None):
    """Generate PDF report for interview session"""
    try:
        # Validate session data
        if not session_data:
            print("Error: No session data provided")
            return None
            
        if not isinstance(session_data, dict):
            print(f"Error: session_data is not a dict, got {type(session_data)}")
            return None
            
        # Generate filename if not provided
        if filename is None:
            session_id = session_data.get('session_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"interview_report_{session_id}_{timestamp}.pdf"
        
        print(f"Generating PDF: {filename}")
        print(f"Session data keys: {list(session_data.keys())}")
        
        # Build PDF
        build_pdf_report(session_data, filename)
        
        # Verify file was created
        import os
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"PDF generated successfully: {filename} ({file_size} bytes)")
            return filename
        else:
            print(f"Error: PDF file was not created: {filename}")
            return None
            
    except Exception as e:
        print(f"PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        return None
