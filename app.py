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
    <title>GP Maker — Premium Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #818cf8;
            --secondary: #c084fc;
            --bg-dark: #050506;
            --card-bg: rgba(22, 22, 26, 0.7);
            --border: rgba(255, 255, 255, 0.08);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(129, 140, 248, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(192, 132, 252, 0.1) 0%, transparent 40%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 40px 16px;
            color: #e2e8f0;
            line-height: 1.5;
        }

        .page { width: 100%; max-width: 550px; position: relative; }

        /* Header */
        .header { text-align: center; padding-bottom: 40px; }
        .logo-container {
            width: 72px; height: 72px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 22px;
            display: inline-flex; align-items: center; justify-content: center;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(12px);
        }
        .header h1 { 
            color: #ffffff; font-size: 32px; font-weight: 700; 
            letter-spacing: -1px; margin-bottom: 8px;
        }
        .header p { 
            color: #94a3b8; font-size: 12px; font-weight: 600;
            letter-spacing: 2px; text-transform: uppercase;
        }

        /* Cards */
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .card:hover { border-color: rgba(129, 140, 248, 0.3); transform: translateY(-2px); }

        .card-title {
            font-size: 12px; font-weight: 700;
            letter-spacing: 0.1em; text-transform: uppercase;
            color: #64748b; margin-bottom: 24px;
            display: flex; align-items: center; gap: 12px;
        }
        .card-title::after {
            content: ''; flex-grow: 1; height: 1px;
            background: linear-gradient(90deg, var(--border) 0%, transparent 100%);
        }

        /* Upload box */
        .upload-box {
            border: 2px dashed var(--border);
            border-radius: 20px;
            padding: 40px 20px;
            text-align: center;
            background: rgba(255, 255, 255, 0.01);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }
        .upload-box:hover, .upload-box.has-file {
            border-color: var(--primary);
            background: rgba(129, 140, 248, 0.05);
        }
        .upload-box input[type="file"] {
            position: absolute; inset: 0; opacity: 0; cursor: pointer;
        }
        .upload-icon { margin-bottom: 16px; transition: transform 0.3s ease; }
        .upload-box:hover .upload-icon { transform: scale(1.1); }
        .upload-text { color: #94a3b8; font-size: 14px; }
        .upload-text strong { color: #ffffff; font-weight: 600; }
        
        .file-name {
            margin-top: 20px; font-size: 13px;
            color: var(--primary); font-weight: 600;
            display: none; align-items: center; justify-content: center; gap: 8px;
            background: rgba(129, 140, 248, 0.15);
            padding: 10px 20px; border-radius: 12px;
            width: fit-content; margin-inline: auto;
            border: 1px solid rgba(129, 140, 248, 0.2);
        }

        /* Section labels */
        .section-label {
            font-size: 13px; font-weight: 600;
            color: #cbd5e1; margin-bottom: 16px;
            display: flex; align-items: center; gap: 10px;
        }
        .dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: var(--primary);
            box-shadow: 0 0 12px var(--primary);
        }

        /* Chips Grid */
        .chips { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; margin-bottom: 20px; }
        .chip {
            font-size: 11px; font-weight: 600;
            padding: 10px 12px; border-radius: 12px;
            border: 1px solid var(--border);
            background: rgba(255,255,255,0.03);
            color: #94a3b8; cursor: pointer;
            transition: all 0.2s ease; text-align: center;
        }
        .chip:hover { background: rgba(255,255,255,0.08); color: #ffffff; }
        .chip.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: #ffffff; border-color: transparent;
            box-shadow: 0 8px 20px rgba(129, 140, 248, 0.3);
        }

        /* Textarea */
        textarea {
            width: 100%; padding: 18px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: rgba(0,0,0,0.3);
            font-size: 14px; color: #ffffff;
            resize: none; min-height: 110px;
            font-family: inherit; outline: none;
            transition: all 0.3s ease;
        }
        textarea:focus { 
            border-color: var(--primary); 
            box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.1);
        }

        /* Button */
        .btn {
            width: 100%; padding: 20px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            color: #fff; border: none; border-radius: 20px;
            font-size: 16px; font-weight: 700; cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
            display: flex; justify-content: center; align-items: center; gap: 12px;
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 15px 40px rgba(99, 102, 241, 0.5); }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        /* Status & Progress */
        .status {
            margin-top: 24px; padding: 18px; border-radius: 18px;
            display: none; font-size: 14px; font-weight: 600;
            align-items: center; justify-content: center; gap: 12px;
        }
        .status.loading { background: rgba(255,255,255,0.05); color: #cbd5e1; display: flex;}
        .status.success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); display: flex;}
        .status.error { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); display: flex;}

        .progress-bar {
            height: 6px; background: rgba(255,255,255,0.05);
            border-radius: 10px; margin-top: 24px; overflow: hidden;
            display: none;
        }
        .progress-fill {
            height: 100%; width: 0%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            transition: width 0.4s ease;
        }

        .footer {
            text-align: center; color: #475569;
            font-size: 11px; padding-top: 40px;
            letter-spacing: 2px; font-weight: 700; text-transform: uppercase;
        }

        @keyframes spin { to { transform: rotate(360deg); } }
        .spinner {
            width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.1);
            border-top-color: var(--primary); border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
    </style>
