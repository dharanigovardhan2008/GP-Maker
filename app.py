from flask import Flask, request, send_file, jsonify, render_template_string
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from ppt_processor import process_ppt_to_pdf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs('uploads', exist_ok=True)

ALLOWED_EXTENSIONS = {'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PPT to PDF Converter</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 30px 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 560px;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 26px;
        }
        .form-group { margin-bottom: 24px; }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            color: #444;
            font-size: 14px;
        }
        .section-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #999;
            margin-bottom: 7px;
        }
        input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 2px dashed #ddd;
            border-radius: 8px;
            background: #f8f9fa;
            cursor: pointer;
        }
        input[type="file"]:hover { border-color: #667eea; }
        .chips {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 8px;
        }
        .chip {
            font-size: 12px;
            padding: 5px 12px;
            border-radius: 20px;
            border: 1.5px solid #ddd;
            background: #f8f9fa;
            color: #555;
            cursor: pointer;
            transition: all 0.15s;
            user-select: none;
        }
        .chip:hover { border-color: #667eea; color: #667eea; background: #f0efff; }
        .chip.active { background: #667eea; color: white; border-color: #667eea; }
        textarea {
            width: 100%;
            padding: 10px 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            resize: vertical;
            min-height: 75px;
            font-family: inherit;
            transition: border-color 0.3s;
            color: #333;
        }
        textarea:focus { outline: none; border-color: #667eea; }
        .hint { font-size: 11px; color: #aaa; margin-top: 4px; }
        .divider { border: none; border-top: 1px solid #eee; margin: 24px 0; }
        button[type="submit"] {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            margin-top: 8px;
        }
        button[type="submit"]:hover { transform: translateY(-2px); }
        button[type="submit"]:disabled { background: #ccc; cursor: not-allowed; transform: none; }
        .status {
            margin-top: 16px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            display: none;
            font-size: 14px;
        }
        .status.loading { background: #e3f2fd; color: #1976d2; }
        .status.success { background: #e8f5e9; color: #2e7d32; }
        .status.error { background: #ffebee; color: #c62828; }
        .spinner {
            display: inline-block;
            width: 16px; height: 16px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        @keyframes spin { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }
    </style>
</head>
<body>
<div class="container">
    <h1>📊 PPT to PDF Converter</h1>
    <form id="uploadForm">

        <div class="form-group">
            <label>📁 Select PowerPoint File</label>
            <input type="file" id="file" accept=".ppt,.pptx" required>
        </div>

        <hr class="divider">

        <!-- MENTEE RESPONSE -->
        <div class="form-group">
            <label>👤 Mentee Response</label>
            <p class="section-label">Quick picks</p>
            <div class="chips" id="mentee-chips">
                <span class="chip" data-target="mentee" data-val="I am doing well and attending all classes regularly.">Doing well</span>
                <span class="chip" data-target="mentee" data-val="I understand the topics covered and will work harder.">Will work harder</span>
                <span class="chip" data-target="mentee" data-val="I am actively participating in classes and completing assignments on time.">Active &amp; on time</span>
                <span class="chip" data-target="mentee" data-val="I need more guidance in some subjects and will seek help from my mentor.">Need guidance</span>
                <span class="chip" data-target="mentee" data-val="I am focused on improving my academic performance this semester.">Focused on improvement</span>
            </div>
            <textarea id="mentee_response" placeholder="Select a quick pick or type your own..." required></textarea>
            <p class="hint">This will replace the text inside the Mentee Response box in the slide.</p>
        </div>

        <!-- PARENT RESPONSE -->
        <div class="form-group">
            <label>👨‍👩‍👧 Parent's Response</label>
            <p class="section-label">Quick picks</p>
            <div class="chips" id="parent-chips">
                <span class="chip" data-target="parent" data-val="My child is performing well and we are happy with the progress.">Happy with progress</span>
                <span class="chip" data-target="parent" data-val="We are monitoring the studies closely and providing full support at home.">Providing support</span>
                <span class="chip" data-target="parent" data-val="We appreciate the mentor's efforts and will encourage our child further.">Appreciate efforts</span>
                <span class="chip" data-target="parent" data-val="We are concerned and will ensure our child attends all classes regularly.">Concerned, will act</span>
                <span class="chip" data-target="parent" data-val="Our child is improving and we are satisfied with the current progress.">Satisfied</span>
            </div>
            <textarea id="parent_response" placeholder="Select a quick pick or type your own..." required></textarea>
            <p class="hint">This will replace the text inside the Parent's Response box in the slide.</p>
        </div>

        <button type="submit" id="submitBtn">🚀 Convert to PDF</button>
        <div class="status" id="status"></div>

    </form>
</div>

<script>
    // Chip click — fill textarea and highlight chip
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const target = chip.dataset.target;
            document.querySelectorAll(`.chip[data-target="${target}"]`).forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            document.getElementById(target + '_response').value = chip.dataset.val;
        });
    });

    // If user types manually, deselect chips
    document.querySelectorAll('textarea').forEach(ta => {
        ta.addEventListener('input', () => {
            const target = ta.id.replace('_response', '');
            const val = ta.value.trim();
            document.querySelectorAll(`.chip[data-target="${target}"]`).forEach(c => {
                c.classList.toggle('active', c.dataset.val === val);
            });
        });
    });

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
        status.innerHTML = '<span class="spinner"></span>Processing your file...';

        const formData = new FormData();
        formData.append('file', file);
        formData.append('parent_response', document.getElementById('parent_response').value);
        formData.append('mentee_response', document.getElementById('mentee_response').value);

        try {
            const response = await fetch('/convert', { method: 'POST', body: formData });
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const contentType = response.headers.get('content-type');
                a.download = 'converted_presentation' + (contentType.includes('pdf') ? '.pdf' : '.pptx');
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                status.className = 'status success';
                status.innerHTML = '✅ Converted successfully — download started!';
                setTimeout(() => {
                    document.getElementById('uploadForm').reset();
                    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                    status.style.display = 'none';
                }, 3000);
            } else {
                throw new Error('Conversion failed');
            }
        } catch (error) {
            status.className = 'status error';
            status.innerHTML = '❌ Error: ' + error.message;
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
            return jsonify({'error': 'Invalid file type. Only PPT and PPTX files are allowed'}), 400

        os.makedirs('uploads', exist_ok=True)
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = os.path.join('uploads', f"{timestamp}_{filename}")
        file.save(input_path)

        output_pdf_path = os.path.join('uploads', f"{timestamp}_output.pdf")
        success = process_ppt_to_pdf(
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

        if success and os.path.exists(output_pdf_path):
            return send_file(output_pdf_path, as_attachment=True,
                             download_name='converted_presentation.pdf',
                             mimetype='application/pdf')

        output_pptx_path = output_pdf_path.replace('.pdf', '_converted.pptx')
        if os.path.exists(output_pptx_path):
            return send_file(output_pptx_path, as_attachment=True,
                             download_name='converted_presentation.pptx',
                             mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')

        return jsonify({'error': 'Failed to convert presentation'}), 500

    except Exception as e:
        print(f"Error in conversion: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("PPT to PDF Converter - Starting...")
    print("="*50)
    print("\nOpen your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
