# Human Face Recognition Attendance System

A comprehensive face recognition-based attendance management system built with FastAPI and InsightFace, designed to automate attendance tracking using facial recognition technology.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Development](#development)

## 🎯 Overview

This project implements a real-time face recognition system for automated attendance marking. It uses deep learning-based face detection and recognition to identify students and record their attendance. The system provides both REST API endpoints and a web interface for easy integration and usage.

## ✨ Features

- **Real-time Face Detection & Recognition**: Detect and identify multiple faces simultaneously
- **Automated Attendance Marking**: Mark attendance automatically when a face is recognized
- **Student Management**: Register and manage student records with face embeddings
- **REST API**: Comprehensive API for integration with other systems
- **Web Interface**: Simple HTML templates for face detection and attendance marking
- **Webcam Support**: Real-time attendance marking using webcam
- **Authentication**: JWT-based authentication for secure API access
- **Multiple Face Detection**: Process and identify multiple faces in a single image
- **High Accuracy**: Uses state-of-the-art InsightFace model for face recognition
- **MongoDB Integration**: Persistent storage for student and attendance records

## 🛠 Technology Stack

### Backend Framework

- **FastAPI**: Modern, high-performance web framework for building APIs
- **Uvicorn**: Lightning-fast ASGI server
- **Python 3.x**: Core programming language

### Face Recognition & Computer Vision

- **InsightFace**: State-of-the-art 2D and 3D face analysis library
  - Model: `buffalo_l` - High accuracy face recognition model
  - 512-dimensional face embeddings
- **OpenCV (cv2)**: Computer vision library for image processing
- **MTCNN**: Multi-task Cascaded Convolutional Networks for face detection
- **NumPy**: Numerical computing for embedding operations

### Database

- **MongoDB**: NoSQL database for storing student and attendance records
- **PyMongo**: MongoDB driver for Python

### Authentication & Security

- **python-jose**: JWT token creation and verification
- **JWT (JSON Web Tokens)**: Secure authentication mechanism
- **HTTPBearer**: FastAPI security scheme

### Machine Learning & Data Processing

- **scikit-learn**: Machine learning utilities for model evaluation
- **NumPy**: Array operations and cosine similarity calculations

### Configuration & Environment

- **python-dotenv**: Environment variable management
- **Pydantic**: Data validation and settings management

### Additional Libraries

- **CORS Middleware**: Cross-Origin Resource Sharing support
- **tqdm**: Progress bars for training embeddings

## 🏗 System Architecture

### Core Components

1. **API Layer** (`app/api/`)

   - Authentication endpoints
   - Student management endpoints
   - Attendance marking endpoints

2. **Service Layer** (`app/services/`)

   - `face_detector.py`: Face detection using MTCNN
   - `face_embedder.py`: Face embedding generation using InsightFace
   - `face_matcher.py`: Cosine similarity-based face matching
   - `attendance_logic.py`: Business logic for attendance operations

3. **CRUD Layer** (`app/crud/`)

   - `student_crud.py`: Student database operations
   - `attendance_crud.py`: Attendance database operations

4. **Models** (`app/models/`)

   - `student.py`: Student data models
   - `attendance.py`: Attendance data models
   - `user.py`: User authentication models

5. **Core** (`app/core/`)
   - `config.py`: Configuration management
   - `database.py`: MongoDB connection
   - `security.py`: JWT authentication logic

### Data Flow

```
Image Upload → Face Detection (MTCNN/InsightFace) →
Face Embedding (InsightFace buffalo_l) →
Cosine Similarity Matching →
Student Identification →
Attendance Record Creation →
Database Storage (MongoDB)
```

## 📁 Project Structure

```
FYP-120/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── auth.py            # Authentication routes
│   │   ├── students.py        # Student management routes
│   │   └── attendance.py      # Attendance routes
│   ├── core/                  # Core configuration
│   │   ├── config.py          # Environment configuration
│   │   ├── database.py        # MongoDB connection
│   │   └── security.py        # JWT authentication
│   ├── crud/                  # Database operations
│   │   ├── student_crud.py    # Student CRUD operations
│   │   └── attendance_crud.py # Attendance CRUD operations
│   ├── models/                # Data models
│   │   ├── student.py         # Student models
│   │   ├── attendance.py      # Attendance models
│   │   └── user.py            # User models
│   ├── services/              # Business logic
│   │   ├── face_detector.py   # Face detection service
│   │   ├── face_embedder.py   # Face embedding service
│   │   ├── face_matcher.py    # Face matching service
│   │   └── attendance_logic.py# Attendance logic
│   ├── utils/                 # Utility functions
│   │   ├── image_utils.py     # Image processing utilities
│   │   └── logger.py          # Logging configuration
│   └── main.py                # FastAPI application entry point
├── ml/                        # Machine learning scripts
│   ├── train_embeddings.py    # Generate face embeddings
│   ├── evaluate_model.py      # Model evaluation
│   └── requirements.txt       # ML dependencies
├── scripts/                   # Utility scripts
│   ├── register_student.py    # Student registration
│   ├── mark_attendance.py     # Manual attendance marking
│   └── webcam_attendance.py   # Real-time webcam attendance
├── datasets/                  # Data storage
│   ├── raw/                   # Student face images
│   │   └── [student_id]/      # Individual student folders
│   └── embeddings/            # Generated embeddings
│       └── student_embeddings.npy
├── templates/                 # HTML templates
│   ├── index.html            # Main page
│   └── detect.html           # Detection interface
├── requirements.txt          # Main dependencies
└── README.md                 # This file
```

## 📥 Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB (local or cloud instance)
- Webcam (optional, for real-time attendance)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd FYP-120
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install ML dependencies
pip install -r ml/requirements.txt
```

### Step 4: Set Up MongoDB

Ensure MongoDB is running locally or have a MongoDB connection URI ready.

## ⚙ Configuration

Create a `.env` file in the project root:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=attendance_db

# Embeddings Directory
EMBEDDINGS_DIR=datasets/embeddings

# JWT Configuration (in app/core/security.py)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## 🚀 Usage

### 1. Prepare Student Data

Create folders for each student in `datasets/raw/`:

```
datasets/raw/
├── 1186/
│   ├── img1.jpg
│   ├── img2.jpg
│   └── img3.jpg
├── 1192/
│   └── ...
```

### 2. Train Face Embeddings

Generate face embeddings from student images:

```bash
python -m ml.train_embeddings
```

This will create `datasets/embeddings/student_embeddings.npy` containing all face embeddings.

### 3. Start the API Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 4. Access API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### 5. Real-time Webcam Attendance

```bash
python scripts/webcam_attendance.py
```

Press 's' to capture and mark attendance, 'q' to quit.

## 📡 API Endpoints

### Authentication

- `POST /auth/login` - User login
- `POST /auth/register` - User registration

### Students

- `GET /students/` - List all students
- `GET /students/{student_id}` - Get student details
- `POST /students/` - Register new student
- `PUT /students/{student_id}` - Update student
- `DELETE /students/{student_id}` - Delete student

### Attendance

- `POST /attendance/mark` - Mark attendance manually
- `POST /detect-face` - Detect and match faces, mark attendance
- `GET /attendance/` - Get attendance records
- `GET /attendance/student/{student_id}` - Get student attendance history
- `GET /attendance/date/{date}` - Get attendance by date

## 🔧 How It Works

### Face Recognition Pipeline

1. **Image Capture**: Image is captured via upload or webcam
2. **Face Detection**: InsightFace detects faces in the image
3. **Embedding Generation**: Each face is converted to a 512-dimensional embedding vector
4. **Similarity Matching**: Cosine similarity is computed between input embedding and stored embeddings
5. **Threshold Check**: If similarity > 0.6, face is recognized
6. **Student Identification**: Matched embedding is linked to student ID
7. **Attendance Recording**: Attendance record is created with timestamp

### Cosine Similarity Formula

The system uses cosine similarity to match faces:

$$\text{similarity} = \frac{\mathbf{a} \cdot \mathbf{b}}{||\mathbf{a}|| \times ||\mathbf{b}||}$$

Where:

- $\mathbf{a}$ = Input face embedding
- $\mathbf{b}$ = Stored face embedding
- Threshold = 0.6 (adjustable)

### InsightFace Model

- **Model**: buffalo_l
- **Embedding Size**: 512 dimensions
- **Detection Size**: 640x640 pixels
- **Provider**: CPUExecutionProvider (GPU support available)

## 👨‍💻 Development

### Running Tests

```bash
# Run model evaluation
python -m ml.evaluate_model
```

### Adding New Students

```bash
python scripts/register_student.py
```

### Code Structure Guidelines

- **API Routes**: Add new endpoints in `app/api/`
- **Business Logic**: Implement in `app/services/`
- **Database Operations**: Add to `app/crud/`
- **Data Models**: Define in `app/models/`
- **Configuration**: Update `app/core/config.py`

### Key Libraries Usage

- **FastAPI**: Async request handling, automatic documentation
- **InsightFace**: Face analysis and embedding generation
- **OpenCV**: Image preprocessing and manipulation
- **MongoDB**: Document-based storage for flexible data schema
- **JWT**: Stateless authentication for API security

## 📝 Notes

- Ensure good lighting conditions for accurate face detection
- Use multiple images per student for better recognition accuracy
- Adjust similarity threshold based on your requirements
- The system can detect and identify multiple faces simultaneously
- Embeddings need to be regenerated when new students are added

## 🤝 Contributors

FYP Group - NTU

## 📄 License

This project is part of a Final Year Project (FYP) at NTU.
