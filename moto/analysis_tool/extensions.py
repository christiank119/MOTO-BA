from django.urls import reverse
from main_app.registry import register_extension, register_template_extension

# Add a navigation button
@register_extension('pupil_navigation_buttons')
def add_analysis_button(context):
    """Add analysis button to pupil navigation."""
    pupil_id = context.get('nutzer').id
    url = reverse('student_analysis', args=[pupil_id])
    return f'<button class="historybutton" onclick="location.href=\'{url}\';"> Detailanalyse </button>'
