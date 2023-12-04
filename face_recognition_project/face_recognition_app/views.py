from django.shortcuts import render
import cv2
import face_recognition
from django.shortcuts import render
from django.http import HttpResponse
from .forms import *
from .models import Student
from django.http import JsonResponse,FileResponse
from .db_utils import get_database_connection
from django.views.decorators.csrf import csrf_exempt
from datetime import date
import calendar 
from django.db import connections
import pandas as pd
import os
from openpyxl import Workbook, load_workbook
from django.conf import settings

def index(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            rno = form.cleaned_data['rno']
            stream = form.cleaned_data['stream']
            std = form.cleaned_data['std']

            cap = cv2.VideoCapture(0)

            while True:
                ret, frame = cap.read()
                face_locations = face_recognition.face_locations(frame)
                face_encodings = face_recognition.face_encodings(frame, face_locations)

                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                cv2.imshow('Capture Face', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                if face_encodings:
                    encoding = repr(face_encodings[0].tolist())
                connection = None  # Initialize the variable outside the try block
                cursor = None  # Initialize the cursor variable

                try:
                    connection = get_database_connection()

                    if connection:
                        cursor = connection.cursor()
                        cursor.execute("INSERT INTO face_recognition_app_student (name, encoding, rno, stream, std) VALUES (%s, %s, %s, %s, %s)",
                                   (name, encoding, rno, stream, std))
                        connection.commit()

                        return JsonResponse({'message': 'Face added successfully'})
                    else:
                        raise Exception('Database connection is None')
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)
                finally:
                    
                    if cursor:
                        cursor.close()
                    if connection and connection.is_connected():
                        connection.close()
                cv2.destroyAllWindows()
                cap.release()
                return render(request, 'success.html', {'name': name})


    else:
        form = StudentForm()

    return render(request, 'index.html', {'form': form})

def check_face_detection(request):
    # Example: Check if face is detected and return a JsonResponse
    face_detected = True  # Replace with your actual face detection logic

    return JsonResponse({'face_detected': face_detected})


def get_student_status_for_day(student, day):
    # Your logic to retrieve the status for the given day
    # For demonstration purposes, I'm returning a placeholder value "A" (Absent)
    return "A"

def generate_excel(request):
    if request.method == 'POST':
        form = ExcelGenerationForm(request.POST)
        if form.is_valid():
            stream = form.cleaned_data['stream']
            std = form.cleaned_data['std']

            # Filter records based on selected options
            students = Student.objects.filter(stream=stream, std=std)

            # Convert the queryset to a list
            students_list = list(students)

            # Create a DataFrame
            data = {
                'Name': [student.name for student in students_list],
                'Roll Number': [student.rno for student in students_list],
                'Stream': [student.stream for student in students_list],
                'Standard': [student.std for student in students_list],
            }

            # Add columns for each day of the month
            for month in range(1, 13):
                _, last_day = calendar.monthrange(2023, month)  # Replace 2023 with the desired year
                days_in_month = list(range(1, last_day + 1))

                for day in days_in_month:
                    day_column = f'Day_{day}'
                    data[day_column] = [''] * len(students_list)

                    for student in students_list:
                        # Using the placeholder function to get student status for a specific day
                        student_status = get_student_status_for_day(student, day)
                        data[day_column][students_list.index(student)] = student_status

            df = pd.DataFrame(data)

            # Generate Excel file
            excel_folder = os.path.join(settings.MEDIA_ROOT, 'excel_files')
            os.makedirs(excel_folder, exist_ok=True)

            excel_file_path = os.path.join(excel_folder, f'attendance_{stream}_{std}.xlsx')
            df.to_excel(excel_file_path, index=False)

            # Provide a download link to the generated Excel file
            response = FileResponse(open(excel_file_path, 'rb'))
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response['Content-Disposition'] = f'attachment; filename=attendance_{stream}_{std}.xlsx'

            return response
    else:
        form = ExcelGenerationForm()

    return render(request, 'generate_excel.html', {'form': form})




    
# Function to update Excel file
def update_excel(student, excel_file_path):
    df = pd.read_excel(excel_file_path)

    # Get the current day
    current_day = date.today().day

    # Check if the column for the current day exists
    day_column = f'Day_{current_day}'
    if day_column not in df.columns:
        # If the column doesn't exist, add it and initialize with 'A' (Absent)
        df[day_column] = 'A'

    # Update status from 'A' to 'P' for the current day in the DataFrame
    df.loc[df['Name'] == student.name, day_column] = 'P'

    df.to_excel(excel_file_path, index=False)

def load_known_faces():
    global known_names, known_encodings, known_rno, known_stream, known_std

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT name, encoding, rno, stream, std FROM face_recognition_app_student")
    result = cursor.fetchall()

    known_names = []
    known_encodings = []
    known_rno = []
    known_stream = []
    known_std = []

    for row in result:
        known_names.append(row[0])
        known_encodings.append(eval(row[1]))
        known_rno.append(row[2])
        known_stream.append(row[3])
        known_std.append(row[4])

    cursor.close()
    connection.close()


# Updated face_match function
def face_match(request):
    global known_names, known_encodings

    # Load known faces and names
    load_known_faces()

    # Initialize video capture
    cap = cv2.VideoCapture(0)

    while True:
        # Capture frame from the video feed
        ret, frame = cap.read()

        # Find face locations and encodings in the frame
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for encoding in face_encodings:
            # Compare the current face encoding with known encodings
            matches = face_recognition.compare_faces(known_encodings, encoding)

            if True in matches:
                first_match_index = matches.index(True)
                student_name = known_names[first_match_index]

                # Retrieve the student object from the database
                try:
                    student = Student.objects.get(name=student_name)
                except Student.DoesNotExist:
                    return JsonResponse({'error': 'Student not found in the database'}, status=404)

                # Path to the Excel file
                excel_folder = os.path.join(settings.MEDIA_ROOT, 'excel_files')
                excel_file_path = os.path.join(excel_folder, f'attendance_{student.stream}_{student.std}.xlsx')

                # Check if the Excel file exists
                if os.path.exists(excel_file_path):
                    # Update the Excel file
                    update_excel(student, excel_file_path)
                    return JsonResponse({'message': f'Attendance updated for {student_name}'})
                else:
                    return JsonResponse({'error': 'Excel file not found'}, status=404)

        # Display recognized faces and names on the video feed
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            font = cv2.FONT_HERSHEY_DUPLEX
            text = f"{student_name}"
            cv2.putText(frame, text, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

        # Show the video feed
        cv2.imshow('Video', frame)

        # Break the loop if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release video capture and close all windows
    cap.release()
    cv2.destroyAllWindows()