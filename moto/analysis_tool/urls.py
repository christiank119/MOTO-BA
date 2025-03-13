from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test, name='test'),
    path('heatmap/edit/', views.raumplan_edit, name='heatmap_edit'),
    path('heatmap/save/', views.save_polygon, name='heatmap_save'),
    path('heatmap/upload/', views.upload_raumplan, name='heatmap_upload'),
    path('heatmap/get_room_data/', views.get_room_data, name='heatmap_get_room_data'),
    path('heatmap/show/', views.raumplan_show, name='heatmap_show'),
    path('student/<int:pupil_id>/', views.student_analysis_view, name='student_analysis'),
]