import cv2
import face_recognition
import numpy as np
import os

from django.views import View
from django.shortcuts import render, redirect
from .models import Person


class HomeView(View):
    def get(self, request):
        return render(request, "home.html")


class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        name = request.POST.get("name")
        image = request.FILES.get("image")

        if name and image:
            Person.objects.create(name=name, image=image)

        return redirect("home")


class RecognizeView(View):
    def get(self, request):
        known_encodings = []
        known_names = []

        # 🔹 Load stored images
        for person in Person.objects.all():
            image_path = person.image.path

            if not os.path.exists(image_path):
                continue

            # Load image (RGB, uint8)
            image = face_recognition.load_image_file(image_path)
            image = np.ascontiguousarray(image)

            # Detect faces
            locations = face_recognition.face_locations(image)

            if not locations:
                continue

            encodings = face_recognition.face_encodings(image, locations)

            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(person.name)

        # 🔹 Open webcam
        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR → RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame = np.ascontiguousarray(rgb_frame)

            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations
            )

            for encoding, (top, right, bottom, left) in zip(
                face_encodings, face_locations
            ):
                matches = face_recognition.compare_faces(
                    known_encodings, encoding, tolerance=0.5
                )
                name = "Unknown"

                if True in matches:
                    name = known_names[matches.index(True)]

                # Draw box
                cv2.rectangle(
                    frame, (left, top), (right, bottom), (0, 255, 0), 2
                )
                cv2.putText(
                    frame,
                    name,
                    (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow("Face Recognition", frame)

            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

        cap.release()
        cv2.destroyAllWindows()

        return render(request, "recognize.html")
