


#------------------------------------------------------------- SuN -- 2025-Dec-13 ---- {
'''
   Program for Merging Tender Documents from Excel Data Sheet Named "MergerSheet" and Generating a PDF File output 
   The set of normal Word Files have column names defined within double braces {{ }}
   Eg:-  {{tenderName}} {{tenderDate}} 
'''
#------------------------------------------------------------- SuN -- 2025-Dec-13 ---- {

# python merge2pdf.py --sheet MergerSheet  --output "../TempFinalMerged.pdf" "../TenderMergeFile.xlsx" "../Tender document Blade Servers CoverPages.docx"  "../Tender document Blade Servers NIT.docx" "../Tender document Blade Servers PriceBid.docx" "../Tender document Blade Servers TechnicalBid.docx" "../General Conditions of Contract-New.docx"

#python merge2pdf.py --sheet "Employee List" --output "Final_Report.pdf" data.xlsx cover.docx body.docx 

# =========================

import sys
import warnings

# --- 1. Suppress pkg_resources Deprecation Warning ---
# We must do this BEFORE importing libraries that use pkg_resources
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, module='pkg_resources')
    # Some environments trigger it via importlib, so we suppress based on message too
    warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")
    
    # Now import the heavy libraries
    import pandas as pd
    import argparse
    import subprocess
    import os
    import io
    from docxtpl import DocxTemplate
    from docxcompose.composer import Composer
    from docx import Document
    from docx2pdf import convert
    
    from config import config
    from subprocess import TimeoutExpired
    from common.docx2pdf import LibreOfficeError, convert_to
    
    from common.errors import RestAPIError, InternalServerErrorError
    from common.files import uploads_url, save_to

def convertLinux(infile, outfile_path, outfile):
    try:
        result = convert_to(outfile_path, infile, timeout=15)
        # Rename the file
        try:
            pdfname, ext = os.path.splitext(infile)
            pdfname += ".pdf"
            os.rename(pdfname, outfile)
            print(f"File '{pdfname}' renamed to '{outfile}' successfully.")
        except FileNotFoundError:
            print(f"Error: The file '{pdfname}' was not found.")
        except PermissionError:
            print("Error: Permission denied. Unable to rename the file.")
        except OSError as e:
            print(f"An unexpected error occurred: {e}")
    
    except LibreOfficeError:
        raise InternalServerErrorError({'message': 'Error when converting file to PDF'})
    except TimeoutExpired:
        raise InternalServerErrorError({'message': 'Timeout when converting file to PDF'})
        

def mail_merge_to_pdf(excel_path, sheet_name, template_paths, output_docx_path, output_pdf_path):
    # --- 2. Validation ---
    if not os.path.exists(excel_path):
        print(f"Error: Excel file '{excel_path}' not found.")
        return
    
    valid_templates = []
    for t in template_paths:
        if os.path.exists(t):
            valid_templates.append(t)
        else:
            print(f"Warning: Template '{t}' not found. Skipping.")

    if not valid_templates:
        print("Error: No valid template files found.")
        return

    # --- 3. Load Excel Data ---
    print(f"--- Loading data from sheet '{sheet_name}' ---")
    try:
        # dtype=str ensures phone numbers/zips don't lose leading zeros
        df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str).fillna('')
        records = df.to_dict(orient='records')
    except ValueError as ve:
        print(f"Error: Could not find sheet '{sheet_name}'. Check your spelling.")
        return
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    if not records:
        print("No data found in the specified Excel sheet.")
        return

    print(f"Found {len(records)} records. Merging into intermediate Word doc...")

    # --- 4. Merge Logic (In-Memory) ---
    composer = None

    for i, record in enumerate(records):
        print(f"Processing Record {i+1}/{len(records)}...")

        for t_path in valid_templates:
            try:
                tpl = DocxTemplate(t_path)
                tpl.render(record)
                
                # Save rendered doc to memory stream
                temp_stream = io.BytesIO()
                tpl.save(temp_stream)
                temp_stream.seek(0)
                
                if composer is None:
                    # Initialize the master composer with the first doc
                    master_doc = Document(temp_stream)
                    composer = Composer(master_doc)
                else:
                    doc_to_append = Document(temp_stream)
                    # Add a page break so the next doc starts on a new page
                    composer.doc.add_page_break()
                    composer.append(doc_to_append)
            except Exception as e:
                print(f"Error merging template '{t_path}' for record {i+1}: {e}")

    # --- 5. Save Temp DOCX & Convert to PDF ---
    if composer is None:
        print("Error: No documents were merged. Exiting.")
        return

    # We must save a physical .docx file first for the converter to work
    #temp_docx = "temp_intermediate_merge.docx"
    temp_docx = output_docx_path
    
    try:
        print(f"Saving Word file..{output_docx_path}.")
        composer.save(temp_docx)
        
        print(f"Converting to PDF: {output_pdf_path} ...")
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # for Windows use convert  & for Linux LibreOffice use convert_to
        if sys.platform == "win32":
            print("Running on Windows")
            # Windows-specific code here
            convert(temp_docx, output_pdf_path)
        elif sys.platform.startswith("linux"):
            print("Running on Linux") 
            convertLinux(temp_docx, output_dir, output_pdf_path)
            # Linux-specific code here
        elif sys.platform == "darwin":
            print("Running on macOS")
            convertLinux(temp_docx, output_dir, output_pdf_path)
            # macOS-specific code here
        else:
            print(f"Unknown platform: {sys.platform}")
        
        print(f"\nSuccess! PDF saved to: {output_pdf_path}")
        
    except Exception as e:
        print(f"\nCRITICAL ERROR during PDF conversion: {e}")
        print("Make sure Microsoft Word is installed and not currently frozen.")
    
    finally:
        print(f"\n Saved output files to: {output_pdf_path}")
        # Cleanup: Remove the temporary .docx file
        #if os.path.exists(temp_docx):
        #    try:
        #        os.remove(temp_docx)
        #        print("Temporary intermediate file removed.")
        #    except PermissionError:
        #        print("Warning: Could not delete temp file (it might still be open).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mail Merge multiple templates into a single PDF.")
    
    # Positional args
    parser.add_argument("excel_file", help="Path to .xlsx file")
    parser.add_argument("templates", nargs='+', help="Paths to .docx template files")
    
    # Optional flags
    parser.add_argument("--sheet", default="Sheet1", help="Excel sheet name (default: Sheet1)")
    parser.add_argument("--output", default="final_output.pdf", help="Output PDF filename")

    args = parser.parse_args()

    # Ensure output filename ends with .pdf
    output_filename = args.output
    if not output_filename.lower().endswith('.pdf'):
        output_filename += ".pdf"

    output_docxfilename, extension = os.path.splitext(args.output)
    if not output_docxfilename.lower().endswith('.docx'):
        output_docxfilename = output_docxfilename.basename + ".docx"

    mail_merge_to_pdf(args.excel_file, args.sheet, args.templates, output_docxfilename, output_filename)



