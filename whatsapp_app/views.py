"""
WhatsApp Clone Views
Path: views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Max, Count, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
from datetime import timedelta
import json

from .models import (
    User, Contact, Chat, ChatParticipant, Message, MessageReceipt,
    MessageReaction, Status, StatusView, Call, GroupCall, GroupCallParticipant,
    BlockedUser, ArchivedChat, Notification, MediaGallery, DeletedMessage
)


# ==================== Authentication Views ====================

def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('chat_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validation
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        if User.objects.filter(phone_number=phone_number).exists():
            return JsonResponse({'error': 'Phone number already registered'}, status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            phone_number=phone_number,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        login(request, user)
        return JsonResponse({'success': True, 'redirect': '/chats/'})
    
    return render(request, 'register.html')


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('chat_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Update online status
            user.is_online = True
            user.save(update_fields=['is_online'])
            return JsonResponse({'success': True, 'redirect': '/chats/'})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    """User logout"""
    request.user.is_online = False
    request.user.save(update_fields=['is_online'])
    logout(request)
    return redirect('login')


# ==================== Profile Views ====================

@login_required
def profile_view(request):
    """View and edit user profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.about = request.POST.get('about', user.about)
        
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        return JsonResponse({'success': True, 'message': 'Profile updated'})
    
    return render(request, 'profile.html')


@login_required
def update_privacy_settings(request):
    """Update privacy settings via AJAX"""
    if request.method == 'POST':
        user = request.user
        data = json.loads(request.body)
        
        user.last_seen_privacy = data.get('last_seen_privacy', user.last_seen_privacy)
        user.profile_photo_privacy = data.get('profile_photo_privacy', user.profile_photo_privacy)
        user.about_privacy = data.get('about_privacy', user.about_privacy)
        user.status_privacy = data.get('status_privacy', user.status_privacy)
        
        user.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==================== Chat List & Search Views ====================

@login_required
def chat_list_view(request):
    """Main chat list page"""
    # Get all chats for the user with latest message
    chats = Chat.objects.filter(
        participants=request.user
    ).annotate(
        latest_message_time=Max('messages__created_at')
    ).prefetch_related(
        'participants',
        Prefetch('messages', queryset=Message.objects.order_by('-created_at')[:1])
    ).order_by('-latest_message_time')
    
    # Get unread message counts
    unread_counts = {}
    for chat in chats:
        unread = Message.objects.filter(
            chat=chat
        ).exclude(
            sender=request.user
        ).exclude(
            receipts__user=request.user,
            receipts__status='read'
        ).count()
        unread_counts[chat.id] = unread
    
    context = {
        'chats': chats,
        'unread_counts': unread_counts,
    }
    
    return render(request, 'chat_list.html', context)


@login_required
def search_chats(request):
    """Search chats and messages via AJAX"""
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'results': []})
    
    # Search in chat names and messages
    chat_results = Chat.objects.filter(
        Q(participants=request.user) &
        (Q(name__icontains=query) | Q(messages__content__icontains=query))
    ).distinct()[:10]
    
    results = []
    for chat in chat_results:
        results.append({
            'id': str(chat.id),
            'name': chat.name if chat.chat_type == 'group' else 'Personal Chat',
            'type': chat.chat_type,
        })
    
    return JsonResponse({'results': results})


@login_required
def search_contacts(request):
    """Search contacts to start new chat"""
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'results': []})
    
    # Search users excluding self
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone_number__icontains=query)
    ).exclude(id=request.user.id)[:20]
    
    results = []
    for user in users:
        results.append({
            'id': user.id,
            'username': user.username,
            'name': f"{user.first_name} {user.last_name}",
            'phone': user.phone_number,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'about': user.about,
        })
    
    return JsonResponse({'results': results})


# ==================== Chat Views ====================

