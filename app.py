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
    <title>GP Maker — SIMATS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #0f0c29;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 24px 16px 40px;
        }

        .page { width: 100%; max-width: 480px; }

        /* Header */
        .header { text-align: center; padding: 32px 0 28px; }
        .logo {
            width: 56px; height: 56px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 18px;
            display: inline-flex; align-items: center; justify-content: center;
            margin-bottom: 14px; font-size: 26px;
            box-shadow: 0 8px 24px rgba(102,126,234,0.35);
        }
        .header h1 { color: #fff; font-size: 24px; font-weight: 700; letter-spacing: -0.4px; }
        .header p { color: rgba(255,255,255,0.45); font-size: 13px; margin-top: 5px; }

        /* Cards */
        .card {
            background: #16213e;
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 14px;
        }

        .card-title {
            font-size: 10px; font-weight: 700;
            letter-spacing: 0.1em; text-transform: uppercase;
            color: rgba(255,255,255,0.35);
            margin-bottom: 14px;
        }

        /* Upload box */
        .upload-box {
            border: 1.5px dashed rgba(102,126,234,0.45);
            border-radius: 14px;
            padding: 28px 16px;
            text-align: center;
            background: rgba(102,126,234,0.06);
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }
        .upload-box:hover, .upload-box.has-file {
            border-color: #667eea;
            background: rgba(102,126,234,0.12);
        }
        .upload-box input[type="file"] {
            position: absolute; inset: 0;
            opacity: 0; cursor: pointer; width: 100%; height: 100%;
        }
        .upload-icon { font-size: 30px; margin-bottom: 8px; display: block; }
        .upload-text { color: rgba(255,255,255,0.55); font-size: 13px; line-height: 1.5; }
        .upload-text strong { color: #667eea; }
        .file-name {
            margin-top: 10px; font-size: 12px;
            color: #667eea; font-weight: 600;
            display: none;
        }

        /* Section labels */
        .section-label {
            font-size: 13px; font-weight: 600;
            color: #fff; margin-bottom: 11px;
            display: flex; align-items: center; gap: 8px;
        }
        .dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            flex-shrink: 0;
        }

        /* Chips */
        .chips { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 12px; }
        .chip {
            font-size: 12px; padding: 6px 13px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.05);
            color: rgba(255,255,255,0.55);
            cursor: pointer;
            transition: all 0.15s;
            user-select: none;
        }
        .chip:hover { border-color: #667eea; color: #a0a8f8; }
        .chip.active {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff; border-color: transparent;
            box-shadow: 0 3px 10px rgba(102,126,234,0.35);
        }

        /* Textarea */
        textarea {
            width: 100%; padding: 12px 14px;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            background: rgba(255,255,255,0.05);
            font-size: 14px; color: #fff;
            resize: vertical; min-height: 76px;
            font-family: inherit; outline: none;
            transition: border 0.2s; line-height: 1.5;
        }
        textarea::placeholder { color: rgba(255,255,255,0.22); }
        textarea:focus { border-color: #667eea; background: rgba(102,126,234,0.07); }

        /* Submit button */
        .btn {
            width: 100%; padding: 17px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff; border: none;
            border-radius: 14px;
            font-size: 16px; font-weight: 700;
            cursor: pointer;
            letter-spacing: 0.2px;
            transition: opacity 0.2s, transform 0.1s;
            box-shadow: 0 8px 24px rgba(102,126,234,0.4);
            margin-top: 4px;
        }
        .btn:hover { opacity: 0.92; }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { background: rgba(255,255,255,0.1); box-shadow: none; cursor: not-allowed; color: rgba(255,255,255,0.3); }

        /* Status */
        .status {
            margin-top: 14px; padding: 14px 16px;
            border-radius: 12px; text-align: center;
            display: none; font-size: 14px; font-weight: 500;
        }
        .status.loading { background: rgba(102,126,234,0.15); color: #a0a8f8; border: 1px solid rgba(102,126,234,0.25); }
        .status.success { background: rgba(29,158,117,0.15); color: #5dcaa5; border: 1px solid rgba(29,158,117,0.25); }
        .status.error { background: rgba(226,75,74,0.15); color: #f09595; border: 1px solid rgba(226,75,74,0.25); }

        /* Spinner */
        .spinner {
            display: inline-block; width: 15px; height: 15px;
            border: 2px solid rgba(160,168,248,0.3);
            border-top: 2px solid #a0a8f8;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px; vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Footer */
        .footer {
            text-align: center; color: rgba(255,255,255,0.18);
            font-size: 11px; padding-top: 20px;
            letter-spacing: 0.05em;
        }

        /* Progress bar */
        .progress-bar {
            height: 3px; background: rgba(255,255,255,0.08);
            border-radius: 2px; margin-top: 12px; overflow: hidden;
            display: none;
        }
        .progress-fill {
            height: 100%; width: 0%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 2px;
            transition: width 0.4s ease;
        }
    </style>
</head>
<body>
<div class="page">

    <div class="header">
        <div class="logo">📊</div>
        <h1>GP Maker</h1>
        <p>SIMATS Engineering &mdash; Mentor Portal</p>
    </div>

    <form id="uploadForm">

        <div class="card">
            <div class="card-title">Step 1 &mdash; Upload Presentation</div>
            <div class="upload-box" id="uploadBox">
                <input type="file" id="file" accept=".ppt,.pptx" required>
                <span class="upload-icon">📁</span>
                <div class="upload-text">
                    <strong>Tap to choose file</strong><br>
                    Supports PPT and PPTX formats
                </div>
                <div class="file-name" id="fileName"></div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Step 2 &mdash; Mentee Response</div>
            <div class="section-label"><div class="dot"></div>Quick picks</div>
            <div class="chips">
                <span class="chip" data-target="mentee" data-val="I am doing well and attending all classes regularly.">Doing well</span>
                <span class="chip" data-target="mentee" data-val="I understand the topics covered and will work harder.">Will work harder</span>
                <span class="chip" data-target="mentee" data-val="I am actively participating in classes and completing assignments on time.">Active &amp; on time</span>
                <span class="chip" data-target="mentee" data-val="I need more guidance in some subjects and will seek help from my mentor.">Need guidance</span>
                <span class="chip" data-target="mentee" data-val="I am focused on improving my academic performance this semester.">Focused on improvement</span>
            </div>
            <textarea id="mentee_response" placeholder="Select a quick pick or type your own response..." required></textarea>
        </div>

        <div class="card">
            <div class="card-title">Step 3 &mdash; Parent's Response</div>
            <div class="section-label"><div class="dot"></div>Quick picks</div>
            <div class="chips">
                <span class="chip" data-target="parent" data-val="My child is performing well and we are happy with the progress.">Happy with progress</span>
                <span class="chip" data-target="parent" data-val="We are monitoring the studies closely and providing full support at home.">Providing support</span>
                <span class="chip" data-target="parent" data-val="We appreciate the mentor's efforts and will encourage our child further.">Appreciate efforts</span>
                <span class="chip" data-target="parent" data-val="We are concerned and will ensure our child attends all classes regularly.">Concerned, will act</span>
                <span class="chip" data-target="parent" data-val="Our child is improving and we are satisfied with the current progress.">Satisfied</span>
            </div>
            <textarea id="parent_response" placeholder="Select a quick pick or type your own response..." required></textarea>
        </div>

        <button type="submit" class="btn" id="submitBtn">Convert to PDF</button>

        <div class="progress-bar" id="progressBar">
            <div class="progress-fill" id="progressFill"></div>
        </div>

        <div class="status" id="status"></div>

    </form>

    <div class="footer">GP MAKER &bull; SIMATS ENGINEERING &bull; MENTOR PORTAL</div>
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
            const nameEl = document.getElementById('fileName');
            nameEl.textContent = '✓ ' + name;
            nameEl.style.display = 'block';
            document.getElementById('uploadBox').classList.add('has-file');
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
        status.style.display = 'block';
        status.innerHTML = '<span class="spinner"></span>Processing your presentation...';

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
                status.innerHTML = '✅ Done! Your file has been downloaded.';

                setTimeout(() => {
                    document.getElementById('uploadForm').reset();
                    document.getElementById('fileName').style.display = 'none';
                    document.getElementById('uploadBox').classList.remove('has-file');
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
            status.innerHTML = '❌ ' + error.message;
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
