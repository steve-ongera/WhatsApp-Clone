"""
WhatsApp Clone WebSocket Consumers
Path: whatsapp_app/consumers.py
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import (
    User, Chat, Message, MessageReceipt, ChatParticipant,
    Call, Notification
)


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time messaging"""
    
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']
        
        # Check if user is participant
        is_participant = await self.check_participant()
        
        if not is_participant:
            await self.close()
            return
        
        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update user online status
        await self.update_online_status(True)
        
        # Notify others user is online
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'is_online': True,
            }
        )
    
    async def disconnect(self, close_code):
        # Leave chat group
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
        
        # Update user online status
        await self.update_online_status(False)
        
        # Notify others user is offline
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'is_online': False,
            }
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(data)
        elif message_type == 'delete_message':
            await self.handle_delete_message(data)
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message"""
        content = data.get('content')
        reply_to_id = data.get('reply_to')
        
        # Save message to database
        message = await self.save_message(content, reply_to_id)
        
        if message:
            # Send message to chat group
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'sender_id': self.user.id,
                        'sender_name': f"{self.user.first_name} {self.user.last_name}",
                        'content': message.content,
                        'message_type': message.message_type,
                        'created_at': message.created_at.isoformat(),
                        'reply_to': str(reply_to_id) if reply_to_id else None,
                    }
                }
            )
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)
        
        # Send typing status to group
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': f"{self.user.first_name} {self.user.last_name}",
                'is_typing': is_typing,
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle read receipt"""
        message_id = data.get('message_id')
        
        # Update receipt in database
        await self.update_receipt(message_id, 'read')
        
        # Notify sender
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'read_receipt',
                'message_id': message_id,
                'user_id': self.user.id,
            }
        )
    
    async def handle_delete_message(self, data):
        """Handle message deletion"""
        message_id = data.get('message_id')
        delete_for_everyone = data.get('delete_for_everyone', False)
        
        deleted = await self.delete_message(message_id, delete_for_everyone)
        
        if deleted:
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id,
                    'delete_for_everyone': delete_for_everyone,
                }
            )
    
    # WebSocket event handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send own typing indicator back
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))
    
    async def user_status(self, event):
        """Send user online status to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'is_online': event['is_online'],
        }))
    
    async def read_receipt(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
        }))
    
    async def message_deleted(self, event):
        """Send message deletion notification"""
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
            'delete_for_everyone': event['delete_for_everyone'],
        }))
    
    # Database operations
    @database_sync_to_async
    def check_participant(self):
        """Check if user is a participant of the chat"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return chat.participants.filter(id=self.user.id).exists()
        except Chat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        """Save message to database"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            
            message_data = {
                'chat': chat,
                'sender': self.user,
                'content': content,
                'message_type': 'text',
            }
            
            if reply_to_id:
                message_data['reply_to_id'] = reply_to_id
            
            message = Message.objects.create(**message_data)
            
            # Create receipts for other participants
            other_participants = chat.participants.exclude(id=self.user.id)
            for participant in other_participants:
                MessageReceipt.objects.create(
                    message=message,
                    user=participant,
                    status='sent'
                )
            
            return message
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def update_receipt(self, message_id, status):
        """Update message receipt status"""
        try:
            receipt = MessageReceipt.objects.get(
                message_id=message_id,
                user=self.user
            )
            receipt.status = status
            if status == 'read':
                receipt.read_at = timezone.now()
            elif status == 'delivered':
                receipt.delivered_at = timezone.now()
            receipt.save()
            return True
        except MessageReceipt.DoesNotExist:
            return False
    
    @database_sync_to_async
    def delete_message(self, message_id, delete_for_everyone):
        """Delete a message"""
        try:
            message = Message.objects.get(id=message_id, sender=self.user)
            
            if delete_for_everyone:
                # Check if within 1 hour
                from datetime import timedelta
                if timezone.now() - message.created_at > timedelta(hours=1):
                    return False
                
                message.deleted_for_everyone = True
                message.content = "This message was deleted"
                message.save()
            
            return True
        except Message.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_online_status(self, is_online):
        """Update user online status"""
        self.user.is_online = is_online
        self.user.save(update_fields=['is_online', 'last_seen'])


class CallConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time calling (WebRTC signaling)"""
    
    async def connect(self):
        self.call_id = self.scope['url_route']['kwargs']['call_id']
        self.call_group_name = f'call_{self.call_id}'
        self.user = self.scope['user']
        
        # Join call group
        await self.channel_layer.group_add(
            self.call_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave call group
        await self.channel_layer.group_discard(
            self.call_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
            }
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        signal_type = data.get('type')
        
        # Forward WebRTC signaling messages
        if signal_type in ['offer', 'answer', 'ice_candidate']:
            await self.channel_layer.group_send(
                self.call_group_name,
                {
                    'type': 'webrtc_signal',
                    'signal_type': signal_type,
                    'user_id': self.user.id,
                    'data': data.get('data'),
                }
            )
    
    async def webrtc_signal(self, event):
        """Forward WebRTC signaling to client"""
        # Don't send signal back to sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': event['signal_type'],
                'user_id': event['user_id'],
                'data': event['data'],
            }))
    
    async def user_left(self, event):
        """Notify that a user left the call"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for push notifications"""
    
    async def connect(self):
        self.user = self.scope['user']
        self.user_group_name = f'user_{self.user.id}'
        
        # Join user's personal notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave notification group
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        # Handle any client messages if needed
        pass
    
    async def notification(self, event):
        """Send notification to client"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification'],
        }))