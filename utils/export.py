import plotly.io as pio
import plotly.graph_objects as go
import pypdf
import io
import copy


def fig_to_pdf_bytes(fig, width=3508, height=2480, scale=2):
    """Einzelnen Plotly-Graph als PDF exportieren – A4 Querformat, druckoptimiert."""

    # Kopie erstellen damit der angezeigte Graph unverändert bleibt
    fig_export = copy.deepcopy(fig)

    fig_export.update_layout(
        font=dict(size=18, color="black"),
        title_font=dict(size=24),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=100, r=100, t=120, b=100),
        legend=dict(font=dict(size=16, color="black")),
        xaxis=dict(
            title_font=dict(size=20, color="black"),
            tickfont=dict(size=14, color="black"),
            linecolor="black",
            gridcolor="lightgrey"
        ),
        yaxis=dict(
            title_font=dict(size=20, color="black"),
            tickfont=dict(size=14, color="black"),
            linecolor="black",
            gridcolor="lightgrey"
        ),
    )

    return pio.to_image(fig_export, format="pdf", width=width, height=height, scale=scale)


def figs_to_pdf_bytes(figures: list, width=3508, height=2480, scale=2):
    """Mehrere Plotly-Graphen in ein einziges PDF zusammenführen."""
    writer = pypdf.PdfWriter()

    for fig in figures:
        img_bytes = fig_to_pdf_bytes(fig, width=width, height=height, scale=scale)
        reader = pypdf.PdfReader(io.BytesIO(img_bytes))
        writer.add_page(reader.pages[0])

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()