from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Contact, Chat, ChatParticipant, Message, MessageReceipt,
    MessageReaction, Status, StatusView, Call, GroupCall, GroupCallParticipant,
    BlockedUser, ArchivedChat, Notification, MediaGallery, DeletedMessage
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'phone_number', 'email', 'is_online', 'last_seen', 'created_at']
    list_filter = ['is_online', 'is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'phone_number', 'email', 'first_name', 'last_name']
    readonly_fields = ['last_seen', 'created_at', 'updated_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('WhatsApp Profile', {
            'fields': ('phone_number', 'profile_picture', 'about', 'is_online', 'last_seen')
        }),
        ('Privacy Settings', {
            'fields': ('last_seen_privacy', 'profile_photo_privacy', 'about_privacy', 'status_privacy')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'email', 'first_name', 'last_name')
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['user', 'contact_user', 'name', 'is_blocked', 'created_at']
    list_filter = ['is_blocked', 'created_at']
    search_fields = ['user__username', 'contact_user__username', 'name']
    readonly_fields = ['created_at']
    autocomplete_fields = ['user', 'contact_user']


class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 1
    autocomplete_fields = ['user']
    readonly_fields = ['joined_at']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat_type', 'name', 'created_by', 'participant_count', 'created_at']
    list_filter = ['chat_type', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['created_by']
    inlines = [ChatParticipantInline]
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'chat', 'role', 'is_muted', 'is_pinned', 'is_archived', 'joined_at']
    list_filter = ['role', 'is_muted', 'is_pinned', 'is_archived', 'joined_at']
    search_fields = ['user__username', 'chat__name']
    readonly_fields = ['joined_at']
    autocomplete_fields = ['user', 'chat', 'last_read_message']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'chat', 'message_type', 'content_preview', 'is_deleted', 'created_at']
    list_filter = ['message_type', 'is_deleted', 'deleted_for_everyone', 'is_starred', 'created_at']
    search_fields = ['sender__username', 'content', 'chat__name']
    readonly_fields = ['id', 'created_at', 'edited_at']
    autocomplete_fields = ['sender', 'chat', 'reply_to', 'forwarded_from']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        if obj.content:
            return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return f"[{obj.message_type}]"
    content_preview.short_description = 'Content'


@admin.register(MessageReceipt)
class MessageReceiptAdmin(admin.ModelAdmin):
    list_display = ['message_preview', 'user', 'status', 'delivered_at', 'read_at']
    list_filter = ['status', 'delivered_at', 'read_at']
    search_fields = ['message__content', 'user__username']
    readonly_fields = ['delivered_at', 'read_at']
    autocomplete_fields = ['message', 'user']
    
    def message_preview(self, obj):
        return str(obj.message)[:50]
    message_preview.short_description = 'Message'


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['message_preview', 'user', 'emoji', 'created_at']
    list_filter = ['emoji', 'created_at']
    search_fields = ['message__content', 'user__username']
    readonly_fields = ['created_at']
    autocomplete_fields = ['message', 'user']
    
    def message_preview(self, obj):
        return str(obj.message)[:50]
    message_preview.short_description = 'Message'


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status_type', 'content_preview', 'privacy', 'view_count', 'created_at', 'expires_at']
    list_filter = ['status_type', 'privacy', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['id', 'created_at']
    autocomplete_fields = ['user']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        if obj.content:
            return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
        return f"[{obj.status_type}]"
    content_preview.short_description = 'Content'
    
    def view_count(self, obj):
        return obj.views.count()
    view_count.short_description = 'Views'


@admin.register(StatusView)
class StatusViewAdmin(admin.ModelAdmin):
    list_display = ['status_owner', 'viewer', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['status__user__username', 'viewer__username']
    readonly_fields = ['viewed_at']
    autocomplete_fields = ['status', 'viewer']
    
    def status_owner(self, obj):
        return obj.status.user.username
    status_owner.short_description = 'Status Owner'


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['id', 'caller', 'receiver', 'call_type', 'status', 'duration_formatted', 'started_at']
    list_filter = ['call_type', 'status', 'started_at']
    search_fields = ['caller__username', 'receiver__username']
    readonly_fields = ['id', 'started_at', 'answered_at', 'ended_at']
    autocomplete_fields = ['caller', 'receiver']
    date_hierarchy = 'started_at'
    
    def duration_formatted(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}m {seconds}s"
        return "0s"
    duration_formatted.short_description = 'Duration'


class GroupCallParticipantInline(admin.TabularInline):
    model = GroupCallParticipant
    extra = 1
    readonly_fields = ['joined_at', 'left_at']
    autocomplete_fields = ['user']


@admin.register(GroupCall)
class GroupCallAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'call_type', 'initiated_by', 'participant_count', 'started_at', 'ended_at']
    list_filter = ['call_type', 'started_at']
    search_fields = ['chat__name', 'initiated_by__username']
    readonly_fields = ['id', 'started_at', 'ended_at']
    autocomplete_fields = ['chat', 'initiated_by']
    inlines = [GroupCallParticipantInline]
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


@admin.register(GroupCallParticipant)
class GroupCallParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'group_call', 'joined_at', 'left_at']
    list_filter = ['joined_at', 'left_at']
    search_fields = ['user__username', 'group_call__chat__name']
    readonly_fields = ['joined_at', 'left_at']
    autocomplete_fields = ['group_call', 'user']


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ['blocker', 'blocked', 'blocked_at']
    list_filter = ['blocked_at']
    search_fields = ['blocker__username', 'blocked__username']
    readonly_fields = ['blocked_at']
    autocomplete_fields = ['blocker', 'blocked']


@admin.register(ArchivedChat)
class ArchivedChatAdmin(admin.ModelAdmin):
    list_display = ['user', 'chat', 'archived_at']
    list_filter = ['archived_at']
    search_fields = ['user__username', 'chat__name']
    readonly_fields = ['archived_at']
    autocomplete_fields = ['user', 'chat']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'body']
    readonly_fields = ['created_at']
    autocomplete_fields = ['user', 'related_chat', 'related_message']
    date_hierarchy = 'created_at'


@admin.register(MediaGallery)
class MediaGalleryAdmin(admin.ModelAdmin):
    list_display = ['chat', 'media_type', 'uploaded_by', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['chat__name', 'uploaded_by__username']
    readonly_fields = ['created_at']
    autocomplete_fields = ['chat', 'message', 'uploaded_by']
    date_hierarchy = 'created_at'


@admin.register(DeletedMessage)
class DeletedMessageAdmin(admin.ModelAdmin):
    list_display = ['message_preview', 'user', 'deleted_at']
    list_filter = ['deleted_at']
    search_fields = ['message__content', 'user__username']
    readonly_fields = ['deleted_at']
    autocomplete_fields = ['message', 'user']
    
    def message_preview(self, obj):
        return str(obj.message)[:50]
    message_preview.short_description = 'Message'