# My Shangri-La Referendum (MSLR)

## Project Overview

MSLR (My Shangri-La Referendum) is a comprehensive web application for managing referendums with **JWT-protected REST API**. This implementation achieves requirements including:

 **Secure RESTful services with JWT authentication**  
 **AJAX form validation with detailed messages**  
 **QR Code scanning for SCC autofill**  
 **Chart.js visualizations**  
 **Cookie-based "Remember Me" functionality**  
 **Comprehensive error handling**  
 **Responsive Bootstrap 5 design**  

---

## Technology Stack

- **Backend**: Python with Flask Framework
- **Database**: MySQL Workbench
- **Authentication**: 
  - Session-based (Web App)
  - JWT tokens (REST API)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js
- **Security**: SHA-256 password hashing, CSRF protection
- **API**: RESTful with JWT Bearer token authentication

---

## Installation & Deployment Guide

### Prerequisites

Before starting, ensure you have:
- Python 3.8 or higher
- MySQL Workbench
- pip (Python package manager)
- Web browser (Chrome, Firefox, Safari, or Edge)

### Step 1: Extract Project Files

```bash
# Extract the ZIP file
unzip CW2_abc123.zip
cd CW2_abc123
```

Your project structure should look like:
```
CW2_abc123/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── referendum_fixed.sql        # Database schema
├── README.md                   # This file
├── templates/                  # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── voter_dashboard.html
│   ├── ec_login.html
│   ├── ec_dashboard.html
│   ├── create_referendum.html
│   ├── edit_referendum.html
│   ├── view_voters.html
│   └── voter_about.html
├── static/                     # Static files
│   └── images/│       
└── qrcodes/                    # QR codes for SCC
```

### Step 3: Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Windows:
.\venv\Scripts\Activate
```

---

### Step 4: Install Python Dependencies

```bash
# Upgrade PIP
python -m pip install --upgrade pip

# Make sure virtual environment is activated
pip install -r requirements.txt
```


**Option B: MySQL Workbench**

1. Open MySQL Workbench
2. Create new database: `cw2_2025`
3. Import the file: `referendum_fixed.sql`
4. Verify all tables are created

#### 5.3 Verify Database Setup

```sql
USE cw2_2025;

-- Check all tables exist
SHOW TABLES;
-- Should show: referendum, referendum_options, scc_code, voters, voter_history

-- Check sample data
SELECT * FROM referendum;
SELECT COUNT(*) FROM scc_code;
SELECT * FROM voters LIMIT 5;

EXIT;
```

---

### Step 6: Configure Application

Edit `app.py` and update your MySQL credentials (lines 37-41):

```python
app.config['MYSQL_HOST'] = os.environ.get('DB_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD', '1234')  # Mysql Workbench Credentials
app.config['MYSQL_DB'] = os.environ.get('DB_NAME', 'cw2_2025')
```

**Important: Change these secret keys for production:**

Lines 22 and 28:
```python
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'change-this-jwt-secret-key-in-production')
```

---

### Step 7: Run the Application

```bash
# Make sure virtual environment is activated

python app.py
```

** Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
Press CTRL+C to quit
```

**The application is now running at:** `http://localhost:5000`

---

## Application Usage Guide

### Web Application URLs

| URL | Description | Access |
|-----|-------------|--------|
| `http://localhost:5000/` | Home page | Public |
| `http://localhost:5000/register` | Voter registration | Public |
| `http://localhost:5000/login` | Voter login | Public |
| `http://localhost:5000/voter/dashboard` | Voter dashboard | Logged-in voters |
| `http://localhost:5000/ec/login` | EC login | Public |
| `http://localhost:5000/ec/dashboard` | EC dashboard | Logged-in EC |
| `http://localhost:5000/ec/voters` | View all voters | Logged-in EC |

### Default Login Credentials

**Election Commission Account:**
- **Email**: `ec@referendum.gov.sr`
- **Password**: `Shangrilavote&2025@`

**Valid SCC Codes** (For new voter registration):
```
1AZN0FXJVM    JOV50TOSYR    SDUBJ5IOYB    YFUVLYBQZR
IGBQET8OOY    R2ZHBUYO2V    Z9HOC1LF4X    9IJKHGHJK4
N5J53QK9FO    ZDN06T01V9    4XRDN9O4AW    921664ML8D
A546AKU16A    V0GB2G690L    12EOU5RGVX    0IXYCAH8UW
GKJ3K1YBGE    46HJV9KH1F    S6K3AV3IVR    IKKSZYJTSH
```

---

## REST API Documentation

### Authentication Flow

The API uses **JWT (JSON Web Token)** authentication for secure access.

