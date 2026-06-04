from flask import Flask, render_template, request, session, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "career_secret_key"

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'career_guidance'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"DB Error: {e}")
        return None

def predict_cutoff(history):
    if not history:
        return 0
    y = [float(h) for h in history]
    n = len(y)
    if n < 2:
        return round(y[0] + 1.0, 2)
    x = list(range(n))
    sum_x, sum_y = sum(x), sum(y)
    sum_xx = sum(i*i for i in x)
    sum_xy = sum(i*j for i, j in zip(x, y))
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return round(y[-1] + 1.0, 2)
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return min(200.0, round(slope * n + intercept + 1.0, 2))

def get_db_category(career):
    """Maps assessment recommendations to database college categories."""
    mapping = {
        'Engineering': 'Engineering',
        'Medical': 'Medical',
        'Agriculture': 'Agriculture',
        'Law': 'Law',
        'Arts': 'Arts & Science',
        'Commerce': 'Arts & Science',
        'Management': 'Arts & Science',
        'Science': 'Arts & Science',
        'Arts_Commerce': 'Arts & Science',
        'Government_Service': 'Government_Service'
    }
    return mapping.get(career, 'Arts & Science')

@app.route("/")
def home():
    demo_completed = False
    if "user_id" in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM demographics WHERE user_id=%s", (session['user_id'],))
        if cursor.fetchone():
            demo_completed = True
        cursor.close(); conn.close()
    return render_template('home.html', demo_completed=demo_completed)

@app.route("/register", methods=["GET","POST"])
def register():
    if "user_id" in session:
        return redirect(url_for('home'))
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        if not conn: return "DB Error"
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("INSERT INTO users (name, email, password, is_admin) VALUES (%s, %s, %s, 0)", (name, email, password))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            if user:
                session["user_id"] = user["id"]
                session["is_admin"] = user["is_admin"]
                session["user_name"] = user["name"]
                flash("Registered successfully! Please complete your demographics.", "success")
                return redirect(url_for('demographics'))
        except Error as e:
            flash(f"Error: {e}", "danger")
        finally:
            cursor.close(); conn.close()
    return render_template('register.html')

@app.route("/login", methods=["GET","POST"])
def login():
    if "user_id" in session:
        return redirect(url_for('home'))
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        if not conn: return "DB Error"
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email,password))
        user = cursor.fetchone()
        cursor.close(); conn.close()
        if user:
            session["user_id"] = user["id"]
            session["is_admin"] = user["is_admin"]
            session["user_name"] = user["name"]
            return redirect(url_for('home'))
        flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/demographics", methods=["GET", "POST"])
