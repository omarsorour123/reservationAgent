# Hotel Reservation Assistant

A comprehensive API-driven hotel room reservation system with a conversational assistant.

## Overview

This project is a hotel reservation system that combines the power of FastAPI for backend operations with a modern Streamlit frontend. It features a conversational LLM agent built using LangGraph that helps users find and book rooms through natural language interaction.

## Features

- **Conversational AI Assistant**: Natural language interface for hotel room reservations
- **Room Search**: Find available rooms by date, time, capacity, and features
- **Reservation Management**: Create and manage room reservations
- **User-friendly Interface**: Clean Streamlit UI for easy interaction
- **API-driven Architecture**: Modular design with a robust FastAPI backend

## Project Structure

```
hotel_reservation_assistant/
└── src/
    ├── agents/
    │   ├── __init__.py
    │   └── ReservationAgent.py       # LangGraph-based reservation agent
    ├── api/
    │   ├── models.py                 # API data models and schemas
    │   └── routes.py                 # API route definitions
    ├── core/
    │   ├── config.py                 # Application configuration
    │   ├── graph.py                  # LangGraph workflow definition
    │   └── __init__.py
    ├── database/
    │   ├── create_database.py        # Database initialization script
    │   ├── database_operations.py    # Database access functions
    │   ├── __init__.py
    │   └── test_db.py                # Database testing utilities
    ├── service/
    │   ├── __init__.py
    │   └── reservation_service.py    # Business logic for reservations
    ├── test/
    │   ├── __init__.py
    │   └── test_db.py                # Test cases
    ├── main.py                       # FastAPI application entry point
    ├── langchain_main.py             # LangChain integration 
    ├── streamlit_app.py              # Streamlit frontend application
    └── readme.md                     # Project documentation
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hotel-reservation-assistant.git
cd hotel-reservation-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Initial Setup

### Database Initialization

**Important:** Before starting the application, you must initialize the database:

```bash
cd src/database
python create_database.py
```

This script creates the necessary database tables and populates them with initial test data.

## Usage

### Starting the Backend API

```bash
cd src
python main.py
```

The API will be available at http://localhost:8000. You can access the API documentation at http://localhost:8000/docs.

### Starting the Frontend

```bash
cd src
streamlit run streamlit_app.py
```

The Streamlit interface will be available at http://localhost:8501.

## Components

### API Endpoints

- **GET /api/rooms** - List all rooms
- **POST /api/rooms/availability** - Check room availability
- **POST /api/rooms/reserve** - Reserve a room
- **GET /api/reservations** - List reservations
- **POST /api/chat** - Interact with the reservation assistant

### LangGraph Agent

The reservation assistant is built using LangGraph, which orchestrates the conversation flow and room booking process. The agent can:

1. Understand natural language queries about room availability
2. Provide room recommendations based on user requirements
3. Help users make reservations through conversational interaction
4. Answer questions about hotel amenities and policies

### Database

The application uses an SQLite database to store:
- Room information (ID, capacity, features)
- Reservation data (guest name, room, date, time)
- Historical booking data

## Development

### Environment Variables

Create a `.env` file in the project root with the following variables:
```
API_TITLE=Hotel Reservation API
API_VERSION=1.0.0
API_DESCRIPTION=API for hotel room reservations
API_PREFIX=/api
DATABASE_URL=sqlite:///./hotel.db
LLM_API_KEY=your_llm_api_key
```

### Running Tests

```bash
cd src
python -m pytest test/
```


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
