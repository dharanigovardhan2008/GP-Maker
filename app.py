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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #050505;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 85% 30%, rgba(168, 85, 247, 0.08) 0%, transparent 50%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 40px 16px;
            color: #e2e8f0;
        }

        .page { width: 100%; max-width: 500px; position: relative; z-index: 1; }

        /* Header */
        .header { text-align: center; padding: 20px 0 40px; }
        .logo-container {
            width: 64px; height: 64px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            display: inline-flex; align-items: center; justify-content: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        .header h1 { 
            color: #ffffff; font-size: 28px; font-weight: 600; 
            letter-spacing: -0.5px; margin-bottom: 6px;
        }
        .header p { 
            color: #94a3b8; font-size: 13px; font-weight: 400;
            letter-spacing: 1px; text-transform: uppercase;
        }

        /* Cards (Glassmorphism) */
        .card {
            background: rgba(20, 20, 22, 0.6);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 24px;
            padding: 28px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            transition: border-color 0.3s ease;
        }
        .card:hover { border-color: rgba(255, 255, 255, 0.08); }

        .card-title {
            font-size: 11px; font-weight: 600;
            letter-spacing: 0.15em; text-transform: uppercase;
            color: #64748b;
            margin-bottom: 20px;
            display: flex; align-items: center; gap: 10px;
        }
        .card-title::after {
            content: ''; flex-grow: 1; height: 1px;
            background: linear-gradient(90deg, rgba(255,255,255,0.05) 0%, transparent 100%);
        }

        /* Upload box */
        .upload-box {
            border: 1px dashed rgba(255, 255, 255, 0.15);
            border-radius: 16px;
            padding: 36px 20px;
            text-align: center;
            background: rgba(255, 255, 255, 0.01);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }
        .upload-box:hover, .upload-box.has-file {
            border-color: #818cf8;
            background: rgba(129, 140, 248, 0.03);
        }
        .upload-box input[type="file"] {
            position: absolute; inset: 0;
            opacity: 0; cursor: pointer; width: 100%; height: 100%;
        }
        .upload-icon { 
            margin-bottom: 12px; display: inline-block;
            transition: transform 0.3s ease;
        }
        .upload-box:hover .upload-icon { transform: translateY(-3px); }
        .upload-text { color: #94a3b8; font-size: 14px; line-height: 1.6; font-weight: 300; }
        .upload-text strong { color: #e2e8f0; font-weight: 500; }
        .file-name {
            margin-top: 16px; font-size: 13px;
            color: #818cf8; font-weight: 500;
            display: none; align-items: center; justify-content: center; gap: 8px;
            background: rgba(129, 140, 248, 0.1);
            padding: 8px 16px; border-radius: 8px;
            width: fit-content; margin-inline: auto;
        }

        /* Section labels */
        .section-label {
            font-size: 13px; font-weight: 500;
            color: #cbd5e1; margin-bottom: 14px;
            display: flex; align-items: center; gap: 8px;
        }
        .dot {
            width: 6px; height: 6px; border-radius: 50%;
            background: #818cf8;
            box-shadow: 0 0 10px #818cf8;
        }

        /* Chips */
        .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
        .chip {
            font-size: 12px; font-weight: 400;
            padding: 8px 16px;
            border-radius: 100px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.02);
            color: #94a3b8;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }
        .chip:hover { border-color: rgba(255,255,255,0.2); color: #e2e8f0; }
        .chip.active {
            background: #e2e8f0;
            color: #0f172a; 
            border-color: #e2e8f0;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(226, 232, 240, 0.15);
        }

        /* Textarea */
        textarea {
            width: 100%; padding: 16px;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            background: rgba(0,0,0,0.2);
            font-size: 14px; color: #f8fafc;
            resize: vertical; min-height: 100px;
            font-family: inherit; outline: none;
            transition: all 0.3s ease; line-height: 1.6;
        }
        textarea::placeholder { color: #475569; }
        textarea:focus { 
            border-color: #818cf8; 
            background: rgba(0,0,0,0.4);
            box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.1);
        }

        /* Submit button */
        .btn {
            width: 100%; padding: 18px;
            background: linear-gradient(135deg, #4f46e5, #9333ea);
            color: #fff; border: none;
            border-radius: 16px;
            font-size: 15px; font-weight: 600;
            cursor: pointer;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.25);
            margin-top: 10px;
            display: flex; justify-content: center; align-items: center; gap: 10px;
        }
        .btn:hover { 
            box-shadow: 0 12px 30px rgba(79, 70, 229, 0.4); 
            transform: translateY(-2px);
        }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { 
            background: rgba(255,255,255,0.05); 
            box-shadow: none; cursor: not-allowed; 
            color: rgba(255,255,255,0.2); 
            transform: none;
        }

        /* Status */
        .status {
            margin-top: 20px; padding: 16px;
            border-radius: 16px; text-align: center;
            display: none; font-size: 14px; font-weight: 500;
            align-items: center; justify-content: center; gap: 10px;
            animation: fadeIn 0.4s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .status.loading { background: rgba(255,255,255,0.03); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.05); display: flex;}
        .status.success { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); display: flex;}
        .status.error { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); display: flex;}

        .status-icon { width: 18px; height: 18px; }

        /* Spinner */
        .spinner {
            display: inline-block; width: 18px; height: 18px;
            border: 2px solid rgba(255,255,255,0.1);
            border-top: 2px solid #818cf8;
            border-radius: 50%;
            animation: spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Footer */
        .footer {
            text-align: center; color: #475569;
            font-size: 11px; padding-top: 30px;
            letter-spacing: 0.1em; font-weight: 500;
        }

        /* Progress bar */
        .progress-bar {
            height: 4px; background: rgba(255,255,255,0.05);
            border-radius: 4px; margin-top: 24px; overflow: hidden;
            display: none; width: 100%;
        }
        .progress-fill {
            height: 100%; width: 0%;
            background: linear-gradient(90deg, #4f46e5, #c084fc);
            border-radius: 4px;
            transition: width 0.4s ease;
            box-shadow: 0 0 10px rgba(192, 132, 252, 0.5);
        }
    </style>
</head>
<body>
<div class="page">

    <div class="header">
        <div class="logo-container">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="url(#grad)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#818cf8" />
                        <stop offset="100%" stop-color="#c084fc" />
                    </linearGradient>
                </defs>
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
            </svg>
        </div>
        <h1>GP Maker</h1>
        <p>SIMATS Engineering &bull; Mentor Portal</p>
    </div>

    <form id="uploadForm">

        <div class="card">
            <div class="card-title">Step 1 &mdash; Document</div>
            <div class="upload-box" id="uploadBox">
                <input type="file" id="file" accept=".ppt,.pptx" required>
                <div class="upload-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                </div>
                <div class="upload-text">
                    <strong>Click to upload</strong> or drag and drop<br>
                    PPT, PPTX formats supported
                </div>
                <div class="file-name" id="fileName">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    <span id="fileNameText"></span>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Step 2 &mdash; Mentee Response</div>
            <div class="section-label"><div class="dot"></div>Quick Selection</div>
            <div class="chips">
                <span class="chip" data-target="mentee" data-val="I am doing well and attending all classes regularly.">Doing well</span>
                <span class="chip" data-target="mentee" data-val="I understand the topics covered and will work harder.">Will work harder</span>
                <span class="chip" data-target="mentee" data-val="I am actively participating in classes and completing assignments on time.">Active &amp; on time</span>
                <span class="chip" data-target="mentee" data-val="I need more guidance in some subjects and will seek help from my mentor.">Need guidance</span>
                <span class="chip" data-target="mentee" data-val="I am focused on improving my academic performance this semester.">Focused on improvement</span>
            </div>
            <textarea id="mentee_response" placeholder="Select an option above or type a custom response..." required></textarea>
        </div>

        <div class="card">
            <div class="card-title">Step 3 &mdash; Parent's Response</div>
            <div class="section-label"><div class="dot"></div>Quick Selection</div>
            <div class="chips">
                <span class="chip" data-target="parent" data-val="My child is performing well and we are happy with the progress.">Happy with progress</span>
                <span class="chip" data-target="parent" data-val="We are monitoring the studies closely and providing full support at home.">Providing support</span>
                <span class="chip" data-target="parent" data-val="We appreciate the mentor's efforts and will encourage our child further.">Appreciate efforts</span>
                <span class="chip" data-target="parent" data-val="We are concerned and will ensure our child attends all classes regularly.">Concerned, will act</span>
                <span class="chip" data-target="parent" data-val="Our child is improving and we are satisfied with the current progress.">Satisfied</span>
            </div>
            <textarea id="parent_response" placeholder="Select an option above or type a custom response..." required></textarea>
        </div>

        <button type="submit" class="btn" id="submitBtn">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            Generate Document
        </button>

        <div class="progress-bar" id="progressBar">
            <div class="progress-fill" id="progressFill"></div>
        </div>

        <div class="status" id="status"></div>

    </form>

    <div class="footer">GP MAKER &bull; SIMATS ENGINEERING</div>
</div>

<script>
    // Chip selection
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const target = chip.dataset.target;
            document.querySelectorAll(`.chip[data-target="${target}"]`).forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            document.getElementById(target + '_response').value = chip.dataset.val;
        });
    });

    // Deselect chip on manual type
    document.querySelectorAll('textarea').forEach(ta => {
        ta.addEventListener('input', () => {
            const target = ta.id.replace('_response', '');
            const val = ta.value.trim();
            document.querySelectorAll(`.chip[data-target="${target}"]`).forEach(c => {
                c.classList.toggle('active', c.dataset.val === val);
            });
        });
    });

    // File input display
    document.getElementById('file').addEventListener('change', function() {
        if (this.files.length > 0) {
            const name = this.files[0].name;
            document.getElementById('fileNameText').textContent = name;
            document.getElementById('fileName').style.display = 'flex';
            document.getElementById('uploadBox').classList.add('has-file');
            
            // Highlight icon color
            document.querySelector('.upload-icon svg').setAttribute('stroke', '#818cf8');
        }
    });

    // Fake progress bar animation
    function animateProgress(callback) {
        const bar = document.getElementById('progressBar');
        const fill = document.getElementById('progressFill');
        bar.style.display = 'block';
        let w = 0;
        const iv = setInterval(() => {
            w = Math.min(w + Math.random() * 8, 85);
            fill.style.width = w + '%';
            if (w >= 85) clearInterval(iv);
        }, 300);
        return { complete: () => { clearInterval(iv); fill.style.width = '100%'; setTimeout(() => { bar.style.display = 'none'; fill.style.width = '0%'; }, 600); }};
    }

    // Form submit
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('submitBtn');
        const status = document.getElementById('status');
        const file = document.getElementById('file').files[0];

        if (!file) { alert('Please select a file'); return; }

        submitBtn.disabled = true;
        status.className = 'status loading';
        status.innerHTML = '<span class="spinner"></span> Processing presentation...';

        const progress = animateProgress();

        const formData = new FormData();
        formData.append('file', file);
        formData.append('parent_response', document.getElementById('parent_response').value);
        formData.append('mentee_response', document.getElementById('mentee_response').value);

        try {
            const response = await fetch('/convert', { method: 'POST', body: formData });

            progress.complete();

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const contentType = response.headers.get('content-type');
                a.download = 'GP_Report' + (contentType && contentType.includes('pdf') ? '.pdf' : '.pptx');
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                status.className = 'status success';
                status.innerHTML = '<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Conversion successful';

                setTimeout(() => {
                    document.getElementById('uploadForm').reset();
                    document.getElementById('fileName').style.display = 'none';
                    document.getElementById('uploadBox').classList.remove('has-file');
                    document.querySelector('.upload-icon svg').setAttribute('stroke', '#64748b');
                    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                    status.style.display = 'none';
                }, 4000);
            } else {
                const err = await response.json();
                throw new Error(err.error || 'Conversion failed');
            }
        } catch (error) {
            progress.complete();
            status.className = 'status error';
            status.innerHTML = '<svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg> ' + error.message;
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
