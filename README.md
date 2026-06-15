# Face Recognition Attendance & Sentiment Analysis Backend Integration Guide

Welcome to the definitive integration guide for the **Real-Time Face Recognition Attendance Management System** and the **AI-Powered Sentiment Analysis** backend. This document contains all the architectural, API, and WebSocket details necessary for frontend developers to build client interfaces, authentication workflows, and dashboards.

---

## 1. Project Overview & Architecture

This application functions as a high-throughput, real-time facial recognition attendance system with provisions for AI-powered sentiment analysis. It features class-isolated collection matching, dynamic face embedding generation, and live camera streaming over WebSockets.

### Tech Stack Details:
- **FastAPI (Python)**: High-performance ASGI framework for serving API endpoints and managing asynchronous WebSocket connections.
- **MongoDB**: NoSQL database holding student profiles and logs. Utilizes class-isolated collections (e.g. `students-BSCS-8B` and `attendance-BSCS-8B`) for security, scalability, and zero cross-class data leaks.
- **MTCNN & FaceNet**: Employed in backend services for highly accurate face detection and 512-dimension face embedding extraction.
- **RoBERTa Transformer**: Targeted for NLP tasks (such as class feedback/sentiment analysis scoring).
- **InsightFace**: Runs model pipelines for multi-face localization, alignment, and matching.

---

## 2. Frontend Developer Integration Guide

### Authentication Flow
The backend uses **JWT Bearer Token** authentication. All secure endpoints require the `Authorization` header populated with the token obtained during login.

#### Step-by-Step Logic Flow:
1. **Landing/Login Page**: 
   - Arrive at `/`.
   - Submit user credentials to `POST /auth/login` as form data.
   - If credentials are valid, the backend returns a JSON payload containing the JWT token.
2. **Token Management**:
   - Store the returned `access_token` securely in client-side state, local storage, or a secure cookie.
   - Include this token in the header of all subsequent API requests:
     ```http
     Authorization: Bearer <your_access_token_here>
     ```
3. **Dashboard Access**:
   - Fetch initial statistics and listings using `GET /students/list` and `GET /attendance/`.
   - Verify health and configuration using `GET /health` and `GET /api/info`.

---

## 3. Complete API Endpoint Reference

### Authentication Module

#### `POST /auth/login`
Authenticates administration users and returns a JWT bearer token.
- **Content-Type**: `application/x-www-form-urlencoded`
- **Request Payload**:
  ```yaml
  username: admin@fyp.com
  password: admin123
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```
- **Error Response (401 Unauthorized)**:
  ```json
  {
    "detail": "Invalid credentials"
  }
  ```

---

### Student Management Module

#### `POST /students/register`
Registers a new student profile and generates their reference face embeddings.
- **Authorization**: Required (Bearer Token)
- **Content-Type**: `multipart/form-data`
- **Request Payload**:
  - `name` (string): Full name of the student.
  - `reg_number` (string): Unique registration ID.
  - `class_name` (string): Target class collection (e.g., `BSCS-8B`).
  - `image1`, `image2`, `image3`, `image4`, `image5` (Files): Exactly 5 distinct JPG/PNG images of the student's face.
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Student registered successfully",
    "student_id": "22-NTU-CS-1192",
    "name": "Test Student",
    "class_name": "BSCS-8B",
    "collection_name": "students-BSCS-8B",
    "image_paths": [
      "datasets/BSCS-8B/22-NTU-CS-1192/image1.jpg",
      "datasets/BSCS-8B/22-NTU-CS-1192/image2.jpg",
      "datasets/BSCS-8B/22-NTU-CS-1192/image3.jpg",
      "datasets/BSCS-8B/22-NTU-CS-1192/image4.jpg",
      "datasets/BSCS-8B/22-NTU-CS-1192/image5.jpg"
    ]
  }
  ```
- **Error Responses**:
  - `400 Bad Request` (Invalid payload structure or no faces detected in any uploaded images).
  - `401 Unauthorized` (Missing/invalid JWT).
  - `500 Internal Server Error` (Database or physical write failure).

#### `POST /students/enroll`
Onboards a new student and triggers automatic system retraining to update the embeddings file cache.
- **Authorization**: Required (Bearer Token)
- **Content-Type**: `multipart/form-data`
- **Request Payload**:
  - `name` (string): Student name.
  - `roll_number` (string): Student ID.
  - `class_name` (string, optional): Target class.
  - `image1` to `image5` (Files): exactly 5 face images.
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Student enrolled and trained successfully",
    "student_id": "22-NTU-CS-1192",
    "name": "Test Student",
    "images_saved": 5
  }
  ```

#### `GET /students/list`
Lists registered students with class-level filters and page offsets.
- **Request Parameters**:
  - `skip` (Query, int): Offset index (Default: 0).
  - `limit` (Query, int): Max count to return (Default: 10).
  - `class_name` (Query, string, optional): Limit search to a specific class collection.
- **Success Response (200 OK)**:
  ```json
  {
    "students": [
      {
        "student_id": "22-NTU-CS-1192",
        "name": "Test Student",
        "reg_number": "22-NTU-CS-1192",
        "image_paths": ["datasets/..."]
      }
    ],
    "count": 1
  }
  ```

