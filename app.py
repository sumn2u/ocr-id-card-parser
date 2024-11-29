import gradio as gr
import cv2
import face_recognition
import numpy as np
import pytesseract

def extract_text_from_image(image):
    """Extract text using Tesseract OCR."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray)


def parse_id_card_details(text):
    """
    Parse name, DOB, License Number from OCR text.
    """

    # Clean up the text by removing excessive newlines and spaces
    cleaned_text = text.strip()


    lines = cleaned_text.split("\n")
    details = {"Name": None, "DOB": None, "License Number": None, "ID Number": None}


    for i, line in enumerate(lines):
        # Skip the header line with 'LICENSE#', 'BIRTHDATE', etc.
        if "LICENSE#" in line:
            # The actual data line comes right after the header
            next_line = lines[i + 1]  # The line after header contains the data
            parts = next_line.split()
            details["License Number"] = parts[0]  # License number is the first part (C-13)
            details["DOB"] = parts[1]  # Birthdate is the second part (12-13-1989)
         # Extract Driver's License Name (It follows 'DRIVER'S LICENSE |')
        elif "DRIVER'S LICENSE |" in line:
            # The name should be on the next line after 'DRIVER'S LICENSE |'
            name_line_index = i + 2
            parts = lines[name_line_index]
            details["Name"] = parts
    # Return the parsed details
    return details



def process_video(video_path):
    """Extract the first clear face from the uploaded video."""
    cap = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(frame_rgb)
        if face_locations:
            cap.release()
            return frame  # Return the first frame with a detected face
    cap.release()
    return None  # No face detected in the video


def extract_id_face_and_match(id_card_image, video_path):
    try:
        # Extract and parse text from the ID card
        id_text = extract_text_from_image(id_card_image)
        details = parse_id_card_details(id_text)

        # Extract face from ID card image
        id_image_rgb = cv2.cvtColor(id_card_image, cv2.COLOR_BGR2RGB)
        id_face_locations = face_recognition.face_locations(id_image_rgb)
        if len(id_face_locations) == 0:
            return "No face detected in ID card image", None, None, None
        id_face_encoding = face_recognition.face_encodings(id_image_rgb, known_face_locations=id_face_locations)[0]

        # Process the uploaded video to extract a face
        video_frame = process_video(video_path)
        if video_frame is None:
            return "No face detected in the uploaded video", None, None, None
        
        video_image_rgb = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)
        video_face_locations = face_recognition.face_locations(video_image_rgb)
        video_face_encoding = face_recognition.face_encodings(video_image_rgb, known_face_locations=video_face_locations)[0]

        # Compare faces
        match = face_recognition.compare_faces([id_face_encoding], video_face_encoding)
        if match[0]:
            return (
                "Face Matched",
                id_card_image,
                video_frame,
                {"Name": details["Name"], "DOB": details["DOB"], "License Number": details["License Number"]},
            )
        else:
            return "Face did not match", None, None, None

    except Exception as e:
        return str(e), None, None, None


iface = gr.Interface(
    fn=extract_id_face_and_match,
    inputs=[
        gr.Image(type="numpy", label="Upload ID Card Image"),
        gr.Video(label="Upload Video")
    ],
    outputs=[
        gr.Textbox(label="Result"),
        gr.Image(label="ID Card Face"),
        gr.Image(label="Video Frame Face"),
        gr.JSON(label="Extracted User Details"),
    ],
    title="ID Card Face Matching with Video Input",
    description="Upload an ID card image and a video. The application will extract details from the ID card, process the video to extract a face, and match the faces.",
)

iface.launch()
