import plotly.io as pio
import pypdf
import io


def fig_to_pdf_bytes(fig, width=2480, height=3508, scale=3):
    """Einzelnen Plotly-Graph als PDF-Bytes exportieren."""
    return pio.to_image(fig, format="pdf", width=width, height=height, scale=scale)


def figs_to_pdf_bytes(figures: list, width=2480, height=3508, scale=3):
    """Mehrere Plotly-Graphen in ein einziges PDF zusammenführen."""
    writer = pypdf.PdfWriter()

    for fig in figures:
        img_bytes = pio.to_image(fig, format="pdf", width=width, height=height, scale=scale)
        reader = pypdf.PdfReader(io.BytesIO(img_bytes))
        writer.add_page(reader.pages[0])

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()