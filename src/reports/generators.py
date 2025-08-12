"""
Report generators for the AI-Powered Enterprise Workflow Agent.

This module provides various report generators for different output formats
including PDF, HTML, and JSON with visual analytics and charts.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.offline import plot
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    plt = sns = go = px = plot = None

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from jinja2 import Template
from src.utils.logger import get_logger

logger = get_logger("report_generators")

class BaseReportGenerator:
    """Base class for report generators."""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate(self, report_data: Dict[str, Any], filename: str) -> str:
        """Generate report and return file path."""
        raise NotImplementedError("Subclasses must implement generate method")

class JSONReportGenerator(BaseReportGenerator):
    """JSON report generator."""
    
    def generate(self, report_data: Dict[str, Any], filename: str) -> str:
        """Generate JSON report."""
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = self.output_dir / filename
        
        # Add metadata
        report_data['metadata'] = {
            'generated_at': datetime.utcnow().isoformat(),
            'format': 'json',
            'generator': 'JSONReportGenerator'
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"JSON report generated: {file_path}")
        return str(file_path)

class HTMLReportGenerator(BaseReportGenerator):
    """HTML report generator with charts."""
    
    def __init__(self, output_dir: str = "./reports"):
        super().__init__(output_dir)
        self.template = self._create_html_template()
    
    def generate(self, report_data: Dict[str, Any], filename: str) -> str:
        """Generate HTML report with embedded charts."""
        if not filename.endswith('.html'):
            filename += '.html'
        
        file_path = self.output_dir / filename
        
        # Generate charts if plotting is available
        charts_html = ""
        if PLOTTING_AVAILABLE:
            charts_html = self._generate_charts(report_data)
        
        # Prepare template data
        template_data = {
            'title': report_data.get('title', 'Workflow Report'),
            'executive_summary': report_data.get('executive_summary', ''),
            'key_metrics': report_data.get('key_metrics', {}),
            'insights': report_data.get('insights', []),
            'recommendations': report_data.get('recommendations', []),
            'trends': report_data.get('trends', []),
            'risk_areas': report_data.get('risk_areas', []),
            'performance_highlights': report_data.get('performance_highlights', []),
            'charts': charts_html,
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'metadata': report_data.get('metadata', {})
        }
        
        # Render template
        html_content = self.template.render(**template_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {file_path}")
        return str(file_path)
    
    def _generate_charts(self, report_data: Dict[str, Any]) -> str:
        """Generate charts for the report."""
        charts_html = ""
        
        try:
            # Extract metrics for charting
            key_metrics = report_data.get('key_metrics', {})
            
            # Generate status distribution chart
            if 'status_distribution' in key_metrics:
                status_chart = self._create_pie_chart(
                    key_metrics['status_distribution'],
                    'Task Status Distribution'
                )
                charts_html += f'<div class="chart">{status_chart}</div>'
            
            # Generate category distribution chart
            if 'category_distribution' in key_metrics:
                category_chart = self._create_bar_chart(
                    key_metrics['category_distribution'],
                    'Tasks by Category'
                )
                charts_html += f'<div class="chart">{category_chart}</div>'
            
            # Generate priority distribution chart
            if 'priority_distribution' in key_metrics:
                priority_chart = self._create_pie_chart(
                    key_metrics['priority_distribution'],
                    'Task Priority Distribution'
                )
                charts_html += f'<div class="chart">{priority_chart}</div>'
            
        except Exception as e:
            logger.warning(f"Failed to generate charts: {e}")
            charts_html = '<p>Charts could not be generated.</p>'
        
        return charts_html
    
    def _create_pie_chart(self, data: Dict[str, Any], title: str) -> str:
        """Create a pie chart using Plotly."""
        if not PLOTTING_AVAILABLE:
            return f"<p>Chart: {title} (Plotting not available)</p>"
        
        try:
            labels = list(data.keys())
            values = list(data.values())
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.update_layout(title=title, showlegend=True)
            
            return plot(fig, output_type='div', include_plotlyjs=True)
        except Exception as e:
            logger.warning(f"Failed to create pie chart: {e}")
            return f"<p>Chart: {title} (Generation failed)</p>"
    
    def _create_bar_chart(self, data: Dict[str, Any], title: str) -> str:
        """Create a bar chart using Plotly."""
        if not PLOTTING_AVAILABLE:
            return f"<p>Chart: {title} (Plotting not available)</p>"
        
        try:
            x_values = list(data.keys())
            y_values = list(data.values())
            
            fig = go.Figure(data=[go.Bar(x=x_values, y=y_values)])
            fig.update_layout(title=title, xaxis_title='Category', yaxis_title='Count')
            
            return plot(fig, output_type='div', include_plotlyjs=True)
        except Exception as e:
            logger.warning(f"Failed to create bar chart: {e}")
            return f"<p>Chart: {title} (Generation failed)</p>"
    
    def _create_html_template(self) -> Template:
        """Create HTML template for reports."""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
            border-left: 4px solid #007bff;
            padding-left: 15px;
        }
        .metric {
            display: inline-block;
            background-color: #e9ecef;
            padding: 10px 15px;
            margin: 5px;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        .metric-label {
            font-weight: bold;
            color: #495057;
        }
        .metric-value {
            font-size: 1.2em;
            color: #007bff;
        }
        ul {
            list-style-type: none;
            padding-left: 0;
        }
        li {
            background-color: #f8f9fa;
            margin: 5px 0;
            padding: 10px;
            border-left: 3px solid #28a745;
            border-radius: 3px;
        }
        .risk-item {
            border-left-color: #dc3545;
        }
        .chart {
            margin: 20px 0;
            text-align: center;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9em;
        }
        .trends-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .trends-table th, .trends-table td {
            border: 1px solid #dee2e6;
            padding: 12px;
            text-align: left;
        }
        .trends-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        
        <h2>Executive Summary</h2>
        <p>{{ executive_summary }}</p>
        
        <h2>Key Metrics</h2>
        <div class="metrics-container">
            {% for key, value in key_metrics.items() %}
                {% if value is mapping %}
                    <div class="metric">
                        <div class="metric-label">{{ key.replace('_', ' ').title() }}</div>
                        <div class="metric-value">
                            {% for k, v in value.items() %}
                                {{ k }}: {{ v }}<br>
                            {% endfor %}
                        </div>
                    </div>
                {% else %}
                    <div class="metric">
                        <div class="metric-label">{{ key.replace('_', ' ').title() }}</div>
                        <div class="metric-value">{{ value }}</div>
                    </div>
                {% endif %}
            {% endfor %}
        </div>
        
        {% if charts %}
        <h2>Visual Analytics</h2>
        {{ charts|safe }}
        {% endif %}
        
        <h2>Key Insights</h2>
        <ul>
            {% for insight in insights %}
            <li>{{ insight }}</li>
            {% endfor %}
        </ul>
        
        <h2>Recommendations</h2>
        <ul>
            {% for recommendation in recommendations %}
            <li>{{ recommendation }}</li>
            {% endfor %}
        </ul>
        
        {% if trends %}
        <h2>Trends Analysis</h2>
        <table class="trends-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Direction</th>
                    <th>Significance</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {% for trend in trends %}
                <tr>
                    <td>{{ trend.metric }}</td>
                    <td>{{ trend.direction }}</td>
                    <td>{{ trend.significance }}</td>
                    <td>{{ trend.description }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        {% if risk_areas %}
        <h2>Risk Areas</h2>
        <ul>
            {% for risk in risk_areas %}
            <li class="risk-item">{{ risk }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if performance_highlights %}
        <h2>Performance Highlights</h2>
        <ul>
            {% for highlight in performance_highlights %}
            <li>{{ highlight }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        <div class="footer">
            <p>Report generated on {{ generated_at }}</p>
            <p>AI-Powered Enterprise Workflow Agent v1.0</p>
        </div>
    </div>
</body>
</html>
        """
        return Template(template_str)

