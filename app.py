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
    <title>GP Maker — Apple Style</title>
    <link href="https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --apple-blue: #0071e3;
            --apple-bg: #f5f5f7;
            --apple-card: rgba(255, 255, 255, 0.8);
            --apple-text: #1d1d1f;
            --apple-gray: #86868b;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-font-smoothing: antialiased; }

        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--apple-bg);
            color: var(--apple-text);
            display: flex;
            justify-content: center;
            padding: 60px 20px;
            min-height: 100vh;
        }

        .container { width: 100%; max-width: 540px; }

        /* Apple Header */
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 40px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 8px; }
        .header p { color: var(--apple-gray); font-size: 19px; font-weight: 400; }

        /* Card Structure */
        .card {
            background: var(--apple-card);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 32px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.04);
            border: 1px solid rgba(255,255,255,0.4);
        }

        .step-label {
            font-size: 12px; font-weight: 600; text-transform: uppercase;
            letter-spacing: 0.05em; color: var(--apple-blue); margin-bottom: 12px;
            display: block;
        }

        /* Pill Upload Box */
        .upload-area {
            border: 2px dashed #d2d2d7;
            border-radius: 24px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            background: rgba(0,0,0,0.01);
        }
        .upload-area:hover { border-color: var(--apple-blue); background: rgba(0,113,227,0.02); }
        .upload-area input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
        
        .icon-circle {
            width: 54px; height: 54px; background: #fff; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }

        /* Pill Buttons & Chips */
        .pill-group { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
        .pill {
            background: #e8e8ed;
            color: var(--apple-text);
            padding: 8px 18px;
            border-radius: 40px; /* Perfect pill shape */
            font-size: 14px; font-weight: 400;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }
        .pill:hover { background: #d2d2d7; }
        .pill.active { background: var(--apple-text); color: #fff; }

        /* Smooth Textarea */
        textarea {
            width: 100%; min-height: 120px;
            padding: 18px; border-radius: 20px;
            border: 1px solid #d2d2d7;
            background: #fff;
            font-family: inherit; font-size: 16px;
            outline: none; transition: border-color 0.3s;
            resize: none; line-height: 1.5;
        }
        textarea:focus { border-color: var(--apple-blue); box-shadow: 0 0 0 4px rgba(0,113,227,0.1); }

        /* Main Action Button - The Apple Blue */
        .btn-primary {
            width: 100%; padding: 18px;
            background-color: var(--apple-blue);
            color: #fff; border: none;
            border-radius: 40px; /* Pill */
            font-size: 17px; font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
            display: flex; align-items: center; justify-content: center; gap: 10px;
        }
        .btn-primary:hover { opacity: 0.9; transform: scale(1.01); }
        .btn-primary:active { transform: scale(0.98); }
        .btn-primary:disabled { background: #d2d2d7; cursor: not-allowed; transform: none; }

        /* Status Toasts */
        .status-msg {
            margin-top: 24px; padding: 16px 24px;
            border-radius: 20px; text-align: center;
            display: none; font-size: 15px; font-weight: 500;
            animation: slideUp 0.4s ease;
        }
        @keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .loading { background: #e8e8ed; color: var(--apple-text); }
        .success { background: #34c759; color: #fff; }
        .error { background: #ff3b30; color: #fff; }

        /* Smooth Spinner */
        .spinner {
            width: 20px; height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top: 2px solid #fff;
            border-radius: 50%;
            animation: rotate 0.8s linear infinite;
        }
        @keyframes rotate { to { transform: rotate(360deg); } }

        .file-pill {
            display: none; align-items: center; gap: 8px;
            background: #f2f2f7; padding: 6px 16px;
            border-radius: 40px; color: var(--apple-blue);
            font-size: 13px; font-weight: 500;
            width: fit-content; margin: 12px auto 0;
        }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>GP Maker</h1>
        <p>SIMATS Engineering</p>
    </div>

    <form id="uploadForm">
        <div class="card">
            <span class="step-label">Step 1</span>
            <div class="upload-area">
                <input type="file" id="file" accept=".ppt,.pptx" required>
                <div class="icon-circle">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0071e3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                </div>
                <p style="font-weight: 500;">Choose Presentation</p>
                <p style="font-size: 13px; color: var(--apple-gray); margin-top: 4px;">PPT or PPTX up to 50MB</p>
                <div id="fileInfo" class="file-pill">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    <span id="fileNameDisplay"></span>
                </div>
            </div>
        </div>

        <div class="card">
            <span class="step-label">Step 2: Mentee Feedback</span>
            <div class="pill-group">
                <button type="button" class="pill" data-target="mentee" data-val="I am doing well and attending all classes regularly.">Doing well</button>
                <button type="button" class="pill" data-target="mentee" data-val="I understand the topics covered and will work harder.">Work harder</button>
                <button type="button" class="pill" data-target="mentee" data-val="I am focused on improving my academic performance.">Improving</button>
            </div>
            <textarea id="mentee_response" placeholder="Type or select a response..." required></textarea>
        </div>

        <div class="card">
            <span class="step-label">Step 3: Parent Feedback</span>
            <div class="pill-group">
                <button type="button" class="pill" data-target="parent" data-val="My child is performing well and we are happy.">Satisfied</button>
                <button type="button" class="pill" data-target="parent" data-val="We are monitoring the studies closely at home.">Monitoring</button>
                <button type="button" class="pill" data-target="parent" data-val="We appreciate the mentor's efforts.">Appreciative</button>
            </div>
            <textarea id="parent_response" placeholder="Type or select a response..." required></textarea>
        </div>

        <button type="submit" class="btn-primary" id="submitBtn">
            Generate Report
        </button>

        <div id="status" class="status-msg"></div>
    </form>
</div>

<script>
    // Handle Pill Selection
    document.querySelectorAll('.pill').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.target;
            document.querySelectorAll(`.pill[data-target="${target}"]`).forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(target + '_response').value = btn.dataset.val;
        });
    });

    // File Input Visuals
    document.getElementById('file').addEventListener('change', function() {
        if (this.files.length > 0) {
            document.getElementById('fileNameDisplay').textContent = this.files[0].name;
            document.getElementById('fileInfo').style.display = 'flex';
        }
    });

    // Form Handling
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const status = document.getElementById('status');
        const btn = document.getElementById('submitBtn');

        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Processing...';
        status.className = 'status-msg loading';
        status.style.display = 'block';
        status.textContent = 'Preparing your document...';

        const formData = new FormData();
        formData.append('file', document.getElementById('file').files[0]);
        formData.append('parent_response', document.getElementById('parent_response').value);
        formData.append('mentee_response', document.getElementById('mentee_response').value);

        try {
            const response = await fetch('/convert', { method: 'POST', body: formData });
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'GP_Report.pdf';
                document.body.appendChild(a);
                a.click();
                
                status.className = 'status-msg success';
                status.textContent = 'Report downloaded successfully!';
            } else {
                throw new Error('Failed to generate report');
            }
        } catch (err) {
            status.className = 'status-msg error';
            status.textContent = err.message;
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Generate Report';
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
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        parent_response = request.form.get('parent_response', '')
        mentee_response = request.form.get('mentee_response', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(input_path)

        output_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_output.pdf")

        success, file_type = process_ppt_to_pdf(
            input_ppt_path=input_path,
            output_pdf_path=output_pdf_path,
            parent_response=parent_response,
            mentee_response=mentee_response,
            keep_slides=3
        )

        if success and os.path.exists(output_pdf_path):
            return send_file(output_pdf_path, as_attachment=True, download_name='GP_Report.pdf')

        return jsonify({'error': 'Process failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=10000)
