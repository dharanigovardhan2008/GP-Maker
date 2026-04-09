import os
import shutil
import subprocess
import tempfile
from pptx import Presentation


class PPTProcessor:
    def __init__(self):
        self.presentation = None

    def load_presentation(self, ppt_path):
        try:
            self.presentation = Presentation(ppt_path)
            print(f"Loaded presentation with {len(self.presentation.slides)} slides")
            return True
        except Exception as e:
            print(f"Error loading presentation: {e}")
            return False

    def keep_last_n_slides(self, n=3):
        if not self.presentation:
            return False
        total = len(self.presentation.slides)
        if total <= n:
            return True
        for _ in range(total - n):
            rId = self.presentation.slides._sldIdLst[0].rId
            self.presentation.part.drop_rel(rId)
            del self.presentation.slides._sldIdLst[0]
        print(f"Kept last {n} slides")
        return True

    def replace_response_boxes(self, mentee_response, parent_response):
        if not self.presentation:
            return False

        last_slide = self.presentation.slides[-1]

        boxes = [
            shape for shape in last_slide.shapes
            if hasattr(shape, 'text_frame')
            and shape.text_frame.text.strip().lower() == 'text'
        ]

        if len(boxes) < 2:
            print(f"Warning: found {len(boxes)} boxes, expected 2")
            for box in boxes:
                for para in box.text_frame.paragraphs:
                    for run in para.runs:
                        if run.text.strip().lower() == 'text':
                            run.text = mentee_response
            return True

        boxes.sort(key=lambda s: s.left)

        def set_text(shape, new_text):
            first = True
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if first:
                        run.text = new_text
                        first = False
                    else:
                        run.text = ''

        set_text(boxes[0], mentee_response)
        set_text(boxes[1], parent_response)
        print(f"Mentee: '{mentee_response}' | Parent: '{parent_response}'")
        return True

    def save_as_pptx(self, path):
        try:
            self.presentation.save(path)
            print(f"Saved to {path}")
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def convert_to_pdf(self, pptx_path, pdf_path):
        try:
            out_dir = os.path.dirname(os.path.abspath(pdf_path))
            result = subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf",
                 "--outdir", out_dir, os.path.abspath(pptx_path)],
                capture_output=True, text=True, timeout=120
            )
            base = os.path.splitext(os.path.basename(pptx_path))[0]
            generated = os.path.join(out_dir, base + ".pdf")
            if os.path.exists(generated):
                shutil.move(generated, pdf_path)
                print(f"PDF saved: {pdf_path}")
                return True
            print(f"LibreOffice error: {result.stderr}")
            return False
        except FileNotFoundError:
            print("LibreOffice not found")
            return False
        except Exception as e:
            print(f"Conversion error: {e}")
            return False


def process_ppt_to_pdf(input_ppt_path, output_pdf_path, parent_response, mentee_response, keep_slides=3):
    print("\n=== Starting Processing ===")
    processor = PPTProcessor()

    if not processor.load_presentation(input_ppt_path):
        return False, None

    if not processor.keep_last_n_slides(keep_slides):
        return False, None

    if not processor.replace_response_boxes(mentee_response, parent_response):
        return False, None

    temp_dir = tempfile.gettempdir()
    temp_pptx = os.path.join(temp_dir, "temp_presentation.pptx")

    if not processor.save_as_pptx(temp_pptx):
        return False, None

    # Try PDF first
    success = processor.convert_to_pdf(temp_pptx, output_pdf_path)

    try:
        os.unlink(temp_pptx)
    except:
        pass

    if success and os.path.exists(output_pdf_path):
        print("=== Done: PDF ===")
        return True, "pdf"

    # Fallback: save as PPTX
    print("PDF failed, saving as PPTX instead")
    pptx_output = output_pdf_path.replace('.pdf', '.pptx')
    processor2 = PPTProcessor()
    processor2.load_presentation(input_ppt_path)
    processor2.keep_last_n_slides(keep_slides)
    processor2.replace_response_boxes(mentee_response, parent_response)
    processor2.save_as_pptx(pptx_output)

    if os.path.exists(pptx_output):
        print("=== Done: PPTX ===")
        return True, "pptx"

    return False, None
