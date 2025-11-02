from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid


class User(AbstractUser):
    """Extended User model for WhatsApp clone"""
    phone_number = models.CharField(max_length=20, unique=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    about = models.CharField(max_length=139, default="Hey there! I am using WhatsApp")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Privacy settings
    PRIVACY_CHOICES = [
        ('everyone', 'Everyone'),
        ('contacts', 'My Contacts'),
        ('nobody', 'Nobody'),
    ]
    last_seen_privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='everyone')
    profile_photo_privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='everyone')
    about_privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='everyone')
    status_privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='contacts')
    
    def __str__(self):
        return f"{self.username} ({self.phone_number})"


class Contact(models.Model):
    """User contacts/address book"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    contact_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacted_by')
    name = models.CharField(max_length=100)  # Custom name saved by user
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'contact_user']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.user.username}'s contact: {self.name}"


class Chat(models.Model):
    """Chat room - can be personal or group"""
    CHAT_TYPES = [
        ('personal', 'Personal'),
        ('group', 'Group'),
        ('broadcast', 'Broadcast'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPES, default='personal')
    participants = models.ManyToManyField(User, related_name='chats', through='ChatParticipant')
    
    # Group specific fields
    name = models.CharField(max_length=100, null=True, blank=True)  # For groups
    description = models.TextField(null=True, blank=True)
    group_icon = models.ImageField(upload_to='group_icons/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_chats')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.chat_type == 'group':
            return f"Group: {self.name}"
        elif self.chat_type == 'broadcast':
            return f"Broadcast: {self.name}"
        else:
            participants = self.participants.all()[:2]
            return f"Chat: {' & '.join([p.username for p in participants])}"


class ChatParticipant(models.Model):
    """Through model for Chat participants with additional info"""
    ROLES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_message = models.ForeignKey('Message', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    is_muted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['chat', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.chat}"


class Message(models.Model):
    """Individual messages in chats"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('contact', 'Contact'),
        ('location', 'Location'),
        ('sticker', 'Sticker'),
        ('voice', 'Voice Note'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(null=True, blank=True)  # For text messages
    
    # Media fields
    media_file = models.FileField(upload_to='messages/media/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='messages/thumbnails/', null=True, blank=True)
    media_duration = models.IntegerField(null=True, blank=True)  # For audio/video in seconds
    
    # Reply/Forward
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    forwarded_from = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='forwards')
    
    # Location data
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Message metadata
    is_deleted = models.BooleanField(default=False)
    deleted_for_everyone = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        content_preview = self.content[:50] if self.content else f"[{self.message_type}]"
        return f"{self.sender.username}: {content_preview}"


class MessageReceipt(models.Model):
    """Track message delivery and read status"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.message.id} - {self.user.username}: {self.status}"


class MessageReaction(models.Model):
    """Message reactions (emojis)"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  # Unicode emoji
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message"


class Status(models.Model):
    """WhatsApp Status (Stories)"""
    STATUS_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statuses')
    status_type = models.CharField(max_length=10, choices=STATUS_TYPES, default='text')
    
    # Content
    content = models.TextField(null=True, blank=True)  # For text status
    media_file = models.FileField(upload_to='status/media/', null=True, blank=True)
    background_color = models.CharField(max_length=7, null=True, blank=True)  # Hex color for text status
    font = models.CharField(max_length=50, null=True, blank=True)
    
    # Privacy
    privacy = models.CharField(max_length=10, choices=User.PRIVACY_CHOICES, default='contacts')
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 24 hours from creation
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username}'s status ({self.status_type}) - {self.created_at}"


class StatusView(models.Model):
    """Track who viewed a status"""
    status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['status', 'viewer']
    
    def __str__(self):
        return f"{self.viewer.username} viewed {self.status.user.username}'s status"


class Call(models.Model):
    """Voice and Video calls"""
    CALL_TYPES = [
        ('voice', 'Voice'),
        ('video', 'Video'),
    ]
    
    CALL_STATUS = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('ongoing', 'Ongoing'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('declined', 'Declined'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='voice')
    status = models.CharField(max_length=10, choices=CALL_STATUS, default='initiated')
    
    started_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # Duration in seconds
    
    def __str__(self):
        return f"{self.call_type.title()} call: {self.caller.username} → {self.receiver.username} ({self.status})"


class GroupCall(models.Model):
    """Group voice/video calls"""
    CALL_TYPES = [
        ('voice', 'Voice'),
        ('video', 'Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='group_calls')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default='voice')
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_group_calls')
    participants = models.ManyToManyField(User, related_name='group_calls', through='GroupCallParticipant')
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Group {self.call_type} call in {self.chat} - {self.started_at}"


class GroupCallParticipant(models.Model):
    """Participants in group calls"""
    group_call = models.ForeignKey(GroupCall, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} in group call"


class BlockedUser(models.Model):
    """Blocked users"""
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    blocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['blocker', 'blocked']
    
    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"


class ArchivedChat(models.Model):
    """Archived chats per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archived_chats')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    archived_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'chat']
    
    def __str__(self):
        return f"{self.user.username} archived {self.chat}"


class Notification(models.Model):
    """Push notifications"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('call', 'Incoming Call'),
        ('group_add', 'Added to Group'),
        ('status', 'Status Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    related_chat = models.ForeignKey(Chat, null=True, blank=True, on_delete=models.CASCADE)
    related_message = models.ForeignKey(Message, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


class MediaGallery(models.Model):
    """Store media shared in chats for gallery view"""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='media_gallery')
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10)  # image, video, document
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.media_type} in {self.chat} by {self.uploaded_by.username}"


class DeletedMessage(models.Model):
    """Track messages deleted by individual users"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='deleted_by_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} deleted message {self.message.id}"