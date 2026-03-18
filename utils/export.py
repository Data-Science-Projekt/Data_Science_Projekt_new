import plotly.io as pio
import pypdf
import io
import copy


def fig_to_pdf_bytes(fig, width=2480, height=1654, scale=1):
    """Einzelnen Plotly-Graph als hochauflösendes PNG exportieren – A4 Querformat, 300 DPI."""

    fig_export = copy.deepcopy(fig)

    fig_export.update_layout(
        font=dict(size=42, color="black"),
        title_font=dict(size=56, color="black"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=180, r=80, t=120, b=180),
        legend=dict(
            font=dict(size=40, color="black"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="black",
            borderwidth=2,
            orientation="h",
            yanchor="bottom",
            y=-0.22,  # näher am Graph
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
            title_font=dict(size=48, color="black"),
            tickfont=dict(size=38, color="black"),
            linecolor="black",
            linewidth=2,
            gridcolor="#dddddd",
            title_standoff=20,
        ),
        yaxis=dict(
            title_font=dict(size=48, color="black"),
            tickfont=dict(size=38, color="black"),
            linecolor="black",
            linewidth=2,
            gridcolor="#dddddd",
            title_standoff=20,
        ),
    )

    for trace in fig_export.data:
        if trace.name == "Price":
            trace.line.color = "#1f77b4"
            trace.line.width = 4

    return pio.to_image(fig_export, format="png", width=width, height=height, scale=scale)


def figs_to_pdf_bytes(figures: list, width=2480, height=1654, scale=1):
    """Mehrere Plotly-Graphen in ein einziges PDF zusammenführen."""
    writer = pypdf.PdfWriter()

    for fig in figures:
        img_bytes = fig_to_pdf_bytes(fig, width=width, height=height, scale=scale)
        reader = pypdf.PdfReader(io.BytesIO(img_bytes))
        writer.add_page(reader.pages[0])

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()