</head>
<body>
<div class="page">
    <div class="header">
        <div class="logo-container">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="url(#g)" stroke-width="2">
                <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#c084fc"/></linearGradient></defs>
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h1>GP Maker</h1>
        <p>SIMATS ENGINEERING &bull; PREMIUM PORTAL</p>
    </div>

    <form id="uploadForm">
        <div class="card">
            <div class="card-title">Step 1 &mdash; Presentation</div>
            <div class="upload-box" id="uploadBox">
                <input type="file" id="file" accept=".ppt,.pptx" required>
                <div class="upload-icon">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="1.5">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="upload-text"><strong>Drop PPTX</strong> or click to browse</div>
                <div class="file-name" id="fileName">
                    <span id="fileNameText"></span>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Step 2 &mdash; Mentee Performance</div>
            <div class="section-label"><div class="dot"></div>Quick Selection</div>
            <div class="chips">
                <span class="chip" data-target="mentee" data-val="I am doing well and attending all classes regularly.">Regular & Good</span>
                <span class="chip" data-target="mentee" data-val="I am focusing on solving previous year papers to improve my grades.">PYQ Focus</span>
                <span class="chip" data-target="mentee" data-val="I have identified my weak areas and am attending remedial sessions.">Remedial Help</span>
                <span class="chip" data-target="mentee" data-val="I am balancing my project work and regular academics effectively.">Project Balance</span>
                <span class="chip" data-target="mentee" data-val="I am working on improving my internal marks in core subjects.">Mark Focus</span>
                <span class="chip" data-target="mentee" data-val="I am actively participating in club activities along with studies.">Active Student</span>
            </div>
            <textarea id="mentee_response" placeholder="Mentor guidance goes here..." required></textarea>
        </div>

        <div class="card">
            <div class="card-title">Step 3 &mdash; Parent's Feedback</div>
            <div class="section-label"><div class="dot"></div>Quick Selection</div>
            <div class="chips">
                <span class="chip" data-target="parent" data-val="We are happy with the progress and monitoring studies at home.">Satisfied</span>
                <span class="chip" data-target="parent" data-val="We have noticed a significant improvement in discipline and habits.">Improved</span>
                <span class="chip" data-target="parent" data-val="We will ensure our child maintains 100% attendance hereafter.">Attendance Fix</span>
                <span class="chip" data-target="parent" data-val="We appreciate the mentor's efforts and personalized guidance.">Appreciated</span>
                <span class="chip" data-target="parent" data-val="We are providing full support and restricted distractions at home.">Home Support</span>
                <span class="chip" data-target="parent" data-val="We request more frequent updates on the internal test performance.">Update Request</span>
            </div>
            <textarea id="parent_response" placeholder="Parent response goes here..." required></textarea>
        </div>

        <button type="submit" class="btn" id="submitBtn">Generate Report</button>
        <div class="progress-bar" id="progressBar"><div class="progress-fill" id="progressFill"></div></div>
        <div class="status" id="status"></div>
    </form>

    <div class="footer">SIMATS &bull; AUTOMATION TOOL v2.0</div>
</div>

<script>
    // Enhanced Selection Logic
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const target = chip.dataset.target;
            document.querySelectorAll(`.chip[data-target="${target}"]`).forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            document.getElementById(target + '_response').value = chip.dataset.val;
        });
    });

    document.getElementById('file').addEventListener('change', function() {
        if (this.files.length > 0) {
            document.getElementById('fileNameText').textContent = this.files[0].name;
            document.getElementById('fileName').style.display = 'flex';
            document.getElementById('uploadBox').classList.add('has-file');
        }
    });

    // Form Logic
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('submitBtn');
        const status = document.getElementById('status');
        const bar = document.getElementById('progressBar');
        const fill = document.getElementById('progressFill');
        
        submitBtn.disabled = true;
        status.className = 'status loading';
        status.innerHTML = '<div class="spinner"></div> Creating your premium document...';
        bar.style.display = 'block';
        
        let p = 0;
        const interval = setInterval(() => { p = Math.min(p + 5, 90); fill.style.width = p + '%'; }, 200);

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
                a.download = 'GP_Report_' + Date.now() + '.pdf';
                a.click();
                status.className = 'status success';
                status.innerHTML = 'Report Generated Successfully!';
            } else {
                throw new Error('Failed to process file');
            }
        } catch (err) {
            status.className = 'status error';
            status.innerHTML = err.message;
        } finally {
            submitBtn.disabled = false;
            setTimeout(() => { bar.style.display = 'none'; fill.style.width = '0'; }, 2000);
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
            return jsonify({'error': 'Only PPT and PPTX files allowed'}), 400

        os.makedirs('uploads', exist_ok=True)
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = os.path.join('uploads', f"{timestamp}_{filename}")
        file.save(input_path)

        output_pdf_path = os.path.join('uploads', f"{timestamp}_output.pdf")

        # Your backend logic preserved
        success, file_type = process_ppt_to_pdf(
            input_ppt_path=input_path,
            output_pdf_path=output_pdf_path,
            parent_response=parent_response,
            mentee_response=mentee_response,
            keep_slides=3
        )

        try:
            os.unlink(input_path)
        except:
            pass

        if success and file_type == "pdf" and os.path.exists(output_pdf_path):
            return send_file(output_pdf_path, as_attachment=True,
                           download_name='GP_Report.pdf',
                           mimetype='application/pdf')

        pptx_output = output_pdf_path.replace('.pdf', '.pptx')
        if success and file_type == "pptx" and os.path.exists(pptx_output):
            return send_file(pptx_output, as_attachment=True,
                           download_name='GP_Report.pptx',
                           mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')

        return jsonify({'error': 'Failed to convert presentation'}), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=10000)
