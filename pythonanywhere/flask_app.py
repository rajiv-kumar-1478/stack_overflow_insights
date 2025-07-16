from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
CORS(app)

csv_file = "normalized_data.csv"  # Your CSV file


def get_tag_columns(df, count=None):
    """Get top `count` tag columns, excluding 'year_month'."""
    tag_columns = df.columns.drop('year_month')
    if count is not None:
        tag_columns = tag_columns[:count]
    return tag_columns

import plotly.graph_objs as go
from flask import render_template_string

@app.route('/plot_trend')
def plot_trend():
    df = pd.read_csv(csv_file)
    df["Month"] = pd.to_datetime(df["year_month"])

    tag_columns = get_tag_columns(df)

    fig = go.Figure()

    for tag in tag_columns:
        fig.add_trace(go.Scatter(
            x=df["Month"],
            y=df[tag],
            mode="lines+markers",
            name=tag,
            line=dict(width=2),
            marker=dict(size=4),
            hovertemplate='%{x|%Y-%m}<br>' + f'{tag}: ' + '%{y:.2f}%<extra></extra>'
        ))

    fig.update_layout(
        title="StackOverflow Questions Trend by Tag",
        xaxis_title="Month",
        yaxis_title="Tag in percentage",
        hovermode="x unified",
        legend_title="Tags",
        template="plotly_white",
        width=1200,
        height=600
    )

    # Render as HTML
    graph_html = fig.to_html(full_html=False)

    return render_template_string("""
    <html>
        <head><title>Trend Chart</title></head>
        <body>{{ graph_html|safe }}</body>
    </html>
    """, graph_html=graph_html)


@app.route('/trend_data')
def get_trend_data():
    df = pd.read_csv(csv_file)
    count = request.args.get("count", default=13, type=int)
    tag_columns = get_tag_columns(df, count)

    trend_data = {
        "months": df["year_month"].tolist(),
        "technologies": {
            tag: df[tag].astype(int).tolist() for tag in tag_columns
        }
    }

    return jsonify(trend_data)


@app.route('/pie_data')
def get_pie_data():
    df = pd.read_csv(csv_file)
    count = request.args.get("count", default=13, type=int)
    month = request.args.get("month", df["year_month"].iloc[-1])
    tag_columns = get_tag_columns(df, count)

    if month not in df["year_month"].values:
        return jsonify({"error": "Month not found"}), 400

    row = df[df["year_month"] == month][tag_columns].iloc[0]

    pie_data = {
        "labels": row.index.tolist(),
        "values": row.values.astype(int).tolist()
    }

    return jsonify(pie_data)


@app.route('/bar_chart_data')
def get_bar_chart_data():
    df = pd.read_csv(csv_file)
    count = request.args.get("count", default=13, type=int)
    tag_columns = get_tag_columns(df, count)

    sorted_data = {}

    for _, row in df.iterrows():
        month = row["year_month"]
        sorted_tech = sorted([(tech, row[tech]) for tech in tag_columns], key=lambda x: x[1])
        sorted_data[month] = {
            "techs": [tech for tech, _ in sorted_tech],
            "values": [value for _, value in sorted_tech]
        }

    bar_chart_data = {
        "months": df["year_month"].tolist(),
        "technologies": {tech: [] for tech in tag_columns}
    }

    for month in df["year_month"]:
        for tech, value in zip(sorted_data[month]["techs"], sorted_data[month]["values"]):
            bar_chart_data["technologies"][tech].append(value)

    return jsonify(bar_chart_data)


@app.route('/top_tags')
def get_top_tags():
    df = pd.read_csv(csv_file)
    count = request.args.get("count", default=30, type=int)
    tag_totals = df.drop(columns=['year_month']).sum().sort_values(ascending=False)
    top_tags = tag_totals.head(count)

    bar_data = {
        "labels": top_tags.index.tolist(),
        "values": top_tags.values.astype(int).tolist()
    }

    return jsonify(bar_data)


# ✅ This is the key line for WSGI
application = app

# For local development
if __name__ == '__main__':
    app.run(debug=True)
