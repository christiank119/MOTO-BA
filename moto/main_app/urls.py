from django.urls import path
from django.views.generic import RedirectView
from . import views



urlpatterns = [
    # View paths:
    path('master_web/', views.master_web, name='master_web'),
    path('csv_import/', views.csv_import, name='csv_import'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('superuser/', views.superuser, name='superuser'),
    path('set_new_pw/', views.set_new_pw, name='set_new_pw'),
    path('reset_pw_confirmation/', views.reset_pw_confirmation, name='reset_pw_confirmation'),
    path('pupil/<int:pupil>', views.pupil, name='pupil'),
    path('ogs_group/', views.ogs_group, name='ogs_group'),
    path('select_room/', views.select_room, name='select_room'),
    path('room_selection/<str:raum>', views.room_selection, name='room_selection'),
    path('room_information/<str:raum>', views.room_information, name='room_information'),
    path('preferences/', views.preferences, name='preferences'),
    path('room_usage_history/<str:raum>', views.room_usage_history, name='room_usage_history'),
    path('room_history/<int:pupil>', views.room_history, name='room_history'),
    path('feedback_history/<int:pupil>', views.feedback_history, name='feedback_history'),
    path('search_pupil/', views.search_pupil, name='search_pupil'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('food_history/<int:pupil>', views.food_history, name='food_history'),
    path('representation/', views.representation, name='representation'),
    path('choose_data/', views.choose_data_view, name='choose_data'),
    path('choose_data/student/', views.select_student_change_view, name='choose_data_student'),
    path('choose_data/room/', views.select_room_change, name='choose_data_room'),
    path('choose_data/pa/', views.select_pa_change, name='choose_data_pa'),
    path('choose_data/group/', views.select_group_change, name='choose_data_group'),
    path('choose_data/student/<int:id>', views.change_student, name='change_student_data'),
    path('choose_data/room/<int:id>', views.change_room, name='change_room_data'),
    path('choose_data/group/<int:id>', views.change_group, name='change_group_data'),
    path('choose_data/pa/<int:id>', views.change_student, name='change_pa_data'),
]

main_url_web = 'master_web'

urls_apis = [

    'api_test',

]