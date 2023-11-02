import io, json, base64, pyperclip, tempfile, cv2, os, qrcode, fitz
from gtts import gTTS
import soundfile as sf
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
from pdfminer.high_level import extract_text
from tabulate import tabulate
from PIL import Image
import pyzbar
import zipfile2

class PromptCollectionApp:
    def __init__(self):
        self.data = self.load_data()

    def load_data(self):
        data = pd.read_excel("prompts.xlsx")  # Use a configurable file path
        return data

    def data_dict(self, data):
        category_dict = {}
        for index, row in data.iterrows():
            category = row["category"]
            title = row["title"]
            prompt = row["prompt"]
            if category not in category_dict:
                category_dict[category] = {"titles": [], "prompts": []}
            category_dict[category]["titles"].append(title)
            category_dict[category]["prompts"].append(prompt)
        return category_dict

    def prompt_techniques(self):
        st.subheader("🚀 Prompt Techniques")
        with open("prompt_techniques.md", "r", encoding="utf-8") as f:
            techniques_markdown = f.read()
            # Show the extracted text
            with st.expander("Extracted Text"):
                #st.text(text)
                st.markdown(techniques_markdown)
    
    def add_prompt(self, data, category_dict):
        tab1, tab2 = st.tabs(["Add Prompt", "Prompt Lists"])
        with tab1:
            st.subheader("📝 Add New Prompt")
            new_title = st.text_input("Title:")
            new_prompt = st.text_area("Prompt:")

            # Input for category selection
            new_category = st.selectbox("Category", ["Select existing category"] + list(category_dict.keys()))
            if new_category == "Select existing category":
                # If the user wants to create a new category, provide an input field for it
                new_category = st.text_input("New Category:")

            if st.button("➕ Add"):
                if new_title and new_prompt and new_category:
                    if new_category not in category_dict:
                        # If the category is new, add it to the dictionary
                        category_dict[new_category] = {"titles": [new_title], "prompts": [new_prompt]}
                    else:
                        # If the category exists, append the title and prompt
                        category_dict[new_category]["titles"].append(new_title)
                        category_dict[new_category]["prompts"].append(new_prompt)

                    new_row = {'category': new_category, 'title': new_title, 'prompt': new_prompt}
                    new_data = pd.concat([data, pd.DataFrame(new_row, index=[0])], ignore_index=True)
                    new_data.to_excel("prompts.xlsx", index=False)
                    st.success("Prompt added successfully!")


        with tab2:
            st.subheader("🚀 Prompt Lists (A-Z)")
            st.dataframe(data)

    def choose_prompt(self, category_dict):
        st.subheader("✅ Choose Prompt")
        selected_category = st.selectbox("Select Category", list(category_dict.keys()))
        selected_title = st.selectbox("Select Title", category_dict[selected_category]["titles"])

        if selected_title:
            selected_prompt = category_dict[selected_category]["prompts"][
                category_dict[selected_category]["titles"].index(selected_title)
            ]
            #st.write(f"**Selected Title:** {selected_title}")
            st.error(selected_prompt)

            if st.button("📋 Copy Prompt"):
                pyperclip.copy(selected_prompt)
                st.info("Prompt copied to clipboard.")

    def edit_prompt(self, data, category_dict):
        st.subheader("✏️ Edit Prompt")
        selected_category = st.selectbox("Select Category", list(category_dict.keys()))
        selected_title = st.selectbox("Select Title", category_dict[selected_category]["titles"])

        if selected_title:
            selected_prompt = category_dict[selected_category]["prompts"][
                category_dict[selected_category]["titles"].index(selected_title)
            ]

            new_prompt = st.text_area("Edit Old Prompt:", selected_prompt)

            if st.button("✅ Save Changes"):
                category_dict[selected_category]["prompts"][
                    category_dict[selected_category]["titles"].index(selected_title)
                ] = new_prompt
                data.loc[(data["category"] == selected_category) & (data["title"] == selected_title), "prompt"] = new_prompt
                data.to_excel("prompts.xlsx", index=False)
                st.success("Prompt updated successfully!")

    def pdf_processor(self):
        st.info("Upload a PDF file and view, extract text file, save the pages as image.")
        

        # Create Tabs
        pdfViewer, pdfTextExtractor, pdfImgExtractor, pdfZipDownload = st.tabs(["PDF Viewer", "PDF Text Extractor", "PDF Image Extractor", "PDF To Image Zip"])
       
        
        with pdfViewer:
            # Upload PDF file
            pdf_file1 = st.file_uploader("Upload a PDF file", type=["pdf"], key="pdffilek1")
            if pdf_file1:
                with fitz.open(stream=pdf_file1.read(), filetype="pdf") as pdf_document:
                    num_pages = len(pdf_document)
                    if num_pages == 1:
                        # Get the Pixmap for the single page
                        pixmap = pdf_document.load_page(0).get_pixmap()

                        # Convert the Pixmap to a PIL image
                        pil_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

                        # Display the PIL image in Streamlit
                        st.image(pil_image, use_column_width=True)
                    else:

                        # Select a page using a slider
                        page_number = st.slider("Navigate Page", min_value=1, max_value=num_pages, value=38)

                        # Get the Pixmap for the selected page
                        pixmap = pdf_document.load_page(page_number - 1).get_pixmap()

                        # Convert the Pixmap to a PIL image
                        pil_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

                        # Display the PIL image in Streamlit
                        st.image(pil_image, use_column_width=True)

                        # Add navigation for multiple pages
                        st.markdown(f"Page {page_number} of {num_pages}")

        with pdfTextExtractor:
            # Upload PDF file
            pdf_file2 = st.file_uploader("Upload a PDF file", type=["pdf"], key="pdffilek2")
            if pdf_file2:
                # Extract text from the uploaded PDF file
                text = extract_text(pdf_file2)
                # Show the extracted text
                with st.expander("Extracted Text"):
                    st.text(text)
                    
                st.markdown(f"**Download Text File**")
                st.download_button(
                        label="⬇️ Download Text",
                        data=text,
                        key="extracted_text.txt",
                        file_name="extracted_text.txt",
                    )

        with pdfImgExtractor:
            # Upload PDF file
            pdf_file3 = st.file_uploader("Upload a PDF file", type=["pdf"], key="pdffilek3")
            if pdf_file3:
                with fitz.open(stream=pdf_file3.read(), filetype="pdf") as pdf_document:
                    num_pages = len(pdf_document)
                    for i in range(num_pages):
                        # Get the Pixmap for the selected page
                        pixmap = pdf_document.load_page(i).get_pixmap()

                        # Convert the Pixmap to a PIL image
                        pil_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

                        # Display the PIL image in Streamlit
                        st.image(pil_image, use_column_width=True, caption=f"Page {i+1} of {num_pages}")
        
        with pdfZipDownload:
            # Upload PDF file
            pdf_file4 = st.file_uploader("Upload a PDF file", type=["pdf"], key="pdffilek4")
            if pdf_file4:
                with fitz.open(stream=pdf_file4.read(), filetype="pdf") as pdf_document:
                    num_pages = len(pdf_document)
                    # Create a zip file to store page images
                    zip_buffer = io.BytesIO()
                    with zipfile2.ZipFile(zip_buffer, "w") as zipf:
                        for i in range(num_pages):
                            # Get the Pixmap for the selected page
                            pixmap = pdf_document.load_page(i).get_pixmap()

                            # Convert the Pixmap to a PIL image
                            pil_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

                            # Add the page image to the zip file
                            img_bytes = io.BytesIO()
                            pil_image.save(img_bytes, format="JPEG")
                            img_bytes.seek(0)
                            zipf.writestr(f"{i+1}_page.jpg", img_bytes.read())

                    # Add a download button to download the zip file
                    st.markdown("## Download Page Images as a Zip File")
                    st.download_button(
                        label="Download Zip 🗃️",
                        data=zip_buffer.getvalue(),
                        key="zip",
                        file_name="pages.zip",
                        mime="application/zip",
                    )


    def json2csv(self):
        st.subheader("JSON to CSV Conversion")
        st.info("Upload a JSON file to convert it to CSV file.")

        # Upload JSON file
        json_file = st.file_uploader("Upload JSON File", type=["json"])

        if json_file is not None:
            # Read JSON data from the uploaded file
            json_data = json.load(json_file)

            # Convert JSON to DataFrame
            df = pd.DataFrame(json_data)

            # Save DataFrame to CSV
            df.to_csv("data.csv", index=False)

            # Read the CSV data
            csv_data = pd.read_csv("data.csv")

            #
            st.dataframe(csv_data.head())

            # Provide a button to download the generated CSV file
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data.to_csv(index=False).encode(),
                file_name="data.csv",
                key="download-csv",
            )

    def md_table2csv(self):
        st.subheader("MarkdownTable-CSV Conversion")
        st.info("Upload a Markdown file containing a table and click the 'Convert to CSV' button to generate a CSV file.")

        # File uploader for Markdown file
        markdown_file = st.file_uploader("Upload a Markdown file", type=["md", "markdown"])

        # Button to convert to CSV
        if st.button("🔁 Convert to CSV"):
            if markdown_file is not None:
                # Read the uploaded Markdown file
                markdown_text = markdown_file.read().decode("utf-8")

                # Function to convert markdown table to CSV
                def markdown_to_csv(markdown_text):
                    try:
                        # Split markdown text into rows
                        rows = markdown_text.split("\n")
                        headers = None
                        data = []

                        for row in rows:
                            if row:
                                row_data = row.split("|")
                                row_data = [item.strip() for item in row_data]
                                if headers is None:
                                    headers = row_data
                                else:
                                    data.append(row_data)

                        if headers is not None:
                            df = pd.DataFrame(data, columns=headers)
                            csv_buffer = io.StringIO()
                            df.to_csv(csv_buffer, index=False)
                            csv_data = csv_buffer.getvalue()
                            return csv_data
                        else:
                            return "No table found in the Markdown file."

                    except Exception as e:
                        return str(e)

                # Call the function to convert markdown to CSV
                converted_csv = markdown_to_csv(markdown_text)

                if not isinstance(converted_csv, str):
                    st.error("Error converting the markdown table to CSV. Please check your input.")
                else:
                    # Download CSV button
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=converted_csv,
                        key="markdown_to_csv.csv",
                        file_name="markdown_to_csv.csv",
                    )
            else:
                st.warning("Please upload a Markdown file first.")

    def search_prompts(self, data):
        st.subheader("Search for prompts")
        # Create a text input for searching
        search_query = st.text_input("Search for prompts")

        # Filter the data based on the search query
        filtered_data = data[data.apply(lambda row: any(search_query.lower() in str(row[col]).lower() for col in data.columns), axis=1)]

        if not search_query:
            st.write("Enter a search keyword to find prompts.")
        else:
            # Display the filtered prompts
            if not filtered_data.empty:
                st.write(f"**Results for '{search_query}':**")
                st.dataframe(filtered_data)
            else:
                st.warning(f"No prompts found for '{search_query}'")

    def prompt_cards(self, data):
        if data is not None:
            # Group the DataFrame by 'category'
            grouped = data.groupby('category')

            # Split the data into chunks of 3 rows each
            chunk_size = 2
            data_chunks = [group_data[i:i + chunk_size] for _, group_data in grouped for i in range(0, len(group_data), chunk_size)]

            # Iterate over each category chunk
            for data_chunk in data_chunks:
                # Create columns
                cols = st.columns(len(data_chunk))

                # Iterate over each entry in the chunk
                for col, (_, row) in zip(cols, data_chunk.iterrows()):
                    with col:
                        st.info(row['title'])
                        st.success(row['prompt'])

                        copy_button = st.button("📃 Copy", key=f"copy_{row['category']}_{row['title']}")
                        if copy_button:
                            pyperclip.copy(row['prompt'])
                            st.success("Prompt copied to clipboard.")

    def text2speech(self):

        def text_to_audio(text, output_format):
            tts = gTTS(text)
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{output_format}') as temp_file:
                tts.save(temp_file.name)
            return temp_file.name

        st.subheader("Text-to-Speech Converter")
        
        textfile, textbox = st.tabs(["Text File", "Text Box"])

        with textbox:
            st.subheader("Text Box")
            text_input = st.text_area("Enter the text you want to convert to speech")

            output_format = st.radio("Select the output format", ["WAV", "MP3"], key="text_box")

            if st.button("🔁 Convert To 🎵", key="convert_text_box"):
                if text_input:
                    audio_file = text_to_audio(text_input, output_format)
                    with open(audio_file, "rb") as audio:
                        audio_bytes = audio.read()
                    b64 = base64.b64encode(audio_bytes).decode()
                    st.markdown(f'<a href="data:audio/{output_format.lower()};base64,{b64}" download="output.{output_format.lower()}">⬇️ Download {output_format}</a>', unsafe_allow_html=True)
                    os.remove(audio_file)
                else:
                    st.warning("Please enter some text to convert.")


        with textfile:
            st.subheader("Text File")
            uploaded_file = st.file_uploader("Upload a text file", type=["txt"])

            output_format = st.radio("Select audio format:", ["WAV", "MP3"], key="text_file", horizontal= True)

            if st.button("🔁 Convert To 🎵", key="convert_text_file"):
                if uploaded_file:
                    text_input = uploaded_file.read().decode()
                    audio_file = text_to_audio(text_input, output_format)
                    with open(audio_file, "rb") as audio:
                        audio_bytes = audio.read()
                    b64 = base64.b64encode(audio_bytes).decode()
                    st.markdown(f'<a href="data:audio/{output_format.lower()};base64,{b64}" download="output.{output_format.lower()}">⬇️ Download {output_format}</a>', unsafe_allow_html=True)
                    os.remove(audio_file)
                else:
                    st.warning("Please upload a text file to convert.")
        
    def image_processing(self):
        def brighten_image(image, amount):
            img_bright = cv2.convertScaleAbs(image, beta=amount)
            return img_bright

        def blur_image(image, amount):
            blur_img = cv2.GaussianBlur(image, (11, 11), amount)
            return blur_img

        def enhance_details(img):
            hdr = cv2.detailEnhance(img, sigma_s=12, sigma_r=0.15)
            return hdr
        
        st.subheader("OpenCV Image Processing")
        st.info("This app allows you to play with Image filters!")

        blur_rate = st.slider("Blurring", min_value=0.5, max_value=3.5)
        brightness_amount = st.slider("Brightness", min_value=-50, max_value=50, value=0)
        apply_enhancement_filter = st.checkbox('Enhance Details')

        image_file = st.file_uploader("⬆️ Upload Your Image", type=['jpg', 'png', 'jpeg'])
        if not image_file:
            return None

        original_image = Image.open(image_file)
        original_image = np.array(original_image)

        processed_image = blur_image(original_image, blur_rate)
        processed_image = brighten_image(processed_image, brightness_amount)

        if apply_enhancement_filter:
            processed_image = enhance_details(processed_image)

        st.info("Original Image vs Processed Image")
        st.image([original_image, processed_image])

    def qr_processor(self):
        # Streamlit app title and description
        st.subheader("QR Code Encoder & Decoder")
        st.info("Encode text to QR code or decode QR codes from images.")

        tabEncodeQr, tabDecodeQr = st.tabs(["Encode QR Code", "Decode QR Code"])
        with tabEncodeQr:
            # Encode text to QR code
            text = st.text_input("Enter the text to encode as a QR code:")
            if st.button("Generate QR Code"):
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=50,
                    border=2,
                )
                qr.add_data(text)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")

                # Convert the PIL image to Bytes format
                image_bytes = io.BytesIO()
                qr_img.save(image_bytes, format="PNG")
                st.image(image_bytes, caption="QR Code", use_column_width=True)

        with tabDecodeQr:
            # Decode QR code from an image
            uploaded_image = st.file_uploader("Upload an image containing a QR code", type=["jpg", "png", "jpeg"])
            if uploaded_image:
                image = cv2.imdecode(np.frombuffer(uploaded_image.read(), np.uint8), cv2.IMREAD_COLOR)
                decoded_objects = pyzbar.decode(image)

                if decoded_objects:
                    for obj in decoded_objects:
                        st.subheader("QR Code Data")
                        st.write(obj.data.decode("utf-8"))
                else:
                    st.error("No QR code found in the uploaded image.")


