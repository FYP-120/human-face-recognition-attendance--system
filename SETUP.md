# Local Environment & MongoDB Setup Guide - Backend

This guide outlines the step-by-step procedure to configure and run the Face Recognition Attendance System Backend on a local PC, including the installation and configuration of MongoDB.

---

## 1. System Prerequisites

Before proceeding, ensure your local environment contains the following tools:
- **Python**: Version **3.10 to 3.13** (ensure Python is added to the system environment variables PATH).
- **Git**: For version control cloning.
- **C++ Compilation Tools** (Windows only): Necessary to build the `insightface` package.
  - Download and install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
  - During installation, check the workload **"Desktop development with C++"** and complete the installation.

---

## 2. MongoDB Installation & Configuration

The application uses MongoDB to persist student records, logs, and user credentials. Follow these instructions to set it up locally:

### Step 2.1: Download MongoDB Community Server
1. Go to the [MongoDB Download Center](https://www.mongodb.com/try/download/community).
2. Select your OS (e.g., Windows), package type (MSI), and click **Download**.

### Step 2.2: Install MongoDB
1. Double-click the downloaded `.msi` installation package.
2. Accept the license agreement and select the **Complete** installation type.
3. Check the box **"Run service as Network Service user"** to register MongoDB as a background system service (highly recommended). This ensures MongoDB starts automatically when your PC boots.
4. Leave the default data and log directories as is.
5. Check the box to install **MongoDB Compass** (a graphical user interface for viewing databases) and click install.

### Step 2.3: Verify MongoDB Service is Active
- **On Windows**:
  1. Open the search menu and type `services.msc`, then press Enter.
  2. Scroll down to find the service named **MongoDB Server (MongoDB)**.
  3. Ensure its status is **Running**. If not, right-click and select **Start**.
  4. Alternatively, open PowerShell/Command Prompt as administrator and run:
     ```cmd
     net start MongoDB
     ```
- **On macOS/Linux** (if using Homebrew):
  ```bash
  brew services start mongodb-community@7.0
  ```

### Step 2.4: Verify Connection using MongoDB Compass
1. Launch **MongoDB Compass**.
2. Set the connection string input to:
   ```text
   mongodb://localhost:27017/
   ```
3. Click **Connect**. If successful, you will see a list of default system databases (`admin`, `config`, `local`). The application will dynamically create the `attendance_db` database and its relevant collections on startup.

---

## 3. Backend Local Setup & Installation

### Step 3.1: Navigate to Backend Path
Open a terminal (e.g., PowerShell on Windows) and navigate to the backend folder:
```bash
cd "e:\Umair Folder\FYP\FYP-Backend"
```

### Step 3.2: Create and Activate Python Virtual Environment
Creating a virtual environment ensures dependencies do not conflict with system-wide python packages.
```bash
# Create virtual environment named 'myvenv313'
python -m venv myvenv313

# Activate virtual environment
# Windows PowerShell:
.\myvenv313\Scripts\Activate.ps1
# Windows CMD:
.\myvenv313\Scripts\activate.bat
# Linux / macOS:
source myvenv313/bin/activate
```

### Step 3.3: Install Packages & Dependencies
Ensure your virtual environment is active (you will see `(myvenv313)` prefix in the terminal) and run:
```bash
# Upgrade installation utilities
python -m pip install --upgrade pip setuptools wheel

# Install all packages from requirements.txt
pip install -r requirements.txt
```
*Note: If the `insightface` installation fails, verify that you have successfully installed the Visual Studio Build Tools with C++ workloads.*

### Step 3.4: Configure Environment Variables
Create a file named `.env` at the root of the `FYP-Backend` folder:
```env
MONGO_URI=mongodb://localhost:27017/attendance_db
SECRET_KEY=yoursecretkeyhere
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 3.5: Run the Development Server
With the virtual environment active and MongoDB running, run the following command to start the FastAPI server:
```bash
uvicorn app.main:app --reload
```
- The backend starts at: `http://127.0.0.1:8000`
- Interactive API Docs are served at: `http://127.0.0.1:8000/api/docs`
- On initial startup, the backend automatically seeds the database with the default super admin credentials:
  - **Email**: `admin@fyp.com`
  - **Password**: `admin123`