def demographics():
    if "user_id" not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()

    if request.method == "POST":
        f = request.form
        data = {
            "dob": f.get("dob"),
            "gender": f.get("gender"),
            "district": f.get("district"),
            "category": f.get("category"),
            "religion": f.get("religion"),
            "board": f.get("board"),
            "education_level": f.get("education_level"),
            "stream": f.get("stream"),
            "language_1": float(f.get("language1") or 0),
            "language_2": float(f.get("language2") or 0),
            "physics": float(f.get("physics") or 0),
            "chemistry": float(f.get("chemistry") or 0),
            "maths": float(f.get("maths") or 0),
            "botany": float(f.get("botany") or 0),
            "zoology": float(f.get("zoology") or 0),
            "biology": float(f.get("biology") or 0),
            "computer_science": float(f.get("computer_science") or 0),
            "economics": float(f.get("economics") or 0),
            "accountancy": float(f.get("accountancy") or 0),
            "commerce_subject": float(f.get("commerce_subject") or 0),
            "computer_applications": float(f.get("computer_applications") or 0),
            "science": float(f.get("science") or 0),
            "social_science": float(f.get("social_science") or 0),
            "total_marks": float(f.get("total_marks") or 0),
            "max_marks": float(f.get("max_marks") or 0)
        }

        p, c, m, b = data["physics"], data["chemistry"], data["maths"], data["biology"]
        bot, zoo = data["botany"], data["zoology"]
        
        data["cutoff_engineering"] = round(m + (p + c) / 2.0, 2)
        
        main_bio = b if b > 0 else (bot + zoo) / 2.0
        data["cutoff_medical"] = round(main_bio + (p + c) / 2.0, 2)
        data["cutoff_agriculture"] = round(main_bio + (p + c) / 2.0, 2)
        
        if data["max_marks"] > 0:
            data["cutoff_law_arts"] = round((data["total_marks"] / data["max_marks"]) * 200.0, 2)
        else:
            data["cutoff_law_arts"] = 0

        data["cutoff"] = data["cutoff_engineering"] if data["education_level"] == "12th" else 0

        try:
            if demo:
                cursor.execute("""
                    UPDATE demographics SET 
                        dob=%s, gender=%s, district=%s, category=%s, religion=%s,
                        board=%s, education_level=%s, stream=%s,
                        language_1=%s, language_2=%s, physics=%s, chemistry=%s, maths=%s,
                        botany=%s, zoology=%s, biology=%s, computer_science=%s, economics=%s, accountancy=%s, 
                        commerce_subject=%s, computer_applications=%s, science=%s, social_science=%s,
                        total_marks=%s, max_marks=%s, cutoff=%s, cutoff_engineering=%s,
                        cutoff_medical=%s, cutoff_agriculture=%s, cutoff_law_arts=%s
                    WHERE user_id=%s
                """, (
                    data["dob"], data["gender"], data["district"], data["category"], data["religion"],
                    data["board"], data["education_level"], data["stream"],
                    data["language_1"], data["language_2"], data["physics"], data["chemistry"], data["maths"],
                    data["botany"], data["zoology"], data["biology"], data["computer_science"], data["economics"], data["accountancy"],
                    data["commerce_subject"], data["computer_applications"], data["science"], data["social_science"],
                    data["total_marks"], data["max_marks"], data["cutoff"], data["cutoff_engineering"],
                    data["cutoff_medical"], data["cutoff_agriculture"], data["cutoff_law_arts"],
                    session['user_id']
                ))
            else:
                cursor.execute("""
                    INSERT INTO demographics
                    (user_id, dob, gender, district, category, religion, board, education_level, stream,
                     language_1, language_2, physics, chemistry, maths, botany, zoology, biology,
                     computer_science, economics, accountancy, commerce_subject, computer_applications,
                     science, social_science, total_marks, max_marks, cutoff, cutoff_engineering, 
                     cutoff_medical, cutoff_agriculture, cutoff_law_arts)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    session['user_id'], data["dob"], data["gender"], data["district"], data["category"], 
                    data["religion"], data["board"], data["education_level"], data["stream"],
                    data["language_1"], data["language_2"], data["physics"], data["chemistry"], data["maths"],
                    data["botany"], data["zoology"], data["biology"], data["computer_science"], data["economics"], data["accountancy"],
                    data["commerce_subject"], data["computer_applications"], data["science"], data["social_science"],
                    data["total_marks"], data["max_marks"], data["cutoff"], data["cutoff_engineering"],
                    data["cutoff_medical"], data["cutoff_agriculture"], data["cutoff_law_arts"]
                ))
            conn.commit()
            flash("Demographics saved successfully!", "success")
            return redirect(url_for('demographics'))
        except Error as e:
            flash(f"Error saving demographics: {e}", "danger")
        finally:
            cursor.close(); conn.close()
    
    edit_mode = request.args.get('edit', 'false').lower() == 'true'
    if not demo:
        edit_mode = True

    cursor.close(); conn.close()
    user_name = session.get('user_name', '')
    return render_template("demographics.html", demo=demo, edit_mode=edit_mode, user_name=user_name)

@app.route("/assessment")
def assessment():
    if "user_id" not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT education_level FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()
    cursor.close(); conn.close()
    
    if not demo:
        flash("Please complete demographics first.", "warning")
        return redirect(url_for('demographics'))
    
    if demo['education_level'] == '10th':
        return redirect(url_for('assessment_10th'))
    else:
        return redirect(url_for('assessment_12th'))

@app.route("/assessment_10th", methods=["GET","POST"])
def assessment_10th():
    if "user_id" not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == "POST":
        scores = {}
        for key, val in request.form.items():
            if key.startswith("q_") and val == "Yes":
                q_id = key.split("_")[1]
                cursor.execute("SELECT category, weight FROM questions WHERE id=%s", (q_id,))
                q = cursor.fetchone()
                if q:
                    scores[q['category']] = scores.get(q['category'], 0) + q['weight']
        
        recommendation = max(scores, key=scores.get) if scores else "General"
        cursor.execute("DELETE FROM student_results WHERE user_id=%s AND grade_level='10th'", (session['user_id'],))
        cursor.execute("INSERT INTO student_results (user_id, grade_level, recommended_stream_or_career) VALUES (%s, '10th', %s)",
                       (session['user_id'], recommendation))
        conn.commit()
        cursor.close(); conn.close()
        return redirect(url_for('career_results'))

    cursor.execute("SELECT * FROM questions WHERE grade_level='10th'")
    questions = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template("assessment_10th.html", questions=questions)

@app.route("/assessment_12th", methods=["GET","POST"])
def assessment_12th():
    if "user_id" not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT stream FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()
    stream = demo['stream'] if demo else 'All'
    
    if request.method == "POST":
        scores = {}
        for key, val in request.form.items():
            if key.startswith("q_") and val == "Yes":
                q_id = key.split("_")[1]
                cursor.execute("SELECT category, weight FROM questions WHERE id=%s", (q_id,))
                q = cursor.fetchone()
                if q:
                    scores[q['category']] = scores.get(q['category'], 0) + q['weight']
        
        recommendation = max(scores, key=scores.get) if scores else "Engineering"
        cursor.execute("DELETE FROM student_results WHERE user_id=%s AND grade_level='12th'", (session['user_id'],))
        cursor.execute("INSERT INTO student_results (user_id, grade_level, recommended_stream_or_career) VALUES (%s, '12th', %s)",
                       (session['user_id'], recommendation))
        conn.commit()
        cursor.close(); conn.close()
        return redirect(url_for('career_results'))

    cursor.execute("SELECT * FROM questions WHERE grade_level='12th' AND (stream=%s OR stream='All')", (stream,))
    questions = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template("assessment_12th.html", questions=questions)

@app.route("/career_results")
def career_results():
    if "user_id" not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    
    cursor.execute("SELECT * FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()
    cursor.execute("SELECT * FROM student_results WHERE user_id=%s ORDER BY assessment_date DESC", (session['user_id'],))
    result = cursor.fetchone()
    
    if not demo or not result:
        cursor.close(); conn.close()
        return redirect(url_for('demographics'))
    
    level = demo['education_level']
    recommendation = result['recommended_stream_or_career']
    
    if recommendation == 'Engineering': user_mark = float(demo['cutoff_engineering'] or 0)
    elif recommendation == 'Medical':   user_mark = float(demo['cutoff_medical'] or 0)
    elif recommendation == 'Agriculture': user_mark = float(demo['cutoff_agriculture'] or 0)
    elif recommendation == 'Government_Service': user_mark = float(demo['cutoff_engineering'] or 0)
    else: user_mark = float(demo['cutoff_law_arts'] or 0)

    cursor.close(); conn.close()
    return render_template("career_results.html", level=level, recommendation=recommendation, user_mark=user_mark)

NEARBY_DISTRICTS = {
    'Ariyalur': ['Perambalur', 'Tiruchirappalli', 'Thanjavur', 'Cuddalore'],
    'Chengalpattu': ['Chennai', 'Kancheepuram', 'Thiruvallur', 'Villupuram'],
    'Chennai': ['Chengalpattu', 'Thiruvallur', 'Kancheepuram'],
    'Coimbatore': ['Tiruppur', 'Erode', 'The Nilgiris', 'Dindigul'],
    'Cuddalore': ['Villupuram', 'Ariyalur', 'Perambalur', 'Thanjavur', 'Mayiladuthurai', 'Nagapattinam'],
    'Dharmapuri': ['Krishnagiri', 'Salem', 'Thiruvannamalai', 'Erode'],
    'Dindigul': ['Madurai', 'Coimbatore', 'Tiruppur', 'Karur', 'Theni', 'Sivagangai'],
    'Erode': ['Salem', 'Namakkal', 'Tiruppur', 'Coimbatore', 'Karur', 'Dharmapuri'],
    'Kancheepuram': ['Chennai', 'Chengalpattu', 'Thiruvallur', 'Villupuram'],
    'Kanyakumari': ['Tirunelveli', 'Tenkasi', 'Thoothukudi'],
    'Karaikudi': ['Sivagangai', 'Pudukkottai', 'Ramanathapuram'],
    'Karur': ['Tiruchirappalli', 'Dindigul', 'Namakkal', 'Erode'],
    'Krishnagiri': ['Dharmapuri', 'Salem', 'Vellore', 'Thirupathur'],
    'Madurai': ['Dindigul', 'Sivagangai', 'Theni', 'Virudhunagar', 'Ramanathapuram'],
    'Mayiladuthurai': ['Nagapattinam', 'Thanjavur', 'Cuddalore', 'Thiruvarur'],
    'Nagapattinam': ['Mayiladuthurai', 'Thiruvarur', 'Thanjavur', 'Cuddalore'],
    'Namakkal': ['Salem', 'Erode', 'Karur', 'Tiruchirappalli', 'Perambalur'],
    'Perambalur': ['Ariyalur', 'Tiruchirappalli', 'Namakkal', 'Cuddalore'],
    'Periyakulam': ['Theni', 'Madurai', 'Dindigul'],
    'Pudukkottai': ['Sivagangai', 'Thanjavur', 'Tiruchirappalli', 'Karaikudi'],
    'Pudukottai': ['Sivagangai', 'Thanjavur', 'Tiruchirappalli', 'Karaikudi'],
    'Ramanathapuram': ['Sivagangai', 'Madurai', 'Virudhunagar', 'Thoothukudi'],
    'Salem': ['Namakkal', 'Dharmapuri', 'Krishnagiri', 'Erode', 'Thiruvannamalai'],
    'Sivagangai': ['Madurai', 'Ramanathapuram', 'Pudukkottai', 'Dindigul', 'Karaikudi'],
    'Tenkasi': ['Tirunelveli', 'Virudhunagar', 'Kanyakumari', 'Thoothukudi'],
    'Thanjavur': ['Tiruchirappalli', 'Pudukkottai', 'Ariyalur', 'Nagapattinam', 'Thiruvarur', 'Mayiladuthurai'],
    'The Nilgiris': ['Coimbatore', 'Erode', 'Tiruppur'],
    'Theni': ['Madurai', 'Dindigul', 'Virudhunagar', 'Periyakulam'],
    'Thirupathur': ['Vellore', 'Krishnagiri', 'Thiruvannamalai'],
    'Thiruvallur': ['Chennai', 'Kancheepuram', 'Chengalpattu', 'Vellore'],
    'Thiruvannamalai': ['Villupuram', 'Vellore', 'Dharmapuri', 'Salem', 'Thirupathur'],
    'Thiruvarur': ['Nagapattinam', 'Thanjavur', 'Mayiladuthurai'],
    'Thoothukudi': ['Tirunelveli', 'Ramanathapuram', 'Virudhunagar', 'Tenkasi', 'Kanyakumari'],
    'Tiruchirappalli': ['Karur', 'Perambalur', 'Ariyalur', 'Thanjavur', 'Pudukkottai', 'Namakkal'],
    'Trichy': ['Karur', 'Perambalur', 'Ariyalur', 'Thanjavur', 'Pudukkottai', 'Namakkal'],
    'Tirunelveli': ['Tenkasi', 'Thoothukudi', 'Kanyakumari', 'Virudhunagar'],
    'Tiruppur': ['Coimbatore', 'Erode', 'Karur', 'Dindigul', 'The Nilgiris'],
    'Vellore': ['Thiruvallur', 'Thiruvannamalai', 'Krishnagiri', 'Thirupathur'],
    'Villupuram': ['Cuddalore', 'Thiruvannamalai', 'Kancheepuram', 'Chengalpattu'],
    'Virudhunagar': ['Madurai', 'Sivagangai', 'Ramanathapuram', 'Thoothukudi', 'Tirunelveli', 'Tenkasi', 'Theni'],
}

@app.route("/colleges")
def colleges():
    if 'user_id' not in session: return redirect(url_for('login'))

    career = request.args.get('career')
    if not career:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT recommended_stream_or_career FROM student_results WHERE user_id=%s ORDER BY assessment_date DESC", (session['user_id'],))
        res = cursor.fetchone()
        career = res['recommended_stream_or_career'] if res else 'Engineering'
        cursor.close(); conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("SELECT * FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()
    user_cat = demo['category'] if demo else 'OC'
    user_district_raw = demo['district'] if demo else ''
    user_district = user_district_raw.strip().title() if user_district_raw else ''
    
    if career == 'Engineering': user_mark = float(demo.get('cutoff_engineering') or 0)
    elif career == 'Medical':   user_mark = float(demo.get('cutoff_medical') or 0)
    elif career == 'Agriculture': user_mark = float(demo.get('cutoff_agriculture') or 0)
    else: user_mark = float(demo.get('cutoff_law_arts') or 0)

    search_mark = request.args.get('marks')
    if search_mark:
        try: user_mark = float(search_mark)
        except: pass

    district_filter = request.args.get('district_filter', 'native')

    db_cat = get_db_category(career)

    if district_filter == 'native' and user_district:
        cursor.execute("SELECT id, name, district, category, college_code FROM colleges WHERE category=%s AND status='active' AND LOWER(district)=LOWER(%s)", (db_cat, user_district))
    elif district_filter == 'nearby' and user_district:
        nearby = NEARBY_DISTRICTS.get(user_district, [])
        all_districts = [user_district] + nearby
        placeholders = ','.join(['LOWER(%s)'] * len(all_districts))
        cursor.execute(f"SELECT id, name, district, category, college_code FROM colleges WHERE category=%s AND status='active' AND LOWER(district) IN ({placeholders})", [db_cat] + all_districts)
    else:
        cursor.execute("SELECT id, name, district, category, college_code FROM colleges WHERE category=%s AND status='active'", (db_cat,))

    college_list = cursor.fetchall()
    
    results = []
    for coll in college_list:
        if career == 'Agriculture':
            cursor.execute("""
                SELECT d.department_name AS course_name, ac.cutoff_min, ac.cutoff_max, ac.category AS cutoff_category, ac.year
                FROM agri_cutoffs ac
                JOIN departments d ON ac.department_id = d.department_id
                WHERE ac.college_code=%s AND (ac.category=%s OR ac.category='OC')
                ORDER BY (ac.year=2024) DESC, ac.year DESC, (ac.category=%s) DESC, ac.cutoff_min ASC
            """, (coll['college_code'], user_cat, user_cat))
            rows = cursor.fetchall()
            
            dept_data = {}
            for row in rows:
                d_name = row['course_name']
                if d_name not in dept_data:
                    dept_data[d_name] = {
                        'mark': float(row['cutoff_min']),
                        'cutoff_max': float(row['cutoff_max']),
                        'year': row['year'],
                        'category': row['cutoff_category']
                    }
            
            depts = []
            for d_name, info in dept_data.items():
                req_cutoff = info['mark']
                chance = ""
                if user_mark >= req_cutoff: chance = "High Chance"
                elif user_mark >= (req_cutoff - 5): chance = "Medium Chance"
                
                if chance:
                    depts.append({
                        'name': d_name,
                        'req_cutoff': req_cutoff,
                        'req_cutoff_max': info['cutoff_max'],
                        'chance': chance,
                        'year': info['year'],
                        'category': info['category']
                    })
        else:
            cursor.execute("""
                SELECT d.department_name AS course_name, cu.cutoff_mark, cu.year FROM cutoffs cu
                JOIN college_departments cd ON cu.college_department_id = cd.id
                JOIN departments d ON cd.department_id = d.department_id
                WHERE cd.college_code=%s AND (cu.category=%s OR cu.category='OC') 
                ORDER BY (cu.year=2024) DESC, cu.year DESC, (cu.category=%s) DESC, cu.cutoff_mark ASC
            """, (coll['college_code'], user_cat, user_cat))
            rows = cursor.fetchall()
            
            dept_data = {}
            for row in rows:
                d_name = row['course_name']
                if d_name not in dept_data:
                    dept_data[d_name] = {'mark': float(row['cutoff_mark']), 'year': row['year']}
            
            depts = []
            for d_name, info in dept_data.items():
                req_cutoff = info['mark']
                chance = ""
                if user_mark >= req_cutoff: chance = "High Chance"
                elif user_mark >= (req_cutoff - 5): chance = "Medium Chance"
                
                if chance:
                    depts.append({'name': d_name, 'req_cutoff': req_cutoff, 'chance': chance, 'year': info['year']})

        if depts:
            results.append({
                'id': coll['id'], 'name': coll['name'], 'district': coll['district'],
                'category': coll['category'], 'departments': depts
            })

    cursor.close(); conn.close()
    return render_template('colleges_fixed.html', colleges=results, career=career, user_mark=user_mark, user_district=user_district, district_filter=district_filter)

@app.route("/mbbs_colleges", methods=["GET", "POST"])
def mbbs_colleges():
    if "user_id" not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "danger")
        return redirect(url_for('home'))
    cursor = conn.cursor(dictionary=True)

    # Auto-retrieve student category and district from demographics
    cursor.execute("SELECT category, district FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()
    student_category = demo['category'] if demo else 'OC'
    user_district_raw = demo['district'] if demo else ''
    user_district = user_district_raw.strip().title() if user_district_raw else ''

    district_filter = request.args.get('district_filter', 'all')

    colleges = []
    submitted = False
    neet_value = None
    input_type = None

    if request.method == "POST":
        submitted = True
        input_type = request.form.get("input_type", "expected_score")
        district_filter = request.form.get("district_filter", "all")
        try:
            neet_value = float(request.form.get("neet_value", 0))
        except (ValueError, TypeError):
            neet_value = 0

        # Build district filter SQL
        district_clause = ""
        district_params = []
        if district_filter == 'native' and user_district:
            district_clause = " AND LOWER(c.district)=LOWER(%s)"
            district_params = [user_district]
        elif district_filter == 'nearby' and user_district:
            nearby = NEARBY_DISTRICTS.get(user_district, [])
            all_districts = [user_district] + nearby
            dist_placeholders = ','.join(['LOWER(%s)'] * len(all_districts))
            district_clause = f" AND LOWER(c.district) IN ({dist_placeholders})"
            district_params = all_districts

        if input_type in ("expected_score", "actual_score"):
            # Fetch colleges by NEET score
            cursor.execute(f"""
                SELECT c.name, c.district, m.min_score, m.max_score, m.min_rank, m.max_rank
                FROM mbbs_cutoff m
                JOIN colleges c ON c.college_code = m.college_code
                WHERE m.category = %s
                AND m.min_score <= %s
                {district_clause}
                ORDER BY m.min_score DESC
            """, [student_category, neet_value] + district_params)
        else:
            # Fetch colleges by NEET rank
            neet_value = int(neet_value)
            cursor.execute(f"""
                SELECT c.name, c.district, m.min_score, m.max_score, m.min_rank, m.max_rank
                FROM mbbs_cutoff m
                JOIN colleges c ON c.college_code = m.college_code
                WHERE m.category = %s
                AND m.max_rank >= %s
                {district_clause}
                ORDER BY m.max_rank ASC
            """, [student_category, neet_value] + district_params)

        rows = cursor.fetchall()

        for row in rows:
            min_score = float(row['min_score']) if row['min_score'] else 0
            max_score = float(row['max_score']) if row['max_score'] else 0

            # Determine admission chance category
            if input_type in ("expected_score", "actual_score"):
                score = neet_value
                if score >= max_score:
                    chance = "Safe College"
                elif score >= min_score:
                    chance = "Target College"
                else:
                    continue  # Skip Dream colleges
            else:
                # For rank-based: lower rank is better
                max_rank = int(row['max_rank']) if row['max_rank'] else 0
                min_rank = int(row['min_rank']) if row['min_rank'] else 0
                entered_rank = int(neet_value)
                if min_rank > 0 and entered_rank <= min_rank:
                    chance = "Safe College"
                elif max_rank > 0 and entered_rank <= max_rank:
                    chance = "Target College"
                else:
                    continue  # Skip Dream colleges

            colleges.append({
                'name': row['name'],
                'district': row['district'],
                'chance': chance
            })

    cursor.close()
    conn.close()

    return render_template(
        'mbbs_colleges.html',
        colleges=colleges,
        student_category=student_category,
        submitted=submitted,
        neet_value=neet_value,
        input_type=input_type,
        user_district=user_district,
        district_filter=district_filter
    )

@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
    return render_template("admin_dashboard.html")

@app.route("/admin/questions")
def admin_questions():
    if not session.get("is_admin"):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM questions ORDER BY grade_level DESC, category ASC")
    questions = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template("admin_questions.html", questions=questions)

@app.route("/admin/questions/add", methods=["POST"])
def admin_add_question():
    if not session.get("is_admin"):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))
        
    grade = request.form["grade_level"]
    text = request.form["question_text"]
    cat = request.form["category"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO questions (grade_level, question_text, category, weight) VALUES (%s, %s, %s, 1.0)",
                       (grade, text, cat))
        conn.commit()
        flash("Question added successfully!", "success")
    except Error as e:
        flash(f"Error: {e}", "danger")
    finally:
        cursor.close(); conn.close()
        
    return redirect(url_for('admin_questions'))

@app.route("/govt_colleges")
def govt_colleges():
    if 'user_id' not in session: return redirect(url_for('login'))

    college_type = request.args.get('college_type', 'all')  # all, arts, engineering, agriculture, law
    district_filter = request.args.get('district_filter', 'all')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("SELECT * FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()
    user_cat = demo['category'] if demo else 'OC'
    user_district_raw = demo['district'] if demo else ''
    user_district = user_district_raw.strip().title() if user_district_raw else ''
    user_stream = demo['stream'] if demo else ''

    # Determine allowed college categories based on student's stream
    # PCMB/PCMC/PCB → Engineering, Arts & Science, Agriculture, Law
    # Commerce → Only Arts & Science and Law
    if user_stream == 'Commerce':
        ALLOWED_CATEGORIES = ['Arts & Science', 'Law']
    else:
        ALLOWED_CATEGORIES = ['Arts & Science', 'Engineering', 'Agriculture', 'Law']  # Excludes Medical

    type_to_cat = {
        'arts': 'Arts & Science',
        'engineering': 'Engineering',
        'agriculture': 'Agriculture',
        'law': 'Law'
    }

    # Only allow filtering to categories the student is eligible for
    if college_type != 'all' and college_type in type_to_cat:
        selected_cat = type_to_cat[college_type]
        if selected_cat in ALLOWED_CATEGORIES:
            filter_categories = [selected_cat]
        else:
            filter_categories = ALLOWED_CATEGORIES
    else:
        filter_categories = ALLOWED_CATEGORIES

    # Build district clause
    params = []
    cat_placeholders = ','.join(['%s'] * len(filter_categories))
    sql = f"SELECT id, name, district, category, college_code FROM colleges WHERE category IN ({cat_placeholders}) AND status='active'"
    params.extend(filter_categories)

    if district_filter == 'native' and user_district:
        sql += " AND LOWER(district)=LOWER(%s)"
        params.append(user_district)
    elif district_filter == 'nearby' and user_district:
        nearby = NEARBY_DISTRICTS.get(user_district, [])
        all_districts = [user_district] + nearby
        dist_placeholders = ','.join(['LOWER(%s)'] * len(all_districts))
        sql += f" AND LOWER(district) IN ({dist_placeholders})"
        params.extend(all_districts)

    sql += " ORDER BY category, name"
    cursor.execute(sql, params)
    college_list = cursor.fetchall()

    # Determine user cutoff marks for each type
    user_marks = {
        'Engineering': float(demo.get('cutoff_engineering') or 0) if demo else 0,
        'Arts & Science': float(demo.get('cutoff_law_arts') or 0) if demo else 0,
        'Agriculture': float(demo.get('cutoff_agriculture') or 0) if demo else 0,
        'Law': float(demo.get('cutoff_law_arts') or 0) if demo else 0,
    }

    results = []
    for coll in college_list:
        coll_cat = coll['category']
        user_mark = user_marks.get(coll_cat, 0)

        if coll_cat == 'Agriculture':
            cursor.execute("""
                SELECT d.department_name AS course_name, ac.cutoff_min, ac.cutoff_max, ac.category AS cutoff_category, ac.year
                FROM agri_cutoffs ac
                JOIN departments d ON ac.department_id = d.department_id
                WHERE ac.college_code=%s AND (ac.category=%s OR ac.category='OC')
                ORDER BY (ac.year=2024) DESC, ac.year DESC, (ac.category=%s) DESC, ac.cutoff_min ASC
            """, (coll['college_code'], user_cat, user_cat))
            rows = cursor.fetchall()

            dept_data = {}
            for row in rows:
                d_name = row['course_name']
                if d_name not in dept_data:
                    dept_data[d_name] = {
                        'mark': float(row['cutoff_min']),
                        'cutoff_max': float(row['cutoff_max']),
                        'year': row['year'],
                        'category': row['cutoff_category']
                    }

            depts = []
            for d_name, info in dept_data.items():
                req_cutoff = info['mark']
                chance = ""
                if user_mark >= req_cutoff: chance = "High Chance"
                elif user_mark >= (req_cutoff - 5): chance = "Medium Chance"

                if chance:
                    depts.append({
                        'name': d_name,
                        'req_cutoff': req_cutoff,
                        'req_cutoff_max': info['cutoff_max'],
                        'chance': chance,
                        'year': info['year'],
                        'category': info['category']
                    })
        else:
            cursor.execute("""
                SELECT d.department_name AS course_name, cu.cutoff_mark, cu.year, cu.category AS cutoff_category FROM cutoffs cu
                JOIN college_departments cd ON cu.college_department_id = cd.id
                JOIN departments d ON cd.department_id = d.department_id
                WHERE cd.college_code=%s AND (cu.category=%s OR cu.category='OC')
                ORDER BY (cu.year=2024) DESC, cu.year DESC, (cu.category=%s) DESC, cu.cutoff_mark ASC
            """, (coll['college_code'], user_cat, user_cat))
            rows = cursor.fetchall()

            dept_data = {}
            for row in rows:
                d_name = row['course_name']
                if d_name not in dept_data:
                    dept_data[d_name] = {'mark': float(row['cutoff_mark']), 'year': row['year'], 'category': row.get('cutoff_category', '')}

            depts = []
            for d_name, info in dept_data.items():
                req_cutoff = info['mark']
                chance = ""
                if user_mark >= req_cutoff: chance = "High Chance"
                elif user_mark >= (req_cutoff - 5): chance = "Medium Chance"

                if chance:
                    depts.append({
                        'name': d_name,
                        'req_cutoff': req_cutoff,
                        'chance': chance,
                        'year': info['year'],
                        'category': info.get('category', '')
                    })

        if depts:
            results.append({
                'id': coll['id'], 'name': coll['name'], 'district': coll['district'],
                'category': coll['category'], 'departments': depts
            })

    # Count colleges by type for stat display
    type_counts = {}
    for c in results:
        cat = c['category']
        type_counts[cat] = type_counts.get(cat, 0) + 1

    cursor.close(); conn.close()
    return render_template('govt_colleges.html',
        colleges=results, college_type=college_type,
        district_filter=district_filter, user_district=user_district,
        type_counts=type_counts, user_stream=user_stream,
        allowed_types=ALLOWED_CATEGORIES)

@app.route("/law_colleges", methods=["GET", "POST"])
def law_colleges():
    if "user_id" not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection error.", "danger")
        return redirect(url_for('home'))
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT category, cutoff_law_arts FROM demographics WHERE user_id=%s", (session['user_id'],))
    demo = cursor.fetchone()
    default_category = demo['category'] if demo else 'OC'
    default_mark = float(demo['cutoff_law_arts'] or 0) if demo else 0

    categories = ['OC', 'BC', 'BCM', 'MBC', 'SC', 'SCA', 'ST']
    results = []
    student_mark = None
    selected_category = default_category

    if request.method == "POST":
        student_mark = request.form.get("student_mark", type=float)
        selected_category = request.form.get("category", default_category)

        if student_mark is not None and selected_category:
            cursor.execute("""
                SELECT 
                    c.college_name,
                    d.department_name,
                    cu.cutoff_mark,
                    cu.category,
                    cu.year
                FROM cutoffs cu
                JOIN college_departments cd ON cu.college_department_id = cd.id
                JOIN colleges c ON cd.college_code = c.college_code
                JOIN departments d ON cd.department_id = d.department_id
                WHERE cu.category = %s
                AND cu.cutoff_mark <= %s
                AND cu.year = 2024
                ORDER BY cu.cutoff_mark DESC
            """, (selected_category, student_mark))
            results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'law_colleges.html',
        results=results,
        categories=categories,
        student_mark=student_mark,
        selected_category=selected_category,
        default_mark=default_mark
    )

if __name__ == "__main__":
    app.run(debug=True)