def main():
    #st.title("Productivity Tools")
    menu = ["Prompt Techniques", "Add Prompt", "Search Prompts", "Prompt Cards", "Choose Prompt", "Edit Prompt", "Image Processing(OpenCV)", "Text-Speech Conversion", "JSON-CSV Converter", "MD Table-CSV Conversion", "QR Encoder-Decoder","PDF Processor"]
    icons = ['house', 'plus-square',"search", "card-heading","check2-square", "pencil-square","cpu", "music-note-list", "filetype-csv","filetype-csv" , "qr-code", "filetype-pdf"]
    with st.sidebar:
        selected = option_menu("Productivity Tools", menu, icons=icons, menu_icon="list", default_index=11, orientation="vertical")

    app = PromptCollectionApp()
    data = app.load_data()
    category_dict = app.data_dict(data)

    if selected == "Prompt Techniques":
        app.prompt_techniques()

    elif selected == "Add Prompt":
        app.add_prompt(data, category_dict)
    
    elif selected == "Search Prompts":
        app.search_prompts(data)
    
    elif selected == "Choose Prompt":
        app.choose_prompt(category_dict)

    elif selected == "Edit Prompt":
        app.edit_prompt(data, category_dict)

    elif selected == "Text-Speech Conversion":
        app.text2speech()
    
    elif selected == "JSON-CSV Converter":
        app.json2csv()

    elif selected == "MD Table-CSV Conversion":
        app.md_table2csv()

    elif selected == "Prompt Cards":
        app.prompt_cards(data)
    
    elif selected == "Prompt Cards":
        app.text2speech()

    elif selected == "Image Processing(OpenCV)":
        app.image_processing()
    
    elif selected == "QR Encoder-Decoder":
        app.qr_processor()
    
    elif selected == "PDF Processor":
        app.pdf_processor()

    st.error("📜 Copyright © 2023 https://www.youtube.com/@LearnWithNewton. All rights reserved.")

        
if __name__ == "__main__":
    main()
