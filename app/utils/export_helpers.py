import csv
import io
from flask import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_csv(results, branch=None, semester=None):
    """Generate CSV from results list."""
    output = io.StringIO()
    writer = csv.writer(output)

    # 🔹 Write headers
    writer.writerow(['Name', 'Roll Number', 'Branch', 'Semester', 'Votes'])

    # 🔹 Write data rows
    for r in results:
        user = r['nominee']
        writer.writerow([
            user.name,
            user.roll_no,
            user.branch,
            user.semester,
            r['votes']
        ])

    output.seek(0)
    filename = f"CR_Voting_Results_{branch or 'All'}_{semester or 'All'}.csv".replace(" ", "_")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

def generate_pdf(results, branch=None, semester=None):
    """Generate PDF from results list."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # 🔹 Title
    title = f"CR Voting Results - Branch: {branch or 'All'}, Semester: {semester or 'All'}"
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, height - 40, title)

    # 🔹 Column headers
    p.setFont("Helvetica-Bold", 11)
    y = height - 70
    p.drawString(40, y, "Name")
    p.drawString(160, y, "Roll No")
    p.drawString(250, y, "Branch")
    p.drawString(330, y, "Semester")
    p.drawString(420, y, "Votes")
    y -= 20

    # 🔹 Candidate rows
    p.setFont("Helvetica", 10)
    for r in results:
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 40

            # Repeat headers on new page
            p.setFont("Helvetica-Bold", 11)
            p.drawString(40, y, "Name")
            p.drawString(160, y, "Roll No")
            p.drawString(250, y, "Branch")
            p.drawString(330, y, "Semester")
            p.drawString(420, y, "Votes")
            y -= 20
            p.setFont("Helvetica", 10)

        user = r['nominee']
        p.drawString(40, y, user.name)
        p.drawString(160, y, user.roll_no)
        p.drawString(250, y, user.branch)
        p.drawString(330, y, str(user.semester))
        p.drawString(420, y, str(r['votes']))
        y -= 20

    p.save()
    buffer.seek(0)
    filename = f"CR_Voting_Results_{branch or 'All'}_{semester or 'All'}.pdf".replace(" ", "_")
    return Response(
        buffer,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
