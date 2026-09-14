# 🌳 Family Tree App

A modern mobile app for building and sharing your family tree, built for all families.

## Features
- 🔐 Google Sign-In authentication
- 🌳 Interactive visual family tree with generational layout
- 👨‍👩‍👧 Add, edit and delete family members
- 💍 30+ relationship types in English, Hindi, Tamil, Telugu, Malayalam and Punjabi
- 🤝 Invite family members with a unique family code
- ✅ Join request system with owner approval
- 📱 Responsive design for all screen sizes
- 📢 Banner ads via Google AdMob
- 🔄 Real-time data sync via Railway backend

## Tech Stack
### Android App
- Kotlin + Jetpack Compose
- MVVM Architecture
- Retrofit2 + OkHttp for networking
- Google Sign-In SDK
- Google AdMob
- DataStore for token storage
- Navigation Compose

### Backend
- Django REST Framework
- MySQL database
- JWT authentication (djangorestframework-simplejwt)
- Google OAuth verification
- Deployed on Railway.app

## Getting Started

### Backend Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with your database and Google credentials
5. Run migrations: `python manage.py migrate`
6. Start the server: `python manage.py runserver`

### Android Setup
1. Open the project in Android Studio
2. Update `BASE_URL` in `RetrofitClient.kt` to point to your backend
3. Add your Google Web Client ID in `LoginScreen.kt`
4. Build and run on emulator or device

## Environment Variables

The backend reads the following variables from a `.env` file locally (see `config/settings.py`):

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True`/`False` — enables Django debug mode |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `DB_NAME` | MySQL database name |
| `DB_USER` | MySQL username |
| `DB_PASSWORD` | MySQL password |
| `DB_HOST` | MySQL host (defaults to `localhost`) |
| `DB_PORT` | MySQL port (defaults to `3306`) |
| `GOOGLE_CLIENT_ID` | Google OAuth Web Client ID used to verify Google Sign-In tokens |

On Railway, the database connection instead uses the platform-provided `MYSQLDATABASE`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLHOST` and `MYSQLPORT` variables automatically, falling back to the `DB_*` names above if they aren't set.
