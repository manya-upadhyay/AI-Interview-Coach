from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf(report_text):

    file_path = "reports/interview_report.pdf"

    doc = SimpleDocTemplate(file_path)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>AI Interview Report</b>", styles["Title"]))

    story.append(Paragraph(report_text.replace("\n", "<br/>"), styles["BodyText"]))

    doc.build(story)

    return file_path