# WhatsApp Clone - Backend API

A full-featured WhatsApp clone backend built with Django and Django REST Framework, providing real-time messaging, voice/video calls, status updates, and comprehensive chat functionality.

##  Features

### Core Messaging
- **Real-time Messaging** - Text, images, videos, audio, documents, voice notes, and stickers
- **Group Chats** - Create and manage group conversations with admin controls
- **Message Receipts** - Sent, delivered, and read status indicators (double check marks)
- **Message Reactions** - React to messages with emojis
- **Reply & Forward** - Reply to specific messages and forward content
- **Delete Messages** - Delete for yourself or delete for everyone

### Status (Stories)
- **24-Hour Stories** - Share text, image, and video statuses that expire after 24 hours
- **Status Privacy** - Control who can view your status updates
- **View Tracking** - See who has viewed your status

### Calls
- **Voice & Video Calls** - One-to-one voice and video calling
- **Group Calls** - Multi-participant voice and video calls
- **Call History** - Complete call logs with duration tracking

### User Features
- **User Profiles** - Custom profile pictures, about text, and privacy settings
- **Contact Management** - Save contacts with custom names
- **User Privacy** - Control visibility of last seen, profile photo, about, and status
- **User Blocking** - Block and unblock users
- **Online Status** - Real-time online/offline indicators

### Chat Management
- **Pin Chats** - Pin important conversations to the top
- **Archive Chats** - Archive conversations to declutter your chat list
- **Mute Notifications** - Mute individual or group chats
- **Star Messages** - Bookmark important messages
- **Media Gallery** - Quick access to all shared media in conversations

### Notifications
- **Push Notifications** - Real-time notifications for messages, calls, and group activities
- **Custom Notification Settings** - Per-chat notification preferences

## Tech Stack

- **Backend Framework:** Django 4.2+
- **API:** Django REST Framework
- **Database:** PostgreSQL (recommended) / SQLite (development)
- **Real-time:** Django Channels (WebSocket support)
- **Authentication:** JWT Token-based authentication
- **File Storage:** Django Storage (supports S3, local, etc.)

##  Prerequisites

- Python 3.9+
- PostgreSQL 13+ (or SQLite for development)
- Redis (for Django Channels)
- pip and virtualenv

##  Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd whatsapp-clone
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

##  Project Structure

```
whatsapp-clone/
├── chat/
│   ├── models.py          # Database models
│   ├── admin.py           # Django admin configuration
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── urls.py            # URL routing
│   ├── consumers.py       # WebSocket consumers
│   └── signals.py         # Django signals
├── config/
│   ├── settings.py        # Project settings
│   ├── urls.py            # Main URL configuration
│   └── asgi.py            # ASGI configuration
├── media/                 # User uploaded files
├── static/                # Static files
├── requirements.txt       # Python dependencies
└── manage.py             # Django management script
```

##  Database Models

### Core Models
- **User** - Extended user model with WhatsApp-specific fields
- **Contact** - User contact management
- **Chat** - Personal, group, and broadcast chats
- **ChatParticipant** - Chat membership with roles and settings
- **Message** - All message types with metadata
- **MessageReceipt** - Delivery and read tracking
- **MessageReaction** - Emoji reactions

### Status & Calls
- **Status** - 24-hour status updates
- **StatusView** - Status view tracking
- **Call** - One-to-one calls
- **GroupCall** - Group call management
- **GroupCallParticipant** - Group call participants

### Additional Features
- **BlockedUser** - User blocking
- **ArchivedChat** - Chat archiving
- **Notification** - Push notifications
- **MediaGallery** - Media organization
- **DeletedMessage** - Message deletion tracking

##  Security Features

- JWT-based authentication
- Password hashing with Django's built-in security
- Privacy settings for user information
- Message encryption (end-to-end encryption ready)
- User blocking and reporting
- Rate limiting on API endpoints

## 🧪 Testing

Run tests with:
```bash
python manage.py test
```

##  API Documentation

API documentation is available at `/api/docs/` when running the development server.

Key endpoints:
- `/api/auth/` - Authentication endpoints
- `/api/users/` - User management
- `/api/chats/` - Chat operations
- `/api/messages/` - Message operations
- `/api/status/` - Status updates
- `/api/calls/` - Call management

##  Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in settings
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for Channels
- [ ] Configure static files serving
- [ ] Set up media file storage (S3 recommended)
- [ ] Configure environment variables
- [ ] Set up SSL certificates
- [ ] Configure CORS settings
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

##  Performance Optimization

- Database query optimization with `select_related` and `prefetch_related`
- Redis caching for frequently accessed data
- Media file compression
- Database indexing on frequently queried fields
- Pagination for large datasets
- WebSocket connection pooling

##  Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Developer

**Steve Ongera**  
Backend Developer  
 Email: steveongera001@gmail.com  
 GitHub: [@steveongera](https://github.com/steveongera)

##  Acknowledgments

- Django & Django REST Framework communities
- WhatsApp for inspiration
- All contributors and supporters

##  Support

For support, email steveongera001@gmail.com or open an issue in the repository.

---

**Note:** This is a clone project for educational purposes. WhatsApp is a trademark of Meta Platforms, Inc.