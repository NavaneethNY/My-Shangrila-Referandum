from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from flask_mysqldb import MySQL
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from flask_cors import CORS
import hashlib
import os
from datetime import datetime, timedelta
from functools import wraps
import re

# -----------------------------
# App configuration
# -----------------------------
app = Flask(__name__)

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/mslr/*": {"origins": "*"}})

# Secret keys - CHANGE THESE IN PRODUCTION
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# -----------------------------
# JWT configuration (FOR REST API)
# -----------------------------
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'change-this-jwt-secret-key-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

jwt = JWTManager(app)

# -----------------------------
# MySQL Configuration
# -----------------------------
app.config['MYSQL_HOST'] = os.environ.get('DB_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD', '1234')
app.config['MYSQL_DB'] = os.environ.get('DB_NAME', 'cw2_2025')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# -----------------------------
# JWT Error Handlers
# -----------------------------
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token has expired',
        'message': 'The authentication token has expired. Please obtain a new token.'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'Invalid token',
        'message': 'The authentication token is invalid or malformed.'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'error': 'Missing authorization token',
        'message': 'Request does not contain a valid authentication token.'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token has been revoked',
        'message': 'The authentication token has been revoked.'
    }), 401


# -----------------------------
# Utility Functions
# -----------------------------
def get_password_hash(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def login_required(f):
    """Decorator for routes requiring voter login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def ec_required(f):
    """Decorator for routes requiring EC login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('ec_logged_in'):
            return redirect(url_for('ec_login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_age(dob_str):
    """Calculate age from date of birth"""
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d')
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        return 0


# -----------------------------
# Web Application Routes
# -----------------------------
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Voter registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        fullname = request.form.get('fullname', '').strip()
        dob = request.form.get('dob', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        scc = request.form.get('scc', '').strip().upper()

        # Validation
        errors = []

        if not email or not validate_email(email):
            errors.append('Please enter a valid email address.')

        if not fullname:
            errors.append('Please enter your full name.')

        if not dob:
            errors.append('Please enter your date of birth.')
        else:
            age = calculate_age(dob)
            if age < 18:
                errors.append('You must be at least 18 years old to register.')

        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if not scc:
            errors.append('Please enter your Shangri-La Citizen Code.')

        if not errors:
            cur = mysql.connection.cursor()

            # Check if email already exists
            cur.execute("SELECT voter_email FROM voters WHERE voter_email = %s", (email,))
            if cur.fetchone():
                errors.append('This email address is already registered.')

            # Check if SCC is valid and not used
            cur.execute("SELECT scc, used FROM scc_code WHERE scc = %s", (scc,))
            scc_record = cur.fetchone()

            if not scc_record:
                errors.append('Invalid Shangri-La Citizen Code.')
            elif scc_record['used'] == 1:
                errors.append('This Shangri-La Citizen Code has already been used.')

            if not errors:
                # Register the user
                password_hash = get_password_hash(password)
                cur.execute(
                    "INSERT INTO voters (voter_email, fullname, dob, passwordhash, scc) VALUES (%s, %s, %s, %s, %s)",
                    (email, fullname, dob, password_hash, scc)
                )
                # Mark SCC as used
                cur.execute("UPDATE scc_code SET used = 1 WHERE scc = %s", (scc,))
                mysql.connection.commit()
                cur.close()

                return render_template('register.html', success=True)

            cur.close()

        return render_template('register.html', errors=errors)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Voter login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT voter_email, fullname FROM voters WHERE voter_email=%s AND passwordhash=%s",
            (email, get_password_hash(password))
        )
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_email'] = user['voter_email']
            session['user_name'] = user['fullname']
            session.permanent = True
            
            resp = make_response(redirect(url_for('voter_dashboard')))
            if remember:
                resp.set_cookie('remembered_email', email, max_age=30*24*60*60)
            return resp

        return render_template('login.html', error="Invalid credentials")

    remembered_email = request.cookies.get('remembered_email', '')
    return render_template('login.html', remembered_email=remembered_email)

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/voter/dashboard')
@login_required
def voter_dashboard():
    """Voter dashboard - view and vote on referendums"""
    cur = mysql.connection.cursor()

    # Get all open referendums
    cur.execute("""
        SELECT r.referendum_id, r.referendum_title, r.referendum_desc, r.status
        FROM referendum r
        WHERE r.status = 'open'
        ORDER BY r.referendum_id DESC
    """)
    referendums = cur.fetchall()

    # For each referendum, get options and check if user has voted
    for ref in referendums:
        # Get options
        cur.execute("""
            SELECT opt_id, option_text
            FROM referendum_options
            WHERE referendum_id = %s
            ORDER BY opt_id
        """, (ref['referendum_id'],))
        ref['options'] = cur.fetchall()

        # Check if user has voted
        cur.execute("""
            SELECT voted_option_id
            FROM voter_history
            WHERE voter_email = %s AND referendum_id = %s
        """, (session['user_email'], ref['referendum_id']))
        vote = cur.fetchone()
        ref['has_voted'] = vote is not None
        ref['voted_option'] = vote['voted_option_id'] if vote else None

    # Get closed referendums user participated in
    cur.execute("""
        SELECT r.referendum_id,
            r.referendum_title,
            r.status,
            r.closed_at,
            vh.voted_option_id,
            ro.option_text as voted_option_text
        FROM referendum r
        JOIN voter_history vh ON r.referendum_id = vh.referendum_id
        JOIN referendum_options ro ON vh.voted_option_id = ro.opt_id
        WHERE vh.voter_email = %s
        AND r.status = 'closed'
        ORDER BY r.closed_at DESC
    """, (session['user_email'],))
    past_referendums = cur.fetchall()

    cur.close()

    return render_template('voter_dashboard.html', 
                         referendums=referendums, 
                         past_referendums=past_referendums)

@app.route('/voter/vote/<int:referendum_id>', methods=['POST'])
@login_required
def cast_vote(referendum_id):
    """Cast a vote"""
    option_id = request.form.get('option_id')

    if not option_id:
        return jsonify({'success': False, 'message': 'Please select an option.'}), 400

    cur = mysql.connection.cursor()

    # Check if user has already voted
    cur.execute("""
        SELECT * FROM voter_history 
        WHERE voter_email = %s AND referendum_id = %s
    """, (session['user_email'], referendum_id))

    if cur.fetchone():
        cur.close()
        return jsonify({'success': False, 'message': 'You have already voted in this referendum.'}), 400

    # Check if referendum is open
    cur.execute("SELECT status FROM referendum WHERE referendum_id = %s", (referendum_id,))
    ref = cur.fetchone()
    if not ref or ref['status'] != 'open':
        cur.close()
        return jsonify({'success': False, 'message': 'This referendum is not open for voting.'}), 400

    # Record the vote
    cur.execute("""
        INSERT INTO voter_history (voter_email, referendum_id, voted_option_id)
        VALUES (%s, %s, %s)
    """, (session['user_email'], referendum_id, option_id))

    # Check if 50% of voters have voted for this option
    cur.execute("SELECT COUNT(*) as total FROM voters")
    total_voters = cur.fetchone()['total']

    cur.execute("""
        SELECT COUNT(*) as votes 
        FROM voter_history 
        WHERE referendum_id = %s AND voted_option_id = %s
    """, (referendum_id, option_id))
    option_votes = cur.fetchone()['votes']

    # Auto-close if 50% threshold reached
    if option_votes >= (total_voters * 0.5):
        cur.execute("""
            UPDATE referendum
            SET status = 'closed',
                closed_at = NOW()
            WHERE referendum_id = %s
        """, (referendum_id,))

    mysql.connection.commit()
    cur.close()

    return jsonify({'success': True, 'message': 'Your vote has been recorded successfully!'})

@app.route('/voter/about')
@login_required
def voter_about():
    """About Us page for voters"""
    return render_template('voter_about.html')


# -----------------------------
# Election Commission Routes
# -----------------------------
@app.route('/ec/login', methods=['GET', 'POST'])
def ec_login():
    """Election Commission login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if email == 'ec@referendum.gov.sr' and password == 'Shangrilavote&2025@':
            session['ec_logged_in'] = True
            session['ec_email'] = email
            session.permanent = True
            return redirect(url_for('ec_dashboard'))
        else:
            return render_template('ec_login.html', error='Invalid credentials.')

    return render_template('ec_login.html')

@app.route('/ec/logout')
def ec_logout():
    """EC logout"""
    session.pop('ec_logged_in', None)
    session.pop('ec_email', None)
    return redirect(url_for('index'))

@app.route('/ec/dashboard')
@ec_required
def ec_dashboard():
    """Election Commission dashboard"""
    cur = mysql.connection.cursor()

    # Get all referendums with vote counts
    cur.execute("""
        SELECT referendum_id, referendum_title, referendum_desc, status, closed_at
        FROM referendum
        ORDER BY referendum_id DESC
    """)
    referendums = cur.fetchall()

    for ref in referendums:
        # Get options with vote counts
        cur.execute("""
            SELECT ro.opt_id, ro.option_text, 
                   COUNT(vh.voted_option_id) as votes
            FROM referendum_options ro
            LEFT JOIN voter_history vh ON ro.opt_id = vh.voted_option_id 
                                       AND vh.referendum_id = %s
            WHERE ro.referendum_id = %s
            GROUP BY ro.opt_id, ro.option_text
            ORDER BY ro.opt_id
        """, (ref['referendum_id'], ref['referendum_id']))
        ref['options'] = cur.fetchall()

        # Calculate total votes and percentages
        ref['total_votes'] = sum(opt['votes'] for opt in ref['options'])
        for opt in ref['options']:
            if ref['total_votes'] > 0:
                opt['percentage'] = round((opt['votes'] / ref['total_votes']) * 100, 1)
            else:
                opt['percentage'] = 0

    # Get total registered voters
    cur.execute("SELECT COUNT(*) as total FROM voters")
    total_voters = cur.fetchone()['total']

    # Get voter statistics
    cur.execute("SELECT COUNT(DISTINCT voter_email) as active FROM voter_history")
    active_voters = cur.fetchone()['active']

    cur.close()

    return render_template('ec_dashboard.html', 
                         referendums=referendums,
                         total_voters=total_voters,
                         active_voters=active_voters)

@app.route('/ec/referendum/create', methods=['GET', 'POST'])
@ec_required
def create_referendum():
    """Create new referendum"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        options = request.form.getlist('options[]')

        errors = []
        if not title:
            errors.append('Please enter a referendum title.')
        if not description:
            errors.append('Please enter a referendum description.')
        if len(options) < 2:
            errors.append('Please enter at least 2 options.')

        options = [opt.strip() for opt in options if opt.strip()]

        if not errors:
            cur = mysql.connection.cursor()

            # Insert referendum (starts as closed)
            cur.execute("""
                INSERT INTO referendum (referendum_title, referendum_desc, status)
                VALUES (%s, %s, 'closed')
            """, (title, description))

            referendum_id = cur.lastrowid

            # Insert options
            for option in options:
                cur.execute("""
                    INSERT INTO referendum_options (referendum_id, option_text)
                    VALUES (%s, %s)
                """, (referendum_id, option))

            mysql.connection.commit()
            cur.close()

            return redirect(url_for('ec_dashboard'))

        return render_template('create_referendum.html', errors=errors)

    return render_template('create_referendum.html')

@app.route('/ec/referendum/<int:referendum_id>/toggle', methods=['POST'])
@ec_required
def toggle_referendum_status(referendum_id):
    """Open or close a referendum"""
    cur = mysql.connection.cursor()

    cur.execute("SELECT status FROM referendum WHERE referendum_id = %s", (referendum_id,))
    ref = cur.fetchone()

    if ref:
        if ref['status'] == 'open':
            # Close referendum
            cur.execute("""
                UPDATE referendum
                SET status = 'closed',
                    closed_at = NOW()
                WHERE referendum_id = %s
            """, (referendum_id,))
        else:
            # Open referendum
            cur.execute("""
                UPDATE referendum
                SET status = 'open',
                    closed_at = NULL
                WHERE referendum_id = %s
            """, (referendum_id,))

        mysql.connection.commit()

    cur.close()
    return redirect(url_for('ec_dashboard'))

@app.route('/ec/referendum/<int:referendum_id>/edit', methods=['GET', 'POST'])
@ec_required
def edit_referendum(referendum_id):
    """Edit a referendum (only if never opened)"""
    cur = mysql.connection.cursor()
    
    # Get referendum details
    cur.execute("""
        SELECT referendum_id, referendum_title, referendum_desc, status
        FROM referendum WHERE referendum_id = %s
    """, (referendum_id,))
    referendum = cur.fetchone()
    
    if not referendum:
        cur.close()
        return redirect(url_for('ec_dashboard'))
    
    # Check if referendum has votes (has been opened)
    cur.execute("""
        SELECT COUNT(*) as vote_count
        FROM voter_history
        WHERE referendum_id = %s
    """, (referendum_id,))
    vote_count = cur.fetchone()['vote_count']
    
    # If referendum has votes, it cannot be edited
    if vote_count > 0:
        cur.close()
        return render_template('edit_referendum.html', 
                             referendum=referendum, 
                             error='Cannot edit referendum that has received votes.')
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        options = request.form.getlist('options[]')
        
        errors = []
        if not title:
            errors.append('Please enter a referendum title.')
        if not description:
            errors.append('Please enter a referendum description.')
        if len(options) < 2:
            errors.append('Please enter at least 2 options.')
        
        options = [opt.strip() for opt in options if opt.strip()]
        
        if not errors:
            # Update referendum
            cur.execute("""
                UPDATE referendum 
                SET referendum_title = %s, referendum_desc = %s
                WHERE referendum_id = %s
            """, (title, description, referendum_id))
            
            # Delete old options
            cur.execute("DELETE FROM referendum_options WHERE referendum_id = %s", (referendum_id,))
            
            # Insert new options
            for option in options:
                cur.execute("""
                    INSERT INTO referendum_options (referendum_id, option_text)
                    VALUES (%s, %s)
                """, (referendum_id, option))
            
            mysql.connection.commit()
            cur.close()
            
            return redirect(url_for('ec_dashboard'))
        
        referendum['errors'] = errors
    
    # Get current options
    cur.execute("""
        SELECT opt_id, option_text
        FROM referendum_options
        WHERE referendum_id = %s
        ORDER BY opt_id
    """, (referendum_id,))
    referendum['options'] = cur.fetchall()
    
    cur.close()
    
    return render_template('edit_referendum.html', referendum=referendum)

@app.route('/ec/referendum/<int:referendum_id>/delete', methods=['POST'])
@ec_required
def delete_referendum(referendum_id):
    """Delete a referendum (only if no votes)"""
    cur = mysql.connection.cursor()
    
    # Check if referendum has votes
    cur.execute("""
        SELECT COUNT(*) as vote_count
        FROM voter_history
        WHERE referendum_id = %s
    """, (referendum_id,))
    vote_count = cur.fetchone()['vote_count']
    
    if vote_count == 0:
        # Delete referendum (cascade will delete options)
        cur.execute("DELETE FROM referendum WHERE referendum_id = %s", (referendum_id,))
        mysql.connection.commit()
    
    cur.close()
    
    return redirect(url_for('ec_dashboard'))

@app.route('/ec/voters')
@ec_required
def view_voters():
    """View all registered voters with pagination and search"""
    cur = mysql.connection.cursor()
    
    # Get search query and page number
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    # Base query for counting total voters
    if search_query:
        count_sql = """
            SELECT COUNT(*) as total
            FROM voters v
            WHERE v.voter_email LIKE %s 
            OR v.fullname LIKE %s
            OR v.scc LIKE %s
        """
        search_pattern = f"%{search_query}%"
        cur.execute(count_sql, (search_pattern, search_pattern, search_pattern))
    else:
        cur.execute("SELECT COUNT(*) as total FROM voters")
    
    total_voters = cur.fetchone()['total']
    total_pages = (total_voters + per_page - 1) // per_page
    
    # Query to get voters with pagination
    if search_query:
        voters_sql = """
            SELECT v.voter_email, v.fullname, v.dob, v.scc, v.created_at,
                COUNT(vh.id) as votes_cast
            FROM voters v
            LEFT JOIN voter_history vh ON v.voter_email = vh.voter_email
            WHERE v.voter_email LIKE %s 
            OR v.fullname LIKE %s
            OR v.scc LIKE %s
            GROUP BY v.voter_email, v.fullname, v.dob, v.scc, v.created_at
            ORDER BY v.created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(voters_sql, (search_pattern, search_pattern, search_pattern, per_page, offset))
    else:
        voters_sql = """
            SELECT v.voter_email, v.fullname, v.dob, v.scc, v.created_at,
                   COUNT(vh.id) as votes_cast
            FROM voters v
            LEFT JOIN voter_history vh ON v.voter_email = vh.voter_email
            GROUP BY v.voter_email, v.fullname, v.dob, v.scc, v.created_at
            ORDER BY v.created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(voters_sql, (per_page, offset))
    
    voters = cur.fetchall()
    
    # Get SCC usage statistics
    cur.execute("""
        SELECT 
            COUNT(*) as total_codes,
            SUM(used) as used_codes
        FROM scc_code
    """)
    scc_stats = cur.fetchone()
    
    # Get all voters count for statistics
    cur.execute("SELECT COUNT(*) as total FROM voters")
    all_voters_count = cur.fetchone()['total']
    
    # Get active voters count
    cur.execute("SELECT COUNT(DISTINCT voter_email) as active FROM voter_history")
    active_voters_count = cur.fetchone()['active']
    
    cur.close()
    
    return render_template('view_voters.html', 
                         voters=voters,
                         total_voters=all_voters_count,
                         active_voters=active_voters_count,
                         inactive_voters=all_voters_count - active_voters_count,
                         scc_stats=scc_stats,
                         page=page,
                         total_pages=total_pages,
                         search_query=search_query,
                         per_page=per_page)


# -----------------------------
# REST API Routes (JWT PROTECTED)
# -----------------------------
@app.route('/api/token', methods=['POST'])
def api_token():
    """
    Generate JWT access token for API authentication
    
    Request body:
    {
        "email": "ec@referendum.gov.sr",
        "password": "Shangrilavote&2025@"
    }
    
    Response:
    {
        "access_token": "eyJ...",
        "token_type": "Bearer",
        "expires_in": 7200
    }
    """
    if not request.is_json:
        return jsonify({
            'error': 'Invalid request',
            'message': 'Content-Type must be application/json'
        }), 400
    
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            'error': 'Missing credentials',
            'message': 'Email and password are required'
        }), 400

    # Authenticate EC credentials (only EC can access API)
    if email == 'ec@referendum.gov.sr' and password == 'Shangrilavote&2025@':
        # Create JWT token with additional claims
        additional_claims = {
            'role': 'election_commission',
            'permissions': ['read', 'write', 'admin']
        }
        
        access_token = create_access_token(
            identity=email,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 7200  # 2 hours in seconds
        }), 200

    return jsonify({
        'error': 'Invalid credentials',
        'message': 'The provided email or password is incorrect'
    }), 401

@app.route('/mslr/referendums', methods=['GET'])
@jwt_required()
def api_get_referendums():
    """
    Get all referendums filtered by status
    
    Query parameters:
    - status: 'open' or 'closed' (default: 'open')
    
    Example: GET /mslr/referendums?status=open
    
    Response format matches coursework specification
    """
    # Verify JWT identity
    current_user = get_jwt_identity()
    claims = get_jwt()
    
    # Get status parameter (default to 'open')
    status = request.args.get('status', 'open').lower()
    
    if status not in ['open', 'closed']:
        return jsonify({
            'error': 'Invalid status',
            'message': 'Status must be either "open" or "closed"'
        }), 400
    
    cur = mysql.connection.cursor()

    # Get referendums by status
    cur.execute("""
        SELECT referendum_id, referendum_title, referendum_desc, status
        FROM referendum 
        WHERE status = %s
        ORDER BY referendum_id DESC
    """, (status,))
    referendums = cur.fetchall()

    result = []
    for ref in referendums:
        # Get options with vote counts
        cur.execute("""
            SELECT ro.opt_id, ro.option_text, COUNT(vh.id) AS votes
            FROM referendum_options ro
            LEFT JOIN voter_history vh ON ro.opt_id = vh.voted_option_id
            WHERE ro.referendum_id = %s
            GROUP BY ro.opt_id, ro.option_text
            ORDER BY ro.opt_id
        """, (ref['referendum_id'],))
        options = cur.fetchall()

        # Format according to specification
        result.append({
            "referendum_id": str(ref['referendum_id']),
            "status": ref['status'],
            "referendum_title": ref['referendum_title'],
            "referendum_desc": ref['referendum_desc'],
            "referendum_options": {
                "options": [
                    {
                        str(o['opt_id']): o['option_text'],
                        "votes": str(o['votes'])
                    }
                    for o in options
                ]
            }
        })

    cur.close()
    return jsonify({"Referendums": result}), 200

@app.route('/mslr/referendum/<int:referendum_id>', methods=['GET'])
@jwt_required()
def api_get_referendum(referendum_id):
    """
    Get specific referendum by ID
    
    Example: GET /mslr/referendum/1
    
    Response format matches coursework specification
    """
    # Verify JWT identity
    current_user = get_jwt_identity()
    
    cur = mysql.connection.cursor()
    
    # Get referendum details
    cur.execute("""
        SELECT referendum_id, referendum_title, referendum_desc, status
        FROM referendum 
        WHERE referendum_id = %s
    """, (referendum_id,))
    ref = cur.fetchone()

    if not ref:
        cur.close()
        return jsonify({
            'error': 'Not found',
            'message': f'Referendum with ID {referendum_id} does not exist'
        }), 404

    # Get options with vote counts
    cur.execute("""
        SELECT ro.opt_id, ro.option_text, COUNT(vh.id) AS votes
        FROM referendum_options ro
        LEFT JOIN voter_history vh ON ro.opt_id = vh.voted_option_id
        WHERE ro.referendum_id = %s
        GROUP BY ro.opt_id, ro.option_text
        ORDER BY ro.opt_id
    """, (referendum_id,))
    options = cur.fetchall()
    cur.close()

    # Format according to specification
    return jsonify({
        "referendum_id": str(ref['referendum_id']),
        "status": ref['status'],
        "referendum_title": ref['referendum_title'],
        "referendum_desc": ref['referendum_desc'],
        "referendum_options": {
            "options": [
                {
                    str(o['opt_id']): o['option_text'],
                    "votes": str(o['votes'])
                }
                for o in options
            ]
        }
    }), 200

@app.route('/api/voter-stats', methods=['GET'])
@ec_required
def get_voter_stats():
    """
    API: Get voter activity statistics (Session protected for internal use)
    
    Response:
    {
        "total_voters": 150,
        "active_voters": 120,
        "inactive_voters": 30
    }
    """
    cur = mysql.connection.cursor()
    
    # Get total voters
    cur.execute("SELECT COUNT(*) as total FROM voters")
    total = cur.fetchone()['total']
    
    # Get active voters (those who have cast at least one vote)
    cur.execute("SELECT COUNT(DISTINCT voter_email) as active FROM voter_history")
    active = cur.fetchone()['active']
    
    cur.close()
    
    return jsonify({
        'total_voters': total,
        'active_voters': active,
        'inactive_voters': total - active
    }), 200

@app.route('/mslr/voter-stats', methods=['GET'])
@jwt_required()
def api_get_voter_stats_jwt():
    """
    REST API: Get voter activity statistics (JWT protected for external API)
    
    Response:
    {
        "total_voters": 150,
        "active_voters": 120,
        "inactive_voters": 30
    }
    """
    current_user = get_jwt_identity()
    
    cur = mysql.connection.cursor()
    
    # Get total voters
    cur.execute("SELECT COUNT(*) as total FROM voters")
    total = cur.fetchone()['total']
    
    # Get active voters (those who have cast at least one vote)
    cur.execute("SELECT COUNT(DISTINCT voter_email) as active FROM voter_history")
    active = cur.fetchone()['active']
    
    cur.close()
    
    return jsonify({
        'total_voters': total,
        'active_voters': active,
        'inactive_voters': total - active
    }), 200


# -----------------------------
# Error Handlers
# -----------------------------
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/') or request.path.startswith('/mslr/'):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested endpoint does not exist'
        }), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/') or request.path.startswith('/mslr/'):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)