#### Step 1: Obtain Access Token

**Endpoint:** `POST /api/token`

**Request:**
```bash
curl -X POST http://localhost:5000/api/token \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ec@referendum.gov.sr",
    "password": "Shangrilavote&2025@"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcwNjI4NDgwMCwianRpIjoiYWJjZGVmMTIzNDU2IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImVjQHJlZmVyZW5kdW0uZ292LnNyIiwibmJmIjoxNzA2Mjg0ODAwLCJjc3JmIjoiYWJjZGVmMTIzNDU2IiwiZXhwIjoxNzA2MjkyMDAwLCJyb2xlIjoiZWxlY3Rpb25fY29tbWlzc2lvbiIsInBlcm1pc3Npb25zIjpbInJlYWQiLCJ3cml0ZSIsImFkbWluIl19.signature_here",
  "token_type": "Bearer",
  "expires_in": 7200
}
```

**Token expires in 2 hours (7200 seconds)**

---

### API Endpoints

All API endpoints require the JWT token in the Authorization header:
```
Authorization: Bearer {your_access_token}
```

#### 1. Get All Referendums by Status

**Endpoint:** `GET /mslr/referendums?status={open|closed}`

**Example Request:**
```bash
# Replace YOUR_TOKEN with actual token
curl -X GET "http://localhost:5000/mslr/referendums?status=open" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "Referendums": [
    {
      "referendum_id": "1",
      "status": "open",
      "referendum_title": "Should Shangri-La pursue an expansion...",
      "referendum_desc": "This referendum seeks to determine...",
      "referendum_options": {
        "options": [
          {
            "1": "Expand its boundaries to include all adjacent counties",
            "votes": "15"
          },
          {
            "2": "Remain status quo",
            "votes": "30"
          }
        ]
      }
    }
  ]
}
```

#### 2. Get Specific Referendum by ID

**Endpoint:** `GET /mslr/referendum/{referendum_id}`

**Example Request:**
```bash
curl -X GET "http://localhost:5000/mslr/referendum/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "referendum_id": "1",
  "status": "open",
  "referendum_title": "Should Shangri-La pursue an expansion...",
  "referendum_desc": "This referendum seeks to determine...",
  "referendum_options": {
    "options": [
      {
        "1": "Expand its boundaries to include all adjacent counties",
        "votes": "15"
      },
      {
        "2": "Remain status quo",
        "votes": "30"
      }
    ]
  }
}
```

#### 3. Get Voter Statistics

**Endpoint:** `GET /mslr/voter-stats`

**Example Request:**
```bash
curl -X GET "http://localhost:5000/mslr/voter-stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_voters": 150,
  "active_voters": 120,
  "inactive_voters": 30
}
```

---

### Testing the API with Postman

1. **Get Token:**
   - Method: POST
   - URL: `http://localhost:5000/api/token`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
   ```json
   {
     "email": "ec@referendum.gov.sr",
     "password": "Shangrilavote&2025@"
   }
   ```
   - Copy the `access_token` from response

2. **Test API Endpoints:**
   - Method: GET
   - URL: `http://localhost:5000/mslr/referendums?status=open`
   - Headers: `Authorization: Bearer {paste_token_here}`
   - Send request

---

## Features Implemented

### Task 1 - Website

 **Voter Registration**
- Email validation with regex
- SCC code validation against database
- QR code scanning support (HTML5-QRCode library)
- Age verification (18+)
- Password strength validation
- Duplicate email prevention
- Real-time AJAX validation
- SHA-256 password hashing

 **Voter Dashboard**
- View all open referendums
- Cast votes with single-click
- One vote per referendum enforcement
- Vote confirmation messages
- View past referendum participation
- Responsive card-based layout
- Auto-refresh on vote cast

 **Election Commission Dashboard**
- View all referendums with statistics
- Create new referendums
- Edit referendums (only if no votes)
- Delete referendums (only if no votes)
- Open/close referendum status toggle
- Auto-close at 50% threshold
- Chart.js visualizations
- View all registered voters with:
  - Pagination (10 per page)
  - Search functionality
  - SCC usage statistics
  - Activity charts

### Task 2 - REST API

 **JWT Authentication**
- OAuth2-style token endpoint
- Secure Bearer token authentication
- Token expiration (2 hours)
- Comprehensive error handling

 **API Endpoints**
- `POST /api/token` - Get JWT access token
- `GET /mslr/referendums?status={open|closed}` - Get referendums
- `GET /mslr/referendum/{id}` - Get specific referendum
- `GET /mslr/voter-stats` - Get voter statistics (bonus)

---