@login_required
def chat_detail_view(request, chat_id):
    """View a specific chat conversation"""
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    
    # Get or create chat participant
    chat_participant, _ = ChatParticipant.objects.get_or_create(
        chat=chat,
        user=request.user
    )
    
    # Get messages
    messages = Message.objects.filter(
        chat=chat
    ).exclude(
        deleted_for_everyone=True
    ).exclude(
        deletedmessage__user=request.user
    ).select_related('sender').prefetch_related(
        'receipts', 'reactions', 'reply_to'
    ).order_by('created_at')
    
    # Mark messages as read
    unread_receipts = MessageReceipt.objects.filter(
        message__chat=chat,
        user=request.user,
        status__in=['sent', 'delivered']
    ).exclude(message__sender=request.user)
    
    unread_receipts.update(status='read', read_at=timezone.now())
    
    # Get other participants
    other_participants = chat.participants.exclude(id=request.user.id)
    
    context = {
        'chat': chat,
        'messages': messages,
        'other_participants': other_participants,
        'chat_participant': chat_participant,
    }
    
    return render(request, 'chat_detail.html', context)


@login_required
def create_personal_chat(request):
    """Create or get existing personal chat"""
    if request.method == 'POST':
        data = json.loads(request.body)
        other_user_id = data.get('user_id')
        
        other_user = get_object_or_404(User, id=other_user_id)
        
        # Check if chat already exists
        existing_chat = Chat.objects.filter(
            chat_type='personal',
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        if existing_chat:
            return JsonResponse({
                'success': True,
                'chat_id': str(existing_chat.id),
                'redirect': f'/chats/{existing_chat.id}/'
            })
        
        # Create new chat
        chat = Chat.objects.create(
            chat_type='personal',
            created_by=request.user
        )
        
        ChatParticipant.objects.create(chat=chat, user=request.user, role='member')
        ChatParticipant.objects.create(chat=chat, user=other_user, role='member')
        
        return JsonResponse({
            'success': True,
            'chat_id': str(chat.id),
            'redirect': f'/chats/{chat.id}/'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def create_group_chat(request):
    """Create a new group chat"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        participant_ids = request.POST.getlist('participants[]')
        
        if not name or not participant_ids:
            return JsonResponse({'error': 'Name and participants required'}, status=400)
        
        # Create group
        chat = Chat.objects.create(
            chat_type='group',
            name=name,
            description=description,
            created_by=request.user
        )
        
        if 'group_icon' in request.FILES:
            chat.group_icon = request.FILES['group_icon']
            chat.save()
        
        # Add creator as admin
        ChatParticipant.objects.create(
            chat=chat,
            user=request.user,
            role='admin'
        )
        
        # Add other participants
        for user_id in participant_ids:
            user = User.objects.get(id=user_id)
            ChatParticipant.objects.create(
                chat=chat,
                user=user,
                role='member'
            )
        
        return JsonResponse({
            'success': True,
            'chat_id': str(chat.id),
            'redirect': f'/chats/{chat.id}/'
        })
    
    return render(request, 'create_group.html')


# ==================== Message Views ====================

@login_required
def send_message(request):
    """Send a message via AJAX"""
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        content = request.POST.get('content')
        message_type = request.POST.get('message_type', 'text')
        reply_to_id = request.POST.get('reply_to')
        
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        
        message_data = {
            'chat': chat,
            'sender': request.user,
            'message_type': message_type,
            'content': content,
        }
        
        if reply_to_id:
            message_data['reply_to_id'] = reply_to_id
        
        # Handle media files
        if 'media_file' in request.FILES:
            message_data['media_file'] = request.FILES['media_file']
        
        message = Message.objects.create(**message_data)
        
        # Create receipts for all participants except sender
        other_participants = chat.participants.exclude(id=request.user.id)
        for participant in other_participants:
            MessageReceipt.objects.create(
                message=message,
                user=participant,
                status='sent'
            )
        
        # Create media gallery entry if needed
        if message_type in ['image', 'video', 'document']:
            MediaGallery.objects.create(
                chat=chat,
                message=message,
                media_type=message_type,
                uploaded_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message_id': str(message.id),
            'created_at': message.created_at.isoformat(),
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_messages(request, chat_id):
    """Get messages for a chat via AJAX (for pagination/loading)"""
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    
    before_id = request.GET.get('before')
    limit = int(request.GET.get('limit', 50))
    
    messages = Message.objects.filter(chat=chat).exclude(
        deleted_for_everyone=True
    ).exclude(
        deletedmessage__user=request.user
    ).select_related('sender').prefetch_related('receipts', 'reactions')
    
    if before_id:
        messages = messages.filter(created_at__lt=Message.objects.get(id=before_id).created_at)
    
    messages = messages.order_by('-created_at')[:limit]
    
    messages_data = []
    for message in reversed(list(messages)):
        messages_data.append({
            'id': str(message.id),
            'sender_id': message.sender.id,
            'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
            'content': message.content,
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
            'is_own': message.sender == request.user,
        })
    
    return JsonResponse({'messages': messages_data})


@login_required
def delete_message(request, message_id):
    """Delete a message"""
    if request.method == 'POST':
        data = json.loads(request.body)
        delete_for_everyone = data.get('delete_for_everyone', False)
        
        message = get_object_or_404(Message, id=message_id, sender=request.user)
        
        if delete_for_everyone:
            # Check if within 1 hour
            if timezone.now() - message.created_at > timedelta(hours=1):
                return JsonResponse({'error': 'Can only delete for everyone within 1 hour'}, status=400)
            
            message.deleted_for_everyone = True
            message.content = "This message was deleted"
            message.save()
        else:
            # Delete for self only
            DeletedMessage.objects.get_or_create(
                message=message,
                user=request.user
            )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def react_to_message(request, message_id):
    """Add/remove reaction to a message"""
    if request.method == 'POST':
        data = json.loads(request.body)
        emoji = data.get('emoji')
        
        message = get_object_or_404(Message, id=message_id)
        
        # Check if already reacted
        existing_reaction = MessageReaction.objects.filter(
            message=message,
            user=request.user
        ).first()
        
        if existing_reaction:
            if existing_reaction.emoji == emoji:
                # Remove reaction
                existing_reaction.delete()
                return JsonResponse({'success': True, 'action': 'removed'})
            else:
                # Update reaction
                existing_reaction.emoji = emoji
                existing_reaction.save()
                return JsonResponse({'success': True, 'action': 'updated'})
        else:
            # Add new reaction
            MessageReaction.objects.create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            return JsonResponse({'success': True, 'action': 'added'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def star_message(request, message_id):
    """Star/unstar a message"""
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id)
        message.is_starred = not message.is_starred
        message.save()
        
        return JsonResponse({'success': True, 'is_starred': message.is_starred})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==================== Status Views ====================

@login_required
def status_list_view(request):
    """View all statuses"""
    # Get statuses from contacts
    contacts = Contact.objects.filter(user=request.user).values_list('contact_user', flat=True)
    
    statuses = Status.objects.filter(
        user__in=contacts,
        expires_at__gt=timezone.now()
    ).select_related('user').prefetch_related('views').order_by('-created_at')
    
    # My statuses
    my_statuses = Status.objects.filter(
        user=request.user,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')
    
    context = {
        'statuses': statuses,
        'my_statuses': my_statuses,
    }
    
    return render(request, 'status_list.html', context)


@login_required
def create_status(request):
    """Create a new status"""
    if request.method == 'POST':
        status_type = request.POST.get('status_type', 'text')
        content = request.POST.get('content', '')
        privacy = request.POST.get('privacy', 'contacts')
        
        status_data = {
            'user': request.user,
            'status_type': status_type,
            'privacy': privacy,
        }
        
        if status_type == 'text':
            status_data['content'] = content
            status_data['background_color'] = request.POST.get('background_color', '#25D366')
            status_data['font'] = request.POST.get('font', 'Arial')
        elif 'media_file' in request.FILES:
            status_data['media_file'] = request.FILES['media_file']
        
        status = Status.objects.create(**status_data)
        
        return JsonResponse({
            'success': True,
            'status_id': str(status.id),
        })
    
    return render(request, 'create_status.html')


@login_required
def view_status(request, status_id):
    """View a specific status"""
    status = get_object_or_404(Status, id=status_id, expires_at__gt=timezone.now())
    
    # Create view record
    StatusView.objects.get_or_create(
        status=status,
        viewer=request.user
    )
    
    context = {
        'status': status,
    }
    
    return render(request, 'view_status.html', context)


@login_required
def delete_status(request, status_id):
    """Delete own status"""
    if request.method == 'POST':
        status = get_object_or_404(Status, id=status_id, user=request.user)
        status.delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==================== Call Views ====================

@login_required
def calls_view(request):
    """View call history"""
    # Get all calls
    calls = Call.objects.filter(
        Q(caller=request.user) | Q(receiver=request.user)
    ).select_related('caller', 'receiver').order_by('-started_at')
    
    context = {
        'calls': calls,
    }
    
    return render(request, 'calls.html', context)


@login_required
def initiate_call(request):
    """Initiate a call"""
    if request.method == 'POST':
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        call_type = data.get('call_type', 'voice')
        
        receiver = get_object_or_404(User, id=receiver_id)
        
        call = Call.objects.create(
            caller=request.user,
            receiver=receiver,
            call_type=call_type,
            status='initiated'
        )
        
        return JsonResponse({
            'success': True,
            'call_id': str(call.id),
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def update_call_status(request, call_id):
    """Update call status (answer, end, decline)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        status = data.get('status')
        
        call = get_object_or_404(Call, id=call_id)
        
        if status == 'ongoing':
            call.status = 'ongoing'
            call.answered_at = timezone.now()
        elif status == 'ended':
            call.status = 'ended'
            call.ended_at = timezone.now()
            if call.answered_at:
                call.duration = int((call.ended_at - call.answered_at).total_seconds())
        elif status == 'declined':
            call.status = 'declined'
        elif status == 'missed':
            call.status = 'missed'
        
        call.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==================== Chat Management Views ====================

@login_required
def pin_chat(request, chat_id):
    """Pin/unpin a chat"""
    if request.method == 'POST':
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        participant = ChatParticipant.objects.get(chat=chat, user=request.user)
        
        participant.is_pinned = not participant.is_pinned
        participant.save()
        
        return JsonResponse({'success': True, 'is_pinned': participant.is_pinned})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def mute_chat(request, chat_id):
    """Mute/unmute a chat"""
    if request.method == 'POST':
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        participant = ChatParticipant.objects.get(chat=chat, user=request.user)
        
        participant.is_muted = not participant.is_muted
        participant.save()
        
        return JsonResponse({'success': True, 'is_muted': participant.is_muted})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def archive_chat(request, chat_id):
    """Archive/unarchive a chat"""
    if request.method == 'POST':
        chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
        participant = ChatParticipant.objects.get(chat=chat, user=request.user)
        
        participant.is_archived = not participant.is_archived
        participant.save()
        
        return JsonResponse({'success': True, 'is_archived': participant.is_archived})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def leave_group(request, chat_id):
    """Leave a group chat"""
    if request.method == 'POST':
        chat = get_object_or_404(Chat, id=chat_id, chat_type='group', participants=request.user)
        participant = ChatParticipant.objects.get(chat=chat, user=request.user)
        
        participant.delete()
        
        return JsonResponse({'success': True, 'redirect': '/chats/'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==================== Contact Management Views ====================

@login_required
def contacts_view(request):
    """View all contacts"""
    contacts = Contact.objects.filter(user=request.user).select_related('contact_user').order_by('name')
    
    context = {
        'contacts': contacts,
    }
    
    return render(request, 'contacts.html', context)


@login_required
def add_contact(request):
    """Add a new contact"""
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        name = data.get('name')
        
        contact_user = get_object_or_404(User, id=user_id)
        
        contact, created = Contact.objects.get_or_create(
            user=request.user,
            contact_user=contact_user,
            defaults={'name': name}
        )
        
        return JsonResponse({'success': True, 'created': created})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def block_user(request, user_id):
    """Block/unblock a user"""
    if request.method == 'POST':
        user_to_block = get_object_or_404(User, id=user_id)
        
        blocked, created = BlockedUser.objects.get_or_create(
            blocker=request.user,
            blocked=user_to_block
        )
        
        if not created:
            blocked.delete()
            return JsonResponse({'success': True, 'action': 'unblocked'})
        
        return JsonResponse({'success': True, 'action': 'blocked'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==================== Notifications View ====================

@login_required
def notifications_view(request):
    """Get notifications via AJAX"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'title': notif.title,
            'body': notif.body,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat(),
        })
    
    return JsonResponse({'notifications': notifications_data})


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)