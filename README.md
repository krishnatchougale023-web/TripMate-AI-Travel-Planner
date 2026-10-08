# TripMate – AI Travel Planner ✈️

TripMate is an AI-powered travel planning web application that helps users create personalized travel itineraries based on their destination, number of days, budget, and number of travelers.

## 🚀 Features

- User Registration and Login
- AI-powered Trip Planning
- Personalized Travel Itinerary
- Destination and Travel Guide Information
- Save and View Previous Trips
- User Profile
- Feedback / Contact
- Download Trip Details
- MySQL Database Integration

## 🛠️ Technologies Used

- Python
- Flask
- HTML
- CSS
- JavaScript
- MySQL
- OpenRouter AI API

## 📁 Project Structure

```text
TripMate/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── Dashboard.css
│   ├── tripCSS.css
│   └── tripResult.css
│
└── templates/
    ├── TripResult.html
    ├── contact.html
    ├── login.html
    ├── myTrips.html
    ├── navbar.html
    ├── planTrip.html
    ├── profile.html
    ├── signup.html
    ├── travelGuides.html
    ├── trip.html
    └── viewTrip.html
```

## ⚙️ Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/krishnatchougale023-web/TripMate-AI-Travel-Planner.git
```

### 2. Open the project folder

```bash
cd TripMate-AI-Travel-Planner
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔐 Environment Variables

Create a `.env` file in the project root directory.

```env
FLASK_SECRET_KEY=your_secret_key
MYSQL_PASSWORD=your_mysql_password
OPENROUTER_API_KEY=your_openrouter_api_key
```

**Note:** Never upload the `.env` file to GitHub.

## ▶️ Run the Application

```bash
python app.py
```

## 🤖 AI Integration

TripMate uses the OpenRouter API to generate personalized travel itineraries based on the user's travel preferences.

## 👩‍💻 Developers

**Tejashri Chougale**
**[Sharvari Barage]**

BCA Students | Python | Flask | SQL | AI