class PDFReportGenerator(BaseReportGenerator):
    """PDF report generator."""
    
    def __init__(self, output_dir: str = "./reports"):
        super().__init__(output_dir)
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available. PDF generation will be limited.")
    
    def generate(self, report_data: Dict[str, Any], filename: str) -> str:
        """Generate PDF report."""
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        file_path = self.output_dir / filename
        
        if not REPORTLAB_AVAILABLE:
            # Fallback to text file
            text_file = str(file_path).replace('.pdf', '.txt')
            self._generate_text_report(report_data, text_file)
            return text_file
        
        try:
            doc = SimpleDocTemplate(str(file_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue
            )
            story.append(Paragraph(report_data.get('title', 'Workflow Report'), title_style))
            story.append(Spacer(1, 12))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            story.append(Paragraph(report_data.get('executive_summary', ''), styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Key Metrics
            story.append(Paragraph("Key Metrics", styles['Heading2']))
            metrics_data = []
            for key, value in report_data.get('key_metrics', {}).items():
                if isinstance(value, dict):
                    value_str = ', '.join([f"{k}: {v}" for k, v in value.items()])
                else:
                    value_str = str(value)
                metrics_data.append([key.replace('_', ' ').title(), value_str])
            
            if metrics_data:
                metrics_table = Table(metrics_data)
                metrics_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(metrics_table)
                story.append(Spacer(1, 12))
            
            # Insights
            insights = report_data.get('insights', [])
            if insights:
                story.append(Paragraph("Key Insights", styles['Heading2']))
                for insight in insights:
                    story.append(Paragraph(f"• {insight}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Recommendations
            recommendations = report_data.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("Recommendations", styles['Heading2']))
                for recommendation in recommendations:
                    story.append(Paragraph(f"• {recommendation}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Risk Areas
            risk_areas = report_data.get('risk_areas', [])
            if risk_areas:
                story.append(Paragraph("Risk Areas", styles['Heading2']))
                for risk in risk_areas:
                    story.append(Paragraph(f"• {risk}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Performance Highlights
            highlights = report_data.get('performance_highlights', [])
            if highlights:
                story.append(Paragraph("Performance Highlights", styles['Heading2']))
                for highlight in highlights:
                    story.append(Paragraph(f"• {highlight}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = f"Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(footer_text, styles['Normal']))
            
            doc.build(story)
            logger.info(f"PDF report generated: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            # Fallback to text file
            text_file = str(file_path).replace('.pdf', '.txt')
            self._generate_text_report(report_data, text_file)
            return text_file
    
    def _generate_text_report(self, report_data: Dict[str, Any], file_path: str):
        """Generate a simple text report as fallback."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{report_data.get('title', 'Workflow Report')}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Executive Summary:\n")
            f.write(f"{report_data.get('executive_summary', '')}\n\n")
            
            f.write("Key Metrics:\n")
            for key, value in report_data.get('key_metrics', {}).items():
                f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
            f.write("\n")
            
            insights = report_data.get('insights', [])
            if insights:
                f.write("Key Insights:\n")
                for insight in insights:
                    f.write(f"  • {insight}\n")
                f.write("\n")
            
            recommendations = report_data.get('recommendations', [])
            if recommendations:
                f.write("Recommendations:\n")
                for recommendation in recommendations:
                    f.write(f"  • {recommendation}\n")
                f.write("\n")
            
            f.write(f"\nReport generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info(f"Text report generated: {file_path}")

class ReportGeneratorFactory:
    """Factory for creating report generators."""
    
    @staticmethod
    def create_generator(format_type: str, output_dir: str = "./reports") -> BaseReportGenerator:
        """Create a report generator for the specified format."""
        format_type = format_type.lower()
        
        if format_type == 'json':
            return JSONReportGenerator(output_dir)
        elif format_type == 'html':
            return HTMLReportGenerator(output_dir)
        elif format_type == 'pdf':
            return PDFReportGenerator(output_dir)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported report formats."""
        return ['json', 'html', 'pdf']
