
from django.urls import path
from . import views


urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/privacy/', views.update_privacy_settings, name='update_privacy'),
    
    # Chat List & Search
    path('chats/', views.chat_list_view, name='chat_list'),
    path('chats/search/', views.search_chats, name='search_chats'),
    path('contacts/search/', views.search_contacts, name='search_contacts'),
    
    # Chat Management
    path('chats/<uuid:chat_id>/', views.chat_detail_view, name='chat_detail'),
    path('chats/create/personal/', views.create_personal_chat, name='create_personal_chat'),
    path('chats/create/group/', views.create_group_chat, name='create_group_chat'),
    path('chats/<uuid:chat_id>/pin/', views.pin_chat, name='pin_chat'),
    path('chats/<uuid:chat_id>/mute/', views.mute_chat, name='mute_chat'),
    path('chats/<uuid:chat_id>/archive/', views.archive_chat, name='archive_chat'),
    path('chats/<uuid:chat_id>/leave/', views.leave_group, name='leave_group'),
    
    # Messages
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/<uuid:chat_id>/get/', views.get_messages, name='get_messages'),
    path('messages/<uuid:message_id>/delete/', views.delete_message, name='delete_message'),
    path('messages/<uuid:message_id>/react/', views.react_to_message, name='react_to_message'),
    path('messages/<uuid:message_id>/star/', views.star_message, name='star_message'),
    
    # Status
    path('status/', views.status_list_view, name='status_list'),
    path('status/create/', views.create_status, name='create_status'),
    path('status/<uuid:status_id>/', views.view_status, name='view_status'),
    path('status/<uuid:status_id>/delete/', views.delete_status, name='delete_status'),
    
    # Calls
    path('calls/', views.calls_view, name='calls'),
    path('calls/initiate/', views.initiate_call, name='initiate_call'),
    path('calls/<uuid:call_id>/update/', views.update_call_status, name='update_call_status'),
    
    # Contacts
    path('contacts/', views.contacts_view, name='contacts'),
    path('contacts/add/', views.add_contact, name='add_contact'),
    path('contacts/<int:user_id>/block/', views.block_user, name='block_user'),
    
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]