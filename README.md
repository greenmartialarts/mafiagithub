# Mafia Role Assignment App 

A modern web application for managing and assigning roles in the party game Mafia. Streamline your game setup and focus on the fun!

## ✨ Features

### Core Features
- Create and join game rooms with unique room codes
- Automatic role assignment with validation
- Support for multiple roles:
  - Mafia 🦹‍♂️
  - Doctor 👨‍⚕️
  - Cop 👮‍♂️
  - Villager 👥
- Real-time player list updates
- Role validation based on player count
- Host controls for managing the game

### Room Management
- Password-protected rooms
- Kick/ban functionality for hosts 

### Player Experience
- Role reveal animations
- Team identification for Mafia members
- Dark mode support
- Mobile-responsive design

## 🛠️ Tech Stack

- **Backend:** Django 5.1.3
- **Frontend:** 
  - HTML5
  - CSS3
  - JavaScript
  - Bootstrap 5
- **Database:** PostgreSQL (via Supabase)
- **WebSocket:** Channels 4.2.0
- **Deployment:** 
  - Gunicorn
  - Whitenoise
  - Redis

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git
- Redis server (for WebSocket support)
- PostgreSQL database

### Installation

1. Clone the repository