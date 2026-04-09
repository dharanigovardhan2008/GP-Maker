from flask import Flask, request, send_file, jsonify, render_template_string
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from ppt_processor import process_ppt_to_pdf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs('uploads', exist_ok=True)

ALLOWED_EXTENSIONS = {'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>GP Maker — Student Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #818cf8;
            --secondary: #c084fc;
            --success: #10b981;
            --bg-dark: #050506;
            --card-bg: rgba(22, 22, 26, 0.8);
            --border: rgba(255, 255, 255, 0.1);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(129, 140, 248, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(192, 132, 252, 0.12) 0%, transparent 40%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 40px 16px;
            color: #e2e8f0;
        }

        .page { width: 100%; max-width: 550px; }

        .header { text-align: center; padding-bottom: 40px; }
        .logo-container {
            width: 72px; height: 72px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 22px;
            display: inline-flex; align-items: center; justify-content: center;
            margin-bottom: 20px;
            backdrop-filter: blur(12px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
        .header h1 { color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -1px; }
        .header p { color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-top: 5px; }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(25px);
            border: 1px solid var(--border);
            border-radius: 30px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .card-title {
            font-size: 11px; font-weight: 800; letter-spacing: 0.2em;
            text-transform: uppercase; color: #64748b; margin-bottom: 24px;
            display: flex; align-items: center; gap: 15px;
        }
        .card-title::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--border), transparent); }

        .upload-box {
            border: 2px dashed var(--border);
            border-radius: 24px;
            padding: 45px 20px;
            text-align: center;
            position: relative;
            transition: all 0.4s ease;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.01);
        }
        
        /* Green outline when file is uploaded */
        .upload-box.file-uploaded {
            border: 2px solid var(--success) !important;
            background: rgba(16, 185, 129, 0.05);
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
        }

        .upload-box input[type="file"] {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            opacity: 0; cursor: pointer; z-index: 10;
        }

        .upload-text { color: #94a3b8; font-size: 14px; }
        .upload-text strong { color: #fff; }

        .file-name {
            margin-top: 20px; font-size: 13px; color: var(--success); font-weight: 700;
            display: none; align-items: center; justify-content: center;
            background: rgba(16, 185, 129, 0.1); padding: 12px; border-radius: 15px;
        }

        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
        .chip {
            font-size: 11px; font-weight: 600; padding: 10px 14px; 
            border-radius: 50px; border: 1px solid var(--border);
            background: rgba(255,255,255,0.04); color: #94a3b8;
            cursor: pointer; transition: all 0.2s ease;
        }
        .chip.active {
            background: #ffffff; color: #000; border-color: #fff;
        }

        textarea {
            width: 100%; padding: 20px; border: 1px solid var(--border);
            border-radius: 20px; background: rgba(0,0,0,0.4);
            font-size: 14px; color: #fff; resize: none; min-height: 110px;
            font-family: inherit; outline: none; transition: all 0.3s ease;
        }

        /* Emerald/Teal Button */
        .btn {
            width: 100%; padding: 22px;
            background: linear-gradient(135deg, #059669, #10b981);
            color: #fff; border: none; border-radius: 24px;
            font-size: 16px; font-weight: 800; cursor: pointer;
            transition: all 0.3s ease; box-shadow: 0 15px 35px rgba(16, 185, 129, 0.2);
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 20px 45px rgba(16, 185, 129, 0.3); }

        .status { margin-top: 24px; padding: 20px; border-radius: 20px; display: none; font-size: 14px; font-weight: 700; align-items: center; justify-content: center; gap: 12px; }
        .status.loading { background: rgba(255,255,255,0.05); color: #cbd5e1; display: flex; }

        .progress-bar { height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; margin-top: 25px; overflow: hidden; display: none; }
        .progress-fill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--success), #34d399); transition: width 0.4s ease; }

        .footer { 
            text-align: center; color: #475569; font-size: 10px; 
            padding-top: 60px; padding-bottom: 40px; letter-spacing: 2px; font-weight: 800; text-transform: uppercase; 
            display: flex; flex-direction: column; align-items: center; gap: 15px;
        }
        .insta-btn {
            display: flex; align-items: center; gap: 10px;
            background: rgba(255, 255, 255, 0.03);
            padding: 10px 20px; border-radius: 50px;
            border: 1px solid var(--border);
            color: #cbd5e1; text-decoration: none;
            transition: all 0.3s ease;
        }
        .insta-btn:hover { background: rgba(255, 255, 255, 0.08); border-color: var(--secondary); color: #fff; }
        .insta-icon { fill: var(--primary); transition: fill 0.3s ease; }

        @keyframes spin { to { transform: rotate(360deg); } }
        .spinner { width: 22px; height: 22px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
    </style>
</head>
<body>
<div class="page">
    <div class="header">
        <div class="logo-container">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="url(#logoG)" stroke-width="2">
                <defs><linearGradient id="logoG" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#c084fc"/></linearGradient></defs>
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h1>GP Maker</h1>
        <p>SIMATS ENGINEERING &bull; STUDENT PORTAL</p>
    </div>

    <form id="uploadForm">
        <div class="card">
            <div class="card-title">Step 1 &mdash; Presentation</div>
            <div class="upload-box" id="uploadBox">
                <input type="file" id="file" accept=".ppt,.pptx" required>
                <div class="upload-text"><strong>Click to upload</strong> your PPTX file<br><span style="font-size: 11px; opacity: 0.6;">Maximum size 50MB</span></div>
                <div class="file-name" id="fileName"><span id="fileNameText"></span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Step 2 &mdash; Student Response</div>
            <div class="chips">
                <span class="chip" data-target="mentee" data-val="I am attending all classes and doing well.">Regular</span>
                <span class="chip" data-target="mentee" data-val="I am studying hard and solving old question papers.">Exam Prep</span>
                <span class="chip" data-target="mentee" data-val="I am finishing all my assignments and records on time.">Assignments</span>
                <span class="chip" data-target="mentee" data-val="I am working to get better marks in the next test.">Better Marks</span>
                <span class="chip" data-target="mentee" data-val="I am learning new skills for my future job.">Job Skills</span>
                <span class="chip" data-target="mentee" data-val="I am following all the advice given by my teacher.">Teacher Advice</span>
                <span class="chip" data-target="mentee" data-val="I am taking extra help for my hard subjects.">Extra Help</span>
                <span class="chip" data-target="mentee" data-val="I am trying my best to be active in class.">Active in Class</span>
            </div>
            <textarea id="mentee_response" placeholder="Choose a button or type here..." required></textarea>
        </div>

        <div class="card">
            <div class="card-title">Step 3 &mdash; Parents Feedback</div>
            <div class="chips">
                <span class="chip" data-target="parent" data-val="We are happy with the progress and check the studies at home.">Happy</span>
                <span class="chip" data-target="parent" data-val="We see a good change in study habits at home.">Good Change</span>
                <span class="chip" data-target="parent" data-val="We will make sure the student comes to college every day.">Daily Attendance</span>
                <span class="chip" data-target="parent" data-val="We are checking the test marks and help them study.">Check Marks</span>
                <span class="chip" data-target="parent" data-val="We like the way the college helps the students learn.">Good Learning</span>
                <span class="chip" data-target="parent" data-val="We will help our child to study more at home.">Home Study</span>
                <span class="chip" data-target="parent" data-val="We thank the teacher for the help and guidance.">Thanks Teacher</span>
                <span class="chip" data-target="parent" data-val="We are keeping a close eye on the assignments.">Check Homework</span>
            </div>
            <textarea id="parent_response" placeholder="Choose a button or type here..." required></textarea>
        </div>

        <button type="submit" class="btn" id="submitBtn">Generate Report</button>
        <div class="progress-bar" id="progressBar"><div class="progress-fill" id="progressFill"></div></div>
        <div class="status" id="status"></div>
    </form>

    <div class="footer">
        <span>GP MAKER &bull; STUDENT EDITION</span>
        <a href="https://www.instagram.com/dharani_govardhan_chowdary?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==" target="_blank" class="insta-btn">
            <svg class="insta-icon" width="18" height="18" viewBox="0 0 24 24">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
            </svg>
            Developed by Developer
        </a>
    </div>
</div>

<script>
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const target = chip.dataset.target;
            document.querySelectorAll(`.chip[data-target="${target}"]`).forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            document.getElementById(target + '_response').value = chip.dataset.val;
        });
    });

    document.getElementById('file').addEventListener('change', function() {
        const box = document.getElementById('uploadBox');
        if (this.files.length > 0) {
            document.getElementById('fileNameText').textContent = this.files[0].name;
            document.getElementById('fileName').style.display = 'flex';
            box.classList.add('file-uploaded');
        } else {
            box.classList.remove('file-uploaded');
        }
    });

    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('submitBtn');
        const status = document.getElementById('status');
        const bar = document.getElementById('progressBar');
        const fill = document.getElementById('progressFill');
        
        submitBtn.disabled = true;
        status.className = 'status loading';
        status.innerHTML = '<div class="spinner"></div> Making Report...';
        status.style.display = 'flex';
        bar.style.display = 'block';
        
        let p = 0;
        const interval = setInterval(() => { p = Math.min(p + 5, 90); fill.style.width = p + '%'; }, 150);

        const formData = new FormData();
        formData.append('file', document.getElementById('file').files[0]);
        formData.append('parent_response', document.getElementById('parent_response').value);
        formData.append('mentee_response', document.getElementById('mentee_response').value);

        try {
            const res = await fetch('/convert', { method: 'POST', body: formData });
            clearInterval(interval);
            fill.style.width = '100%';
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'Report.pdf';
                a.click();
                status.innerHTML = 'Success!';
            } else { throw new Error('Failed'); }
        } catch (err) {
            status.innerHTML = 'Error: ' + err.message;
        } finally {
            submitBtn.disabled = false;
        }
    });
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        file = request.files['file']
        parent_response = request.form.get('parent_response', '')
        mentee_response = request.form.get('mentee_response', '')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = os.path.join('uploads', f"{timestamp}_{filename}")
        file.save(input_path)

        output_pdf_path = os.path.join('uploads', f"{timestamp}_output.pdf")

        success, file_type = process_ppt_to_pdf(
            input_ppt_path=input_path,
            output_pdf_path=output_pdf_path,
            parent_response=parent_response,
            mentee_response=mentee_response,
            keep_slides=3
        )

        if success and os.path.exists(output_pdf_path):
            return send_file(output_pdf_path, as_attachment=True)
        return jsonify({'error': 'Failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
