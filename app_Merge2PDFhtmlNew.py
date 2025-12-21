


#------------------------------------------------------------- SuN -- 2025-Dec-13 ---- {
'''
   Program for Merging Tender Documents from Excel Data Sheet Named "MergerSheet" and Generating a PDF File Output
   The set of normal Word Files have column names defined within double braces {{ }}
   Eg:-  {{tenderName}} {{tenderDate}} 
'''
#------------------------------------------------------------- SuN -- 2025-Dec-13 ---- }

from flask import Flask, request, render_template_string, send_file, session, jsonify
import os, uuid
import pandas as pd
from docx import Document
from docxcompose.composer import Composer
from docx2pdf import convert

from config import config
import merge2pdf
from merge2pdf import mail_merge_to_pdf

app = Flask(__name__)

UPLOAD_FOLDER_BASE = config["uploads_dir"]
OUTPUT_FOLDER_BASE = config["outputs_dir"]
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
os.makedirs(OUTPUT_FOLDER_BASE, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Mail Merge Tool</title>

<style>
body {
    background: linear-gradient(120deg,#e0eafc,#cfdef3);
    font-family: Arial, sans-serif;
}
.container {
    width: 720px;
    margin: 30px auto;
    background: #fff;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,.15);
}    
.containerIn {  
    width: 600px;
    margin: 60px auto;
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0,0,0,.15);
    text-align: center;
    
}
h2 { text-align:center; color:#2c3e50; }
label { font-weight:bold; display:block; margin-top:15px; }

input[type=text] {
    width:100%; padding:10px;
    border-radius:6px; border:1px solid #ccc;
}

.dropzone {
    border:2px dashed #3498db;
    padding:25px;
    text-align:center;
    color:#555;
    border-radius:8px;
    margin-top:10px;
    cursor:pointer;
}
.dropzone.dragover { background:#ecf3ff; }

.file-list {
    margin-top:10px;
}
.file-item {
    display:flex;
    justify-content:space-between;
    align-items:center;
    background:#f4f6f8;
    padding:8px;
    margin-bottom:6px;
    border-radius:6px;
}
.file-item span { flex:1; }

.file-item button {
    margin-left:4px;
    border:none;
    background:#3498db;
    color:white;
    padding:4px 8px;
    border-radius:4px;
    cursor:pointer;
}
.file-item button.delete {
    background:#e74c3c;
}

.progress {
    margin-top:20px;
    height:20px;
    background:#eee;
    border-radius:10px;
    overflow:hidden;
}
.progress-bar {
    height:100%;
    width:0%;
    background:#27ae60;
    transition:width .4s;
}

.buttons {
    display:flex;
    justify-content:space-between;
    margin-top:25px;
}
button.submit {
    width:48%; background:#27ae60;
}
button.reset {
    width:48%; background:#e74c3c;
}
button.submit, button.reset {
    border:none; color:white;
    padding:12px; border-radius:6px;
    cursor:pointer; font-size:15px;
}

footer {
    text-align:center;
    margin-top:10px;
    font-size:12px; color:gray;
}
</style>
</head>

<body>
<div id="result_page">
</div>
<div class="container">
<h2>📄 Document Merge Automation</h2>

<form id="mergeForm" enctype="multipart/form-data">

<div class="containerIn">
<hr/>
<label><u>Input Data File (.xlsx)</u></label><br/>
<input type="file" name="excel" required>
<hr/>
<div>

<label>Sheet Name</label>
<input type="text" name="sheet" placeholder="Sheet1" value="MergerSheet" required>

<label>(<i>.docx</i>) Template Files (Drag, Drop & Reorder)</label>
<div class="dropzone" id="dropzone">Drop .docx files here</div>
<div class="file-list" id="fileList"></div>

<input type="hidden" name="fileOrder" id="fileOrder">

<label>Output .docx Name</label>
<input type="text" name="output_docx" placeholder="merged.docx" value="merged.docx" required>

<label>Output .PDF Name</label>
<input type="text" name="output_pdf" placeholder="merged.pdf" value="merged.pdf" required>

<div class="progress">
    <div class="progress-bar" id="progressBar"></div>
</div>

<div class="buttons">
    <button type="reset" class="reset" onclick="resetForm()">Reset</button>
    <button type="submit" class="submit">Submit</button>
</div>
</form>
</div>


<footer>Document Merge Web Tool - Suresh Nambiar</footer>

<script>
let files = [];

const dropzone = document.getElementById("dropzone");
const fileList = document.getElementById("fileList");
const fileOrder = document.getElementById("fileOrder");

dropzone.onclick = () => {
    let input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.accept = ".docx";
    input.onchange = e => addFiles(e.target.files);
    input.click();
};

dropzone.ondragover = e => { e.preventDefault(); dropzone.classList.add("dragover"); };
dropzone.ondragleave = () => dropzone.classList.remove("dragover");
dropzone.ondrop = e => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    addFiles(e.dataTransfer.files);
};

function addFiles(fileListInput) {
    for (let f of fileListInput) {
        if (f.name.endsWith(".docx")) files.push(f);
    }
    renderFiles();
}

function renderFiles() {
    fileList.innerHTML = "";
    files.forEach((f, i) => {
        let div = document.createElement("div");
        div.className = "file-item";
        div.innerHTML = `
            <span>${f.name}</span>
            <button onclick="moveUp(${i})">↑</button>
            <button onclick="moveDown(${i})">↓</button>
            <button class="delete" onclick="removeFile(${i})">✖</button>
        `;
        fileList.appendChild(div);
    });
    fileOrder.value = files.map(f => f.name).join(",");
}

function moveUp(i) { if (i>0) [files[i],files[i-1]]=[files[i-1],files[i]]; renderFiles(); }
function moveDown(i) { if (i<files.length-1) [files[i],files[i+1]]=[files[i+1],files[i]]; renderFiles(); }
function removeFile(i) { files.splice(i,1); renderFiles(); }

function resetForm() {
    files = [];
    renderFiles();
    document.getElementById("progressBar").style.width="0%";
}

document.getElementById("mergeForm").onsubmit = function(e) {
    e.preventDefault();
    
    let link = document.getElementById("result_page");
    link.innerHTML = 'Please Wait !!....';
    let formData = new FormData(this);
    files.forEach(f => formData.append("templates", f));

    let xhr = new XMLHttpRequest();
    xhr.open("POST", "/", true);

    xhr.upload.onprogress = e => {
        if (e.lengthComputable) {
            let percent = (e.loaded / e.total) * 100;
            document.getElementById("progressBar").style.width = percent + "%";
        }
    };

    xhr.responseType = "text/html";
    xhr.onload = () => {
       let link = document.getElementById("result_page");
       link.innerHTML = xhr.response;
    };
    xhr.send(formData);
/*
    xhr.responseType = "blob";
    xhr.onload = () => {
        let blob = xhr.response;
        let link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "output.pdf";
        link.click();
    };

    xhr.send(formData);
*/

};
</script>

</body>
</html>
"""

RESULT_PAGE = """
<style>
a {
    display: block;
    margin: 15px 0;
    font-size: 18px;
    color: #2980b9;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
</style>

<div class="container">
    <h2>✅ Document Merge Completed</h2>
    <table border="0" style="width:100%"><tr><td align="left">
    <a href="/download/{{docx}}">📄 Download merged .docx</a>
    </td><td align="right">
    <a href="/download/{{pdf}}">📕 Download merged .pdf</a>
    </td></tr><tr><td colspan="2" align="center">
    <div class="buttons">
      <button type="reset" class="reset" onclick="window.location.href='/'" >New Merge</button>
    </div>
    </td></tr></table>
</div>

"""

RESULT_PAGE1 = """
<!DOCTYPE html>
<html>
<head>
<title>Download Files</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: linear-gradient(120deg,#e0eafc,#cfdef3);
}
.container {
    width: 600px;
    margin: 60px auto;
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0,0,0,.15);
    text-align: center;
}
a {
    display: block;
    margin: 15px 0;
    font-size: 18px;
    color: #2980b9;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
button {
    margin-top: 25px;
    padding: 10px 20px;
    background: #27ae60;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}
</style>
</head>
<body>
<div class="container">
    <h2>✅ Document Merge Completed</h2>

    <a href="/download/{{docx}}">📄 Download DOCX</a>
    <a href="/download/{{pdf}}">📕 Download PDF</a>

    <button onclick="window.location.href='/'">New Merge</button>
</div>
</body>
</html>
"""


def replace_placeholders(doc, data):
    for p in doc.paragraphs:
        for k, v in data.items():
            p.text = p.text.replace(f"{{{{{k}}}}}", str(v))
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for k, v in data.items():
                    c.text = c.text.replace(f"{{{{{k}}}}}", str(v))



@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":

        sid = session['sid'] = str(uuid.uuid4())
        UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER_BASE, sid)
        OUTPUT_FOLDER = os.path.join(OUTPUT_FOLDER_BASE, sid)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        excel = request.files["excel"]
        sheet = request.form["sheet"]
        output_docx = request.form["output_docx"]
        output_pdf = request.form["output_pdf"]
        templates = request.files.getlist("templates")

        excel_path = os.path.join(UPLOAD_FOLDER, excel.filename)
        excel.save(excel_path)

        template_paths=[]
        for t in templates:
            path = os.path.join(UPLOAD_FOLDER, t.filename)
            t.save(path)
            template_paths.append(path)

        # -------------
        """
        df = pd.read_excel(excel_path, sheet_name=sheet)

        base = Document(template_paths[0])
        base.paragraphs[0].clear()
        composer = Composer(base)

        for _, row in df.iterrows():
            data = row.to_dict()
            for t in template_paths:
                d = Document(t)
                replace_placeholders(d, data)
                composer.append(d)
            composer.doc.add_page_break()
        """
        # -------------

        docx_path = os.path.join(OUTPUT_FOLDER, output_docx)
        #composer.save(docx_path)

        pdf_path = os.path.join(OUTPUT_FOLDER, output_pdf)
        #convert(docx_path, pdf_path)

        #excel_path = f"/tmp/{excel.filename}"
        #with open(excel_path, "wb") as f:
        #   shutil.copyfileobj(excel.file, f)

        #docs = templates
        #doc_paths = []
        #for d in docs:
        #    #path = f"/tmp/{d.filename}"
        #    path = os.path.join(UPLOAD_FOLDER, d.filename)
        #    with open(path, "wb") as f:
        #        shutil.copyfileobj(d.file, f)
        #    doc_paths.append(path)

        sheetName = sheet

        #mailmerge_output = "/tmp/mailmerge_result.docx"
        #final_output = "/tmp/final_output.docx"
        #mail_merge_to_pdf(excel_path, sheetName, doc_paths, final_output)

        mail_merge_to_pdf(excel_path, sheetName, template_paths, docx_path, pdf_path)

        print(f" Docx & PDF created {docx_path} and {pdf_path}")
        return render_template_string(RESULT_PAGE, docx=output_docx, pdf=output_pdf)
        #return render_template_string(RESULT_PAGE, docx=docx_path, pdf=pdf_path)
        #return render_template_string(RESULT_PAGE, docx=output_docx, pdf=output_pdf)
        #return send_file(pdf_path, as_attachment=True)

    return render_template_string(HTML_PAGE)



@app.route("/download/<filename>")
def download_file(filename):
    sid = session.get('sid')
    path = os.path.join(OUTPUT_FOLDER_BASE, sid, filename)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    # Quick test configuration. Please use proper Flask configuration options
    # in production settings, and use a separate file or environment variables
    # to manage the secret key!
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    #app.config['SESSION_TYPE'] = 'memcached'
    #session.init_app(app) 
    #session = Session()

    app.run(host="0.0.0.0", port=5000, debug=True)




