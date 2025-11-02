"""
Django Management Command to Seed WhatsApp Clone Database
Path: whatsapp_app/management/commands/seed_data.py
Run: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import random
import os
from pathlib import Path

from whatsapp_app.models import (
    User, Contact, Chat, ChatParticipant, Message, MessageReceipt,
    MessageReaction, Status, StatusView, Call, GroupCall, GroupCallParticipant,
    BlockedUser, ArchivedChat, Notification, MediaGallery, DeletedMessage
)


class Command(BaseCommand):
    help = 'Seeds the database with realistic Kenyan WhatsApp data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        # Media path
        self.media_path = Path(r'D:\static\admin\Backup')
        
        # Create data
        users = self.create_users()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))
        
        contacts = self.create_contacts(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(contacts)} contacts'))
        
        chats = self.create_chats(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(chats)} chats'))
        
        messages = self.create_messages(chats, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(messages)} messages'))
        
        receipts = self.create_message_receipts(messages, chats)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(receipts)} message receipts'))
        
        reactions = self.create_reactions(messages, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(reactions)} reactions'))
        
        statuses = self.create_statuses(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(statuses)} statuses'))
        
        status_views = self.create_status_views(statuses, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(status_views)} status views'))
        
        calls = self.create_calls(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(calls)} calls'))
        
        group_calls = self.create_group_calls(chats, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(group_calls)} group calls'))
        
        blocked = self.create_blocked_users(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(blocked)} blocked users'))
        
        notifications = self.create_notifications(users, chats, messages)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(notifications)} notifications'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Database seeding completed successfully!'))

    def clear_data(self):
        """Clear all data from tables"""
        DeletedMessage.objects.all().delete()
        MediaGallery.objects.all().delete()
        Notification.objects.all().delete()
        ArchivedChat.objects.all().delete()
        BlockedUser.objects.all().delete()
        GroupCallParticipant.objects.all().delete()
        GroupCall.objects.all().delete()
        Call.objects.all().delete()
        StatusView.objects.all().delete()
        Status.objects.all().delete()
        MessageReaction.objects.all().delete()
        MessageReceipt.objects.all().delete()
        Message.objects.all().delete()
        ChatParticipant.objects.all().delete()
        Chat.objects.all().delete()
        Contact.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def get_random_file(self, extension=None):
        """Get random file from media path"""
        if not self.media_path.exists():
            return None
        
        files = list(self.media_path.glob('**/*'))
        if extension:
            files = [f for f in files if f.suffix.lower() == extension.lower()]
        
        if not files:
            return None
        
        return random.choice(files)
    
    def attach_file_to_message(self, message, file_path):
        """Properly attach a file to a message"""
        if file_path and file_path.exists():
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    from django.core.files.base import ContentFile
                    message.media_file.save(file_path.name, ContentFile(file_content), save=True)
                return True
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not attach file {file_path}: {e}'))
        return False

    def create_users(self):
        """Create Kenyan users"""
        kenyan_names = [
            ('Kamau', 'Njoroge', 'kamau_njoroge'),
            ('Akinyi', 'Odhiambo', 'akinyi_odhiambo'),
            ('Mwangi', 'Kariuki', 'mwangi_kariuki'),
            ('Wanjiru', 'Kimani', 'wanjiru_kimani'),
            ('Otieno', 'Omondi', 'otieno_omondi'),
            ('Njeri', 'Muthoni', 'njeri_muthoni'),
            ('Kipchoge', 'Kibet', 'kipchoge_kibet'),
            ('Chebet', 'Jepkorir', 'chebet_jepkorir'),
            ('Mutua', 'Musyoka', 'mutua_musyoka'),
            ('Mwikali', 'Nduku', 'mwikali_nduku'),
            ('Juma', 'Hassan', 'juma_hassan'),
            ('Amina', 'Mohammed', 'amina_mohammed'),
            ('Koech', 'Kimutai', 'koech_kimutai'),
            ('Chepkoech', 'Sang', 'chepkoech_sang'),
            ('Ochieng', 'Onyango', 'ochieng_onyango'),
            ('Auma', 'Adhiambo', 'auma_adhiambo'),
            ('Gitau', 'Karanja', 'gitau_karanja'),
            ('Wairimu', 'Wanjiku', 'wairimu_wanjiku'),
            ('Wekesa', 'Barasa', 'wekesa_barasa'),
            ('Nafula', 'Simiyu', 'nafula_simiyu'),
        ]
        
        about_texts = [
            "Available",
            "At work",
            "Busy",
            "Jambo! 🇰🇪",
            "Hakuna Matata",
            "Living my best life in Nairobi",
            "Faith over fear",
            "Blessed and grateful",
            "Work hard, pray harder",
            "Entrepreneur 💼",
            "Team Mafisi 😎",
            "Upcountry is calling",
            "Nairobi ni kuteseka 😅",
            "God's plan",
            "hustling in Mombasa",
        ]
        
        users = []
        for i, (first_name, last_name, username) in enumerate(kenyan_names):
            # Kenyan phone number format
            phone = f"+254{random.choice([7, 1])}{random.randint(10000000, 99999999)}"
            
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=f"{username}@example.com",
                phone_number=phone,
                password=make_password('password123'),
                about=random.choice(about_texts),
                is_online=random.choice([True, False]),
                last_seen=timezone.now() - timedelta(minutes=random.randint(1, 1440)),
                last_seen_privacy=random.choice(['everyone', 'contacts', 'nobody']),
                profile_photo_privacy=random.choice(['everyone', 'contacts', 'nobody']),
                about_privacy=random.choice(['everyone', 'contacts', 'nobody']),
                status_privacy=random.choice(['everyone', 'contacts']),
            )
            users.append(user)
        
        return users

    def create_contacts(self, users):
        """Create contacts between users"""
        contacts = []
        for user in users:
            # Each user has 5-15 contacts
            contact_users = random.sample([u for u in users if u != user], random.randint(5, min(15, len(users)-1)))
            for contact_user in contact_users:
                contact = Contact.objects.create(
                    user=user,
                    contact_user=contact_user,
                    name=f"{contact_user.first_name} {contact_user.last_name}",
                    is_blocked=random.choice([False] * 95 + [True] * 5)  # 5% blocked
                )
                contacts.append(contact)
        
        return contacts

    def create_chats(self, users):
        """Create personal and group chats"""
        chats = []
        
        # Personal chats (one-to-one)
        for i in range(30):
            user1, user2 = random.sample(users, 2)
            chat = Chat.objects.create(
                chat_type='personal',
                created_by=user1
            )
            
            ChatParticipant.objects.create(
                chat=chat,
                user=user1,
                role='member',
                is_pinned=random.choice([False] * 8 + [True] * 2),
                is_muted=random.choice([False] * 9 + [True] * 1),
            )
            
            ChatParticipant.objects.create(
                chat=chat,
                user=user2,
                role='member',
                is_pinned=random.choice([False] * 8 + [True] * 2),
            )
            
            chats.append(chat)
        
        # Group chats
        group_names = [
            'Family WhatsApp',
            'University Comrades',
            'Nairobi Hustlers',
            'Church Youth Group',
            'Mombasa Beach Lovers',
            'Chama Investment Group',
            'Football Fanatics',
            'Githurai Residents',
            'Office Team',
            'High School Reunion',
            'Rift Valley Connect',
            'Kisumu Squad',
            'Nakuru Vibes',
            'Diaspora Kenya',
            'Entrepreneurs Hub',
        ]
        
        for group_name in group_names[:10]:  # Create 10 groups
            admin = random.choice(users)
            chat = Chat.objects.create(
                chat_type='group',
                name=group_name,
                description=f"Welcome to {group_name}! Stay connected.",
                created_by=admin
            )
            
            # Admin
            ChatParticipant.objects.create(
                chat=chat,
                user=admin,
                role='admin'
            )
            
            # Members (5-15 members)
            members = random.sample([u for u in users if u != admin], random.randint(5, 15))
            for member in members:
                ChatParticipant.objects.create(
                    chat=chat,
                    user=member,
                    role='member',
                    is_pinned=random.choice([False] * 9 + [True] * 1),
                    is_muted=random.choice([False] * 7 + [True] * 3),
                )
            
            chats.append(chat)
        
        return chats

    def create_messages(self, chats, users):
        """Create messages with various types"""
        kenyan_messages = [
            "Niaje buda?",
            "Vipi ndugu?",
            "Uko wapi saa hii?",
            "Tupatane town kesho",
            "Niko kwa jam ya Thika Road",
            "Pesa imepatikana?",
            "Tulia tu bana",
            "Si unipe missed call",
            "Nipeleke fare ya kuenda home",
            "Kuja tukunywe chai",
            "Meeting ni saa ngapi?",
            "Niko kwa gari ya matatu",
            "Tutaonana Ngara",
            "Nashangaa sana",
            "Pole sana mdau",
            "Asante sana",
            "Mungu akubariki",
            "Tuombee",
            "Nitafika soon",
            "Nataka kucheki hiyo deal",
            "Wacha jokes",
            "Enyewe ni ukweli",
            "Hizo ni story za jaba",
            "Mi siko sure",
            "Tutakutext",
            "Bado niko kwa njia",
            "Niko na bundles kidogo",
            "Nitakupigia simu",
            "Nimefika home salama",
            "Lala salama",
        ]
        
        messages = []
        
        for chat in chats:
            participants = list(chat.participants.all())
            if not participants:
                continue
            
            # Create 10-50 messages per chat
            num_messages = random.randint(10, 50)
            
            for i in range(num_messages):
                sender = random.choice(participants)
                message_type = random.choices(
                    ['text', 'image', 'video', 'audio', 'document', 'voice', 'location'],
                    weights=[70, 10, 5, 5, 5, 3, 2]
                )[0]
                
                message_data = {
                    'chat': chat,
                    'sender': sender,
                    'message_type': message_type,
                    'created_at': timezone.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23)),
                    'is_deleted': random.choice([False] * 95 + [True] * 5),
                    'is_starred': random.choice([False] * 9 + [True] * 1),
                }
                
                if message_type == 'text':
                    message_data['content'] = random.choice(kenyan_messages)
                elif message_type == 'location':
                    # Kenyan coordinates (Nairobi area)
                    message_data['latitude'] = -1.286389 + random.uniform(-0.5, 0.5)
                    message_data['longitude'] = 36.817223 + random.uniform(-0.5, 0.5)
                    message_data['content'] = "📍 My Location"
                elif message_type == 'image':
                    message_data['content'] = "📷 Photo"
                    image_file = self.get_random_file('.jpg')
                    # Skip if no file found
                elif message_type == 'video':
                    message_data['content'] = "🎥 Video"
                    message_data['media_duration'] = random.randint(5, 180)
                    # Skip file attachment for now
                elif message_type == 'audio':
                    message_data['content'] = "🎵 Audio"
                    message_data['media_duration'] = random.randint(10, 300)
                    # Skip file attachment for now
                elif message_type == 'document':
                    message_data['content'] = "📄 Document"
                    # Skip file attachment for now
                elif message_type == 'voice':
                    message_data['content'] = "🎤 Voice message"
                    message_data['media_duration'] = random.randint(1, 60)
                
                # Reply to previous message sometimes
                if messages and random.random() < 0.15:  # 15% chance
                    previous_messages = [m for m in messages if m.chat == chat]
                    if previous_messages:
                        message_data['reply_to'] = random.choice(previous_messages)
                
                message = Message.objects.create(**message_data)
                messages.append(message)
                
                # Create media gallery entry for media messages
                if message_type in ['image', 'video', 'document']:
                    MediaGallery.objects.create(
                        chat=chat,
                        message=message,
                        media_type=message_type,
                        uploaded_by=sender
                    )
        
        return messages

    def create_message_receipts(self, messages, chats):
        """Create message receipts"""
        receipts = []
        
        for message in messages:
            chat = message.chat
            participants = chat.participants.exclude(id=message.sender.id)
            
            for participant in participants:
                status = random.choices(
                    ['sent', 'delivered', 'read'],
                    weights=[5, 15, 80]
                )[0]
                
                receipt_data = {
                    'message': message,
                    'user': participant,
                    'status': status,
                }
                
                if status in ['delivered', 'read']:
                    receipt_data['delivered_at'] = message.created_at + timedelta(seconds=random.randint(1, 60))
                
                if status == 'read':
                    receipt_data['read_at'] = receipt_data['delivered_at'] + timedelta(seconds=random.randint(1, 300))
                
                receipt = MessageReceipt.objects.create(**receipt_data)
                receipts.append(receipt)
        
        return receipts

    def create_reactions(self, messages, users):
        """Create message reactions"""
        reactions = []
        emojis = ['❤️', '😂', '😮', '😢', '🙏', '👍', '👎', '🔥', '🎉', '💯']
        
        for message in random.sample(messages, min(len(messages) // 3, 100)):
            # 1-3 reactions per message
            num_reactions = random.randint(1, 3)
            reactors = random.sample(list(message.chat.participants.all()), min(num_reactions, message.chat.participants.count()))
            
            for reactor in reactors:
                reaction = MessageReaction.objects.create(
                    message=message,
                    user=reactor,
                    emoji=random.choice(emojis)
                )
                reactions.append(reaction)
        
        return reactions

    def create_statuses(self, users):
        """Create status updates"""
        statuses = []
        status_texts = [
            "Enjoying the Nairobi sun ☀️",
            "Blessed Sunday! 🙏",
            "At the beach 🏖️",
            "New week, new goals 💪",
            "Traffic iko mob 😫",
            "Hakuna Matata 🇰🇪",
            "Living my best life",
            "God is good all the time",
            "Hustle mode activated 💼",
            "Weekend vibes 🎉",
        ]
        
        colors = ['#FF5733', '#33FF57', '#3357FF', '#F333FF', '#33FFF3', '#FFD700']
        
        for user in random.sample(users, min(len(users) // 2, 10)):
            # 1-3 statuses per user
            for _ in range(random.randint(1, 3)):
                status_type = random.choices(['text', 'image', 'video'], weights=[40, 50, 10])[0]
                
                status_data = {
                    'user': user,
                    'status_type': status_type,
                    'privacy': random.choice(['everyone', 'contacts']),
                    'created_at': timezone.now() - timedelta(hours=random.randint(1, 23)),
                }
                
                if status_type == 'text':
                    status_data['content'] = random.choice(status_texts)
                    status_data['background_color'] = random.choice(colors)
                    status_data['font'] = random.choice(['Arial', 'Helvetica', 'Sans-serif'])
                
                status = Status.objects.create(**status_data)
                statuses.append(status)
        
        return statuses

    def create_status_views(self, statuses, users):
        """Create status views"""
        views = []
        
        for status in statuses:
            # 3-10 viewers per status
            viewers = random.sample([u for u in users if u != status.user], random.randint(3, min(10, len(users)-1)))
            
            for viewer in viewers:
                view = StatusView.objects.create(
                    status=status,
                    viewer=viewer,
                    viewed_at=status.created_at + timedelta(minutes=random.randint(1, 300))
                )
                views.append(view)
        
        return views

    def create_calls(self, users):
        """Create call records"""
        calls = []
        
        for _ in range(50):
            caller, receiver = random.sample(users, 2)
            call_type = random.choice(['voice', 'video'])
            status = random.choices(
                ['ended', 'missed', 'declined'],
                weights=[70, 20, 10]
            )[0]
            
            call_data = {
                'caller': caller,
                'receiver': receiver,
                'call_type': call_type,
                'status': status,
                'started_at': timezone.now() - timedelta(days=random.randint(0, 30)),
            }
            
            if status == 'ended':
                call_data['answered_at'] = call_data['started_at'] + timedelta(seconds=random.randint(2, 10))
                call_data['duration'] = random.randint(30, 3600)
                call_data['ended_at'] = call_data['answered_at'] + timedelta(seconds=call_data['duration'])
            
            call = Call.objects.create(**call_data)
            calls.append(call)
        
        return calls

    def create_group_calls(self, chats, users):
        """Create group calls"""
        group_calls = []
        group_chats = [c for c in chats if c.chat_type == 'group']
        
        for chat in random.sample(group_chats, min(len(group_chats), 5)):
            initiator = random.choice(list(chat.participants.all()))
            
            group_call = GroupCall.objects.create(
                chat=chat,
                call_type=random.choice(['voice', 'video']),
                initiated_by=initiator,
                started_at=timezone.now() - timedelta(days=random.randint(0, 7)),
                ended_at=timezone.now() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 2))
            )
            
            # 3-8 participants
            participants = random.sample(list(chat.participants.all()), random.randint(3, min(8, chat.participants.count())))
            
            for participant in participants:
                GroupCallParticipant.objects.create(
                    group_call=group_call,
                    user=participant,
                    joined_at=group_call.started_at + timedelta(seconds=random.randint(0, 30)),
                    left_at=group_call.ended_at - timedelta(seconds=random.randint(0, 60)) if random.random() < 0.8 else None
                )
            
            group_calls.append(group_call)
        
        return group_calls

    def create_blocked_users(self, users):
        """Create blocked users"""
        blocked = []
        
        for _ in range(10):
            blocker, blocked_user = random.sample(users, 2)
            try:
                block = BlockedUser.objects.create(
                    blocker=blocker,
                    blocked=blocked_user
                )
                blocked.append(block)
            except:
                pass  # Skip if already exists
        
        return blocked

    def create_notifications(self, users, chats, messages):
        """Create notifications"""
        notifications = []
        
        for user in random.sample(users, min(len(users), 10)):
            for _ in range(random.randint(3, 10)):
                notif_type = random.choice(['message', 'call', 'group_add', 'status'])
                
                notif_data = {
                    'user': user,
                    'notification_type': notif_type,
                    'is_read': random.choice([True, False]),
                    'created_at': timezone.now() - timedelta(hours=random.randint(1, 48))
                }
                
                if notif_type == 'message':
                    message = random.choice(messages)
                    notif_data['title'] = f"New message from {message.sender.first_name}"
                    notif_data['body'] = message.content[:50] if message.content else f"[{message.message_type}]"
                    notif_data['related_chat'] = message.chat
                    notif_data['related_message'] = message
                elif notif_type == 'call':
                    caller = random.choice(users)
                    notif_data['title'] = f"Missed call from {caller.first_name}"
                    notif_data['body'] = f"{caller.first_name} {caller.last_name} tried to call you"
                elif notif_type == 'group_add':
                    chat = random.choice([c for c in chats if c.chat_type == 'group'])
                    notif_data['title'] = f"Added to {chat.name}"
                    notif_data['body'] = f"You were added to {chat.name}"
                    notif_data['related_chat'] = chat
                elif notif_type == 'status':
                    poster = random.choice(users)
                    notif_data['title'] = f"{poster.first_name} posted a status"
                    notif_data['body'] = "View their latest status update"
                
                notification = Notification.objects.create(**notif_data)
                notifications.append(notification)
        
        return notifications