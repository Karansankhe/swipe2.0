from dotenv import load_dotenv
import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
import fitz  # PyMuPDF for PDF handling
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load environment variables from .env file
load_dotenv()

# Configure Google API with the provided API key
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Function to load Google Gemini model and get responses
def get_gemini_response(content, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model
    response = model.generate_content([content, prompt])
    return response.text

def input_image_setup(uploaded_file):
    # Check if a file has been uploaded
    if uploaded_file is not None:
        # Open the image using PIL
        image = Image.open(uploaded_file)
        return image
    else:
        raise FileNotFoundError("No file uploaded")

def extract_text_from_pdf(uploaded_file):
    # Extract text from a PDF file
    if uploaded_file is not None:
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    else:
        raise FileNotFoundError("No file uploaded")

def create_pdf_from_text(text_list):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    for i, text in enumerate(text_list):
        c.drawString(72, height - 72, f"Document {i + 1}")
        text_lines = text.split('\n')
        y_position = height - 100
        for line in text_lines:
            if y_position < 72:
                c.showPage()
                y_position = height - 72
            c.drawString(72, y_position, line)
            y_position -= 12
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# Fixed prompt for content extraction
input_prompt_text = """
        You are tasked with processing the text extracted from a document (PDF or image). 
        Your goal is to analyze the content and extract only the following information:
        - Customer details (such as name, address, contact information)
        - Product details (such as product names, quantities, descriptions, and prices)
        - Total Amount (the final amount billed, including any taxes or discounts)
        Return only the extracted details, omitting all other content.
        """

## Initialize Streamlit app
st.set_page_config(page_title="Document Analysis with Gemini", layout="wide")
st.title("Document Information Extractor")
st.markdown("""
    Welcome to the Document Information Extractor! Upload your PDFs or images, and get the essential details extracted and compiled into a downloadable PDF.
    
    **Instructions:**
    - **PDF Upload:** Select one or more PDF files. You can analyze them all together.
    - **Image Upload:** Select an image file for analysis.
""")

# PDF upload section
st.header("📄 PDF Upload")
pdf_files = st.file_uploader("Choose PDF files...", type=["pdf"], accept_multiple_files=True, key="pdf_uploader")

if pdf_files:
    st.write("Processing PDFs... Please wait.")
    combined_text = []
    for i, pdf_file in enumerate(pdf_files):
        pdf_text = extract_text_from_pdf(pdf_file)
        # Process each PDF and extract required information
        extracted_info = get_gemini_response(pdf_text, input_prompt_text)
        combined_text.append(f"Document {i + 1}:\n{extracted_info}")

    if st.button("Analyze PDFs"):
        st.subheader("📋 PDF Analysis Result")
        combined_text_str = "\n\n".join(combined_text)
        st.write(combined_text_str)

        # Create and download PDF with results
        result_pdf_buffer = create_pdf_from_text(combined_text)
        st.download_button(
            label="Download Analysis PDF",
            data=result_pdf_buffer,
            file_name="analysis_results.pdf",
            mime="application/pdf"
        )

# Image upload section
st.header("🖼️ Image Upload")
image_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], key="image_uploader")
if image_file is not None:
    image = input_image_setup(image_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)
    if st.button("Analyze Image"):
        st.write("Analyzing image... Please wait.")
        response = get_gemini_response(image, input_prompt_text)
        st.subheader("📋 Image Analysis Result")
        st.write(response)

        # Create and download PDF with results
        result_pdf_buffer = create_pdf_from_text([response])
        st.download_button(
            label="Download Analysis PDF",
            data=result_pdf_buffer,
            file_name="analysis_results.pdf",
            mime="application/pdf"
        )