#### `GET /students/search/by-name`
Searches profiles using case-insensitive matching.
- **Request Parameters**:
  - `query` (Query, string): Part or full name to search for.
  - `class_name` (Query, string, optional): Class collection filter.
- **Success Response (200 OK)**:
  ```json
  {
    "results": [
      {
        "student_id": "22-NTU-CS-1192",
        "name": "Test Student"
      }
    ],
    "count": 1
  }
  ```

#### `GET /students/{student_id}`
Retrieves a specific student's profile metadata.
- **Request Parameters**:
  - `student_id` (Path, string): Registration ID.
  - `class_name` (Query, string, optional): Target class.
- **Success Response (200 OK)**:
  ```json
  {
    "student_id": "22-NTU-CS-1192",
    "name": "Test Student",
    "reg_number": "22-NTU-CS-1192",
    "image_paths": ["datasets/..."]
  }
  ```
- **Error Response (404 Not Found)**:
  ```json
  {
    "detail": "Student not found"
  }
  ```

#### `PUT /students/{student_id}`
Updates details of an existing profile.
- **Authorization**: Required (Bearer Token)
- **Request Parameters**:
  - `student_id` (Path, string): Target student registration ID.
  - `class_name` (Query, string, optional): Scoped class name.
  - **Body** (JSON): key-value dictionary representing field updates.
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Student updated successfully",
    "student_id": "22-NTU-CS-1192"
  }
  ```

#### `DELETE /students/{student_id}`
Removes a student profile from the database.
- **Authorization**: Required (Bearer Token)
- **Request Parameters**:
  - `student_id` (Path, string): Target registration ID.
  - `class_name` (Query, string, optional): Class collection.
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Student deleted successfully",
    "student_id": "22-NTU-CS-1192"
  }
  ```

---

### Attendance Module

#### `POST /attendance/mark`
Logs attendance status manually for a specific student.
- **Authorization**: Required (Bearer Token)
- **Request Parameters**:
  - `class_name` (Query, string): Targeted class name.
  - **Body** (JSON):
    ```json
    {
      "student_id": "22-NTU-CS-1192",
      "name": "Test Student",
      "status": "Present",
      "confidence": 1.0
    }
    ```
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Attendance marked successfully",
    "student_id": "22-NTU-CS-1192",
    "date": "2026-06-15T08:22:01.123Z"
  }
  ```

#### `POST /attendance/mark-from-image`
Processes an uploaded image to recognize multiple faces and log attendance dynamically.
- **Authorization**: Required (Bearer Token)
- **Content-Type**: `multipart/form-data`
- **Request Payload**:
  - `class_name` (Form, string): Target class name.
  - `file` (File): Image file containing student faces.
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Image processed successfully",
    "results": [
      {
        "face_number": 1,
        "bbox": [100, 200, 300, 400],
        "confidence": 0.89,
        "student_id": "22-NTU-CS-1192",
        "name": "Test Student",
        "status": "recognized",
        "already_marked": false,
        "message": "Attendance marked for Test Student"
      }
    ],
    "processed_by": "admin@fyp.com",
    "timestamp": "2026-06-15T08:22:01.123Z"
  }
  ```

#### `GET /attendance/`
Lists attendance logs.
- **Request Parameters**:
  - `skip` (Query, int): Offset index (Default: 0).
  - `limit` (Query, int): Max count (Default: 10).
  - `student_id` (Query, string, optional): Filter by student.
  - `date` (Query, string, optional): Filter by date (`YYYY-MM-DD`).
  - `class_name` (Query, string, optional): Filter by class.
- **Success Response (200 OK)**:
  ```json
  {
    "records": [
      {
        "_id": "69fee6...",
        "student_id": "22-NTU-CS-1192",
        "name": "Test Student",
        "date": "2026-06-15T00:00:00Z",
        "status": "Present",
        "confidence": 0.95
      }
    ],
    "count": 1
  }
  ```

#### `GET /attendance/{attendance_id}`
Retrieves a specific attendance record by record ID or student ID.
- **Authorization**: Required (Bearer Token)
- **Request Parameters**:
  - `attendance_id` (Path, string): Record ID or Student ID.
  - `class_name` (Query, string, optional): Scoped class name.
- **Success Response (200 OK)**:
  ```json
  {
    "_id": "69fee6...",
    "student_id": "22-NTU-CS-1192",
    "name": "Test Student",
    "date": "2026-06-15T00:00:00Z",
    "status": "Present",
    "confidence": 0.95
  }
  ```

#### `PUT /attendance/{attendance_id}`
Updates details of an attendance record.
- **Authorization**: Required (Bearer Token)
- **Request Parameters**:
  - `attendance_id` (Path, string): Target record ID.
  - `class_name` (Query, string, optional): Target class.
  - **Body** (JSON): Key-value fields to update (e.g. `{"status": "Absent"}`).
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Attendance updated successfully",
    "attendance_id": "69fee6..."
  }
  ```

#### `DELETE /attendance/{attendance_id}`
Deletes an attendance record.
- **Authorization**: Required (Bearer Token)
- **Request Parameters**:
  - `attendance_id` (Path, string): Target record ID.
  - `class_name` (Query, string, optional): Scoped class name.
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Attendance record deleted successfully",
    "attendance_id": "69fee6..."
  }
  ```

