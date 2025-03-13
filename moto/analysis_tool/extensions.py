from django.urls import reverse
from main_app.registry import register_extension, register_template_extension
from django.utils.safestring import mark_safe

# Add a navigation button
@register_extension('pupil_navigation_buttons')
def add_analysis_button(context):
    """Add analysis button to pupil navigation."""
    try:
        pupil_id = context.get('nutzer').id
        url = reverse('student_analysis', args=[pupil_id])
        #url = reverse('heatmap_show')
        button_html = f'<button class="historybutton" onclick="location.href=\'{url}\';"> Detailanalyse </button>'
        return mark_safe(button_html)
    except (AttributeError, KeyError):
        return ''
