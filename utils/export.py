import plotly.io as pio
import pypdf
import io
import copy


def fig_to_pdf_bytes(fig, width=3508, height=2480, scale=2):
    """Einzelnen Plotly-Graph als hochauflösendes PNG exportieren – druckoptimiert."""

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

    # Preislinie auf Blau setzen damit sie auf weißem Hintergrund sichtbar ist
    for trace in fig_export.data:
        if trace.name == "Price":
            trace.line.color = "#1f77b4"
            trace.line.width = 2.5

    return pio.to_image(fig_export, format="png", width=width, height=height, scale=2)


def figs_to_pdf_bytes(figures: list, width=3508, height=2480, scale=2):
    """Mehrere Plotly-Graphen in ein einziges PNG zusammenführen."""
    writer = pypdf.PdfWriter()

    for fig in figures:
        img_bytes = fig_to_pdf_bytes(fig, width=width, height=height, scale=scale)
        reader = pypdf.PdfReader(io.BytesIO(img_bytes))
        writer.add_page(reader.pages[0])

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()