---

### Class Management Module

#### `POST /api/classes/create`
Initializes a new class and programmatically creates dedicated student and attendance collections for it in MongoDB.
- **Content-Type**: `application/json`
- **Request Payload**:
  ```json
  {
    "class_name": "BSCS-8B"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "message": "Class 'BSCS-8B' created successfully",
    "class_name": "BSCS-8B",
    "collection_name": "BSCS-8B",
    "created": true
  }
  ```
- **Error Response (400 Bad Request)**:
  ```json
  {
    "detail": "Class name must only contain alphanumeric characters, hyphens, underscores, or periods."
  }
  ```

---

### System & Health Endpoints

- `GET /health`: Monitor server status (`{"status": "healthy"}`).
- `GET /api/info`: Obtain base path, version, and endpoints metadata.
- `GET /test`: Connectivity handshake (`{"status": "ok", "message": "Server is running"}`).
- `GET /api`: Versioning status (`{"version": "2.0.0", "base_path": "/api/v1"}`).

---

## 4. Deep-Dive: Live Camera & WebSocket Protocol

### Overview
The frontend captures canvas frames at a regular interval (e.g., 2 frames per second) and streams them to the backend over WebSockets. The backend executes face recognition on each frame and streams back identification matches, drawing boxes, and confirmation statuses.

### `/camera` GET Endpoint
This route (`http://127.0.0.1:8000/camera`) is used to render the full camera streaming interface.
- **Query Parameters**:
  - `class_tag` (Query, string, optional): If provided, pre-selects the class collection and immediately starts the camera.
  - `class_name` (Query, string, optional): Alternative name parameter.
- **Jinja-style Injection**:
  Before rendering, the backend retrieves all MongoDB student collection names (`students-*`), resolves available class identifiers, and injects them as a JSON list into the DOM:
  ```javascript
  window.AVAILABLE_CLASSES = ["BSCS-8A", "BSCS-8B", "BSCS-8C"];
  ```

### WebSocket Protocol: `/ws/camera/{session_id}`
Connect to: `ws://127.0.0.1:8000/ws/camera/{session_id}?class_tag={chosenClass}`

#### Class Isolation Logic Flow:
1. When connecting, the frontend appends the query parameter `?class_tag=BSCS-8B` (or `?class_name=BSCS-8B`) to the connection string.
2. The backend extracts `class_tag` (or `class_name`).
3. If provided, the backend:
   - Restricts references dynamically.
   - Loads the global embedding cache `.npy` file.
   - Queries `student_crud.list_students(limit=10000, class_name=target_class)` to obtain student IDs registered under that class.
   - Filters the candidate embeddings matrix to only include vectors mapped to those IDs.
   - Queries `student_crud.get_student_by_id(..., class_name=target_class)` to display names.
   - Records attendance logs using `AttendanceCRUD(target_class)` directly inside the class attendance collection.

#### Protocol Messages (JSON):

##### 1. Client to Server - Send Frame
```json
{
  "type": "frame",
  "data": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMC...",
  "timestamp": "2026-06-15T08:22:01.123Z"
}
```
*Note: `data` is a base64 encoded JPG frame string.*

##### 2. Client to Server - Keepalive / End
- **Ping**: `{"type": "ping"}`
- **End Session**: `{"type": "end"}`

##### 3. Server to Client - Match Results
```json
{
  "type": "match_result",
  "timestamp": "2026-06-15T08:22:01.554Z",
  "faces_detected": 1,
  "newly_marked": 1,
  "marked_today": 1,
  "matches": [
    {
      "student_id": "22-NTU-CS-1192",
      "name": "Test Student",
      "confidence": 0.86,
      "bbox": [120, 240, 320, 440],
      "status": "newly_marked"
    }
  ]
}
```
*Possible `status` values in matches:*
- `"newly_marked"`: Match is positive, database attendance successfully logged.
- `"already_marked"`: Match is positive, attendance was already logged today.
- `"unknown"`: Match confidence falls below threshold (`0.6`).

##### 4. Server to Client - Pong Response
```json
{
  "type": "pong"
}
```

##### 5. Server to Client - Error Message
```json
{
  "type": "error",
  "message": "Embeddings not found"
}
```

---

## 5. Local Setup & Environment Constants

To run this backend locally, configure a `.env` file at the root:
```env
MONGO_URI=mongodb://localhost:27017/attendance_db
SECRET_KEY=yoursecretkeyhere
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Spin up backend server:
```bash
# Activate virtual environment
# Windows PowerShell:
.\myvenv313\Scripts\Activate.ps1

# Run development server
uvicorn app.main:app --reload
```
By default, the server starts up at: `http://127.0.0.1:8000`
Auto-generated swagger interactive docs can be accessed at: `http://127.0.0.1:8000/api/docs`
