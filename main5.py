import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
import pandas as pd
import hashlib
from doctors_data import doctors  # Import doctors from the external Python file
from datetime import datetime
from datetime import timedelta
from pathlib import Path


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* General page style with background image and overlay */
        .stApp {
            background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), 
                        url("https://i.imgur.com/Mbr2YOT.jpeg") no-repeat center center fixed;
            background-size: cover;
            color: #ffffff;
        }

        /* Style for navigation bar */
        .css-1d391kg {
            background-color: rgba(0, 60, 120, 0.6) !important;
            color: #ffffff !important;
            font-weight: bold;
        }

        /* General font family across app */
        .css-1v3fvcr {
            font-family: "Helvetica", sans-serif;
        }

        /* Style for buttons with smooth hover effect */
        .stButton button {
            background-color: #00214d;
            color: #ffffff;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease-in-out;
        }

        /* Button hover effect */
        .stButton button:hover {
            background-color: #005bb5;
            transform: scale(1.1);
        }

        /* Heading styles */
        h1, h2, h3 {
            color:#ffffff;
        }

        /* Style for input fields */
        input {
            color: #00214d; /* Desired text color for inputs */
            background-color: rgba(255, 255, 255, 0.8); /* Optional background color */
            border: 1px solid #cccccc; /* Optional border color */
            border-radius: 4px;
            padding: 10px;
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# MongoDB connection
@st.cache_resource
def connect_to_mongodb():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["hospital_db"]
    return db

# Initialize doctors in the database
def initialize_doctors(db):
    for doctor in doctors:
        # Add default availability if missing
        if "availability" not in doctor:
            doctor["availability"] = "09:00-17:00"
        if not db.doctors.find_one({"doctor_identity_number": doctor["doctor_identity_number"]}):
            db.doctors.insert_one(doctor)

# Update existing doctors to include availability if it's missing
def update_existing_doctors(db):
    for doctor in db.doctors.find():
        if "availability" not in doctor:
            db.doctors.update_one(
                {"_id": doctor["_id"]},
                {"$set": {"availability": "09:00-17:00"}}  # Add default availability
            )

# Initialize users in the database
def initialize_users(db):
    users = [
        {
            "username": "admin",
            "password": hash_password("admin123"),  # Hashed password
            "type": "admin",
            "name": "Admin User"
        }
        # {
        #     "username": "patient1",
        #     "password": hash_password("patient123"),  # Hashed password
        #     "type": "patient",
        #     "name": "John Doe",
        #     "age": 30
        # }
    ]
    for user in users:
        if not db.users.find_one({"username": user["username"]}):
            db.users.insert_one(user)

# Hashing password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authentication
def authenticate_user(db, username, password, user_type):
    hashed_password = hash_password(password)
    user = db.users.find_one({"username": username, "password": hashed_password, "type": user_type})
    return user

# Register user
def register_user(db, username, password, name, age, phone, email):
    if db.users.find_one({"username": username}):
        return False
    db.users.insert_one({
        "username": username,
        "password": hash_password(password),
        "type": "patient",
        "name": name,
        "age": age,
        "phone": phone,
        "email": email
    })
    return True

# Home page
def render_home():
    st.title("👩‍⚕️ Welcome to MedConnect ")

    st.title("About Us")
    st.write("""Welcome to MedConnect, a revolutionary web-based platform designed to streamline hospital operations and improve patient care using cutting-edge AI and ML technologies. 
    Our project focuses on simplifying the process of booking appointments, integrating seamlessly with hospital management systems, and providing instant assistance through AI-powered chatbots for symptom analysis and health-related inquiries.  
    This project is a result of innovation, dedication, and technical expertise brought to you by *Meghana V M* and *Sirivarshini S A*. 
    We are passionate about leveraging technology to create efficient, user-friendly solutions that address real-world healthcare challenges. With this system, we aim to enhance the patient experience, reduce administrative workloads, and modernize hospital operations.  
    Thank you for being a part of our journey. We hope our project makes a meaningful impact in the healthcare space.""")

    st.title("Contact Us")
    st.write("""We’re here to assist you! Whether you have questions about booking appointments, need help navigating our system, or simply want to share your feedback, we’d love to hear from you.
    Contact any of our contributors:
    """)
    
    st.write("Siri Varshini S A")
    st.write(""" 
    📧 [Email Siri Varshini S A:] (sirivarshinisa@gmail.com)\n  
    📞 [Call Siri Varshini S A:] (8660844495)\n\n
    """)

    st.write("Meghana V M")
    st.write("""
    📧 [Email Meghana V M:] (meghanavemala@gmail.com)\n
    📞 [Call Meghana V M:] (8296744624)
    """)

# Admin Patient Info page
def render_patient_info(db):
    st.title("🩺 Patient Information 📋")

    patients = list(db.users.find({"type": "patient"}))

    if patients:
        df_patients = pd.DataFrame(patients)
        df_patients = df_patients[["name", "age", "username", "phone", "email"]]
        st.write("### Registered Patients")
        st.dataframe(df_patients)
    else:
        st.write("No patients registered yet.")

# Book Appointment page
def render_book_appointment(db, user):
    st.title("📅 Book an Appointment")

    doctor_id = st.text_input("Enter Doctor Identity Number").strip()

    if doctor_id:
        doctor = db.doctors.find_one({"doctor_identity_number": doctor_id})
        if doctor:
            st.write(f"**Doctor Name:** {doctor['name']}")
            st.write(f"**Specialization:** {doctor['specialization']}")
            st.write(f"**Contact:** {doctor['contact']}")
            st.write(f"**Email:** {doctor['email']}")
            st.write(f"**Hospital Name:** {doctor['hospital_name']}")
            st.write(f"**Hospital Location:** {doctor['hospital_location']}")

            # Doctor's availability and working days
            availability = doctor.get("availability", "Not Specified")
            working_days = doctor.get("working_days", ["Monday", "Wednesday", "Friday"])  # Example working days
            st.write(f"**Available Time:** {availability}")
            st.write(f"**Working Days:** {', '.join(working_days)}")

            if availability != "Not Specified":
                try:
                    doctor_available_start, doctor_available_end = [
                        datetime.strptime(time.strip(), "%H:%M").time()
                        for time in availability.split("-")
                    ]

                    # Generate a list of valid dates (today + future working days)
                    st.write("### Select Appointment Date")
                    today = datetime.today().date()
                    valid_dates = [
                        today + timedelta(days=i)
                        for i in range(0, 30)  # Check up to 30 days ahead, including today
                        if (today + timedelta(days=i)).strftime("%A") in working_days
                    ]

                    # Allow the user to select only valid dates (today or future)
                    selected_date = st.date_input(
                        "Choose a Date for Appointment",
                        min_value=today,
                        value=valid_dates[0] if valid_dates else today,
                    )

                    if selected_date in valid_dates:
                        selected_weekday = selected_date.strftime("%A")

                        # Generate time slots for the selected day
                        time_slots = []
                        current_time = doctor_available_start
                        while current_time <= doctor_available_end:
                            time_slots.append(current_time.strftime("%H:%M"))
                            current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=30)).time()

                        # Fetch existing appointments for the doctor on the selected date
                        appointments = list(db.appointments.find({"doctor": doctor["name"], "date": selected_date.isoformat()}))
                        booked_slots = [appointment["appointment_time"] for appointment in appointments]

                        # Filter out the booked slots
                        available_slots = [slot for slot in time_slots if slot not in booked_slots]

                        if available_slots:
                            st.write("### Available Time Slots")
                            df_slots = pd.DataFrame(available_slots, columns=["Time Slot"])
                            st.dataframe(df_slots)

                            # Allow the patient to select a time slot
                            appointment_time = st.selectbox("Choose Appointment Time", available_slots)

                            # Collect patient details
                            name = st.text_input("Enter Patient Name", value=user['name'])
                            age = st.number_input("Enter Age", min_value=1, max_value=120, value=user.get('age', 25))
                            symptoms = st.text_area("Describe Symptoms")

                            if st.button("Submit Appointment"):
                                if name and symptoms:
                                    # Book the appointment
                                    db.appointments.insert_one({
                                        "patient_name": name,
                                        "age": age,
                                        "symptoms": symptoms,
                                        "appointment_time": appointment_time,
                                        "date": selected_date.isoformat(),
                                        "doctor": doctor["name"],
                                        "specialization": doctor["specialization"]
                                    })
                                    st.success(f"Appointment booked successfully with {doctor['name']} on {selected_date} at {appointment_time}!")
                                else:
                                    st.error("Please fill in all the details.")
                        else:
                            st.error("No available time slots for this doctor on the selected date.")
                    else:
                        st.error("Invalid date selected. Please choose today or an upcoming working day.")
                except ValueError:
                    st.error("Invalid availability format. Please contact the administrator.")
            else:
                st.error("Doctor availability is not specified.")
        else:
            st.error(f"No doctor found with Identity Number '{doctor_id}'.")
    else:
        st.write("Please enter a valid Doctor Identity Number.")


# Chatbot page
def render_chatbot():
    st.title("🤖 AI-Powered Chatbot 🗨️")

    # user_input = st.text_input("Describe your symptoms:")
    # if st.button("Analyze Symptoms"):
    #     st.write("Symptom analysis will appear here (AI integration placeholder).")
    
    # Add a link to the Streamlit app
    st.markdown(
        """
        If you'd like to use our full AI-powered symptom analysis tool, 
        please click on the following link:
        [Launch Chatbot](https://medibot-hb9rduvv3tgxt4htasvgxl.streamlit.app/)
        """,
        unsafe_allow_html=True
    )


# Manage Doctors page
def render_manage_doctors(db):
    st.title("🩺 Manage Doctors 👨‍⚕️👩‍⚕️")

    doctors_in_db = list(db.doctors.find())
    if len(doctors_in_db) > 0:
        df_doctors = pd.DataFrame(doctors_in_db)
        df_doctors["_id"] = df_doctors["_id"].astype(str)
        st.write("### Doctors List")
        st.write(df_doctors)

    # Add a new doctor
    st.write("### Add New Doctor")
    with st.form(key="add_doctor_form"):
        doctor_id = st.text_input("Doctor Identity Number (Unique)")
        name = st.text_input("Name")
        specialization = st.text_input("Specialization")
        contact = st.text_input("Contact")
        email = st.text_input("Email")
        hospital_name = st.text_input("Hospital Name")
        hospital_location = st.text_input("Hospital Location")
        availability = st.text_input("Availability (e.g., 09:00-17:00)")
        submitted = st.form_submit_button("Add Doctor")
        if submitted:
            if doctor_id and name and specialization:
                existing_doctor = db.doctors.find_one({"doctor_identity_number": doctor_id})
                if existing_doctor:
                    st.error("A doctor with this identity number already exists.")
                else:
                    db.doctors.insert_one({
                        "doctor_identity_number": doctor_id,
                        "name": name,
                        "specialization": specialization,
                        "contact": contact,
                        "email": email,
                        "hospital_name": hospital_name,
                        "hospital_location": hospital_location,
                        "availability": availability or "09:00-17:00"  # Default if not provided
                    })
                    st.success(f"Doctor {name} added successfully.")
                    st.experimental_rerun()
            else:
                st.error("Please fill all required fields.")

    # Delete doctor
    st.write("### Delete Doctor by Identity Number")
    with st.form(key="delete_doctor_form"):
        delete_doctor_id = st.text_input("Enter Doctor Identity Number")
        delete_submitted = st.form_submit_button("Delete Doctor")
        if delete_submitted:
            if delete_doctor_id:
                doctor_to_delete = db.doctors.find_one({"doctor_identity_number": delete_doctor_id})
                if doctor_to_delete:
                    db.doctors.delete_one({"doctor_identity_number": delete_doctor_id})
                    st.success(f"Doctor with Identity Number {delete_doctor_id} has been deleted.")
                    st.experimental_rerun()
                else:
                    st.error(f"No doctor found with Identity Number {delete_doctor_id}.")
            else:
                st.error("Please enter a valid Doctor Identity Number.")

# Manage Appointments page
def render_manage_appointments(db):
    st.title("📋 Manage Appointments 📅")
    
    # Fetch all appointments
    appointments = list(db.appointments.find())
    
    if len(appointments) > 0:
        df_appointments = pd.DataFrame(appointments)
        df_appointments["_id"] = df_appointments["_id"].astype(str)
        
        st.write("### Appointments")
        for _, appointment in df_appointments.iterrows():
            patient_name = appointment.get("patient_name", "N/A")
            doctor_name = appointment.get("doctor", "N/A")
            appointment_time = appointment.get("appointment_time", "N/A")
            status = str(appointment.get("appointment_status", "pending"))  # Ensure 'status' is a string
            
            with st.expander(f"Appointment with {doctor_name} for {patient_name} at {appointment_time}"):
                st.write(f"**Patient Name:** {patient_name}")
                st.write(f"**Doctor Name:** {doctor_name}")
                st.write(f"**Appointment Time:** {appointment_time}")
                st.write(f"**Symptoms:** {appointment.get('symptoms', 'N/A')}")
                st.write(f"**Current Status:** {status.capitalize()}")

                # Admin actions: Approve, Reject, Delete
                col1, col2, col3 = st.columns(3)
                
                if status == "pending":
                    # Approve button
                    if col1.button("Approve", key=f"approve_{appointment['_id']}"):
                        db.appointments.update_one(
                            {"_id": ObjectId(appointment["_id"])} ,
                            {"$set": {"appointment_status": "approved"}}
                        )
                        send_notification(db, patient_name, f"Your appointment with {doctor_name} at {appointment_time} has been approved.")
                        st.success("Appointment approved successfully.")
                        st.session_state.page = "Manage Appointments"  # Trigger rerun

                    # Reject button
                    if col2.button("Reject", key=f"reject_{appointment['_id']}"):
                        db.appointments.update_one(
                            {"_id": ObjectId(appointment["_id"])} ,
                            {"$set": {"appointment_status": "rejected"}}
                        )
                        send_notification(db, patient_name, f"Your appointment with {doctor_name} at {appointment_time} has been rejected.")
                        st.error("Appointment rejected.")
                        st.session_state.page = "Manage Appointments"  # Trigger rerun
                
                # Delete button (Available for all statuses)
                if col3.button("Delete", key=f"delete_{appointment['_id']}"):
                    db.appointments.delete_one({"_id": ObjectId(appointment["_id"])})
                    send_notification(db, patient_name, f"Your appointment with {doctor_name} at {appointment_time} has been deleted by the admin.")
                    st.warning("Appointment deleted.")
                    st.session_state.page = "Manage Appointments"  # Trigger rerun
    else:
        st.write("No appointments found.")


# Patient Notifications
def render_notifications(db, user):
    st.title("🔔 Notifications 📲")
    
    # Button to clear all notifications
    if st.button("Clear All Notifications"):
        db.notifications.delete_many({"recipient": user["name"]})
        st.success("All notifications cleared.")
    
    # Fetch notifications for the logged-in patient
    notifications = list(db.notifications.find({"recipient": user["name"]}))
    
    if len(notifications) > 0:
        for notification in notifications:
            st.info(notification["message"])
    else:
        st.write("No notifications.")


# Send Notification Function
def send_notification(db, recipient_name, message):
    db.notifications.insert_one({
        "recipient": recipient_name,
        "message": message,
        "timestamp": pd.Timestamp.now()
    })

# Adjust Navbar for Patients
def navbar(user_type):
    st.sidebar.title("Navigation")
    if user_type == "admin":
        options = ["Home", "Manage Doctors", "Manage Appointments", "Patient Info"]
    else:
        options = ["Home", "Book Appointment", "Notifications", "Chatbot"]
    choice = st.sidebar.radio("Go to", options)
    return choice


# Navigation Menu
def navbar(user_type):
    st.sidebar.title("Navigation")
    if user_type == "admin":
        options = ["Home", "Manage Doctors", "Manage Appointments", "Patient Info"]
    else:
        options = ["Home", "Book Appointment", "Notifications", "Chatbot"]
    return st.sidebar.radio("Go to", options)


# Logout function
def logout():
    st.session_state.user = None
    st.session_state.page = "Login"


# Main function
def main():
    inject_custom_css()
    db = connect_to_mongodb()
    initialize_doctors(db)
    initialize_users(db)
    update_existing_doctors(db)

    # Ensure session state is properly initialized
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "Login"

    # Page navigation handler
    if st.session_state.page == "Login":
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        user_type = st.radio("Login as:", ["patient", "admin"])
        if st.button("Login"):
            user = authenticate_user(db, username, password, user_type)
            if user:
                st.session_state.user = user
                st.session_state.page = "Home"
            else:
                st.error("Invalid credentials.")
        if st.button("Sign Up"):
            st.session_state.page = "Sign Up"

    elif st.session_state.page == "Sign Up":
        st.title("Sign Up")
        name = st.text_input("Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")
        age = st.number_input("Age", min_value=1, max_value=120, step=1)
        
        if st.button("Sign Up"):
            if name and username and password:
                success = register_user(db, username, password, name, age, phone, email)
                if success:
                    st.success("Account created successfully! Please log in.")
                    st.session_state.page = "Login"
                else:
                    st.error("Username already exists.")
            else:
                st.error("All fields are required.")

    else:
        user = st.session_state.user
        page = navbar(user["type"])

        if page == "Home":
            render_home()
        elif page == "Patient Info" and user["type"] == "admin":
            render_patient_info(db)
        elif page == "Book Appointment" and user["type"] == "patient":
            render_book_appointment(db, user)
        elif page == "Notifications" and user["type"] == "patient":
            render_notifications(db, user)
        elif page == "Chatbot" and user["type"] == "patient":
            render_chatbot()
        elif page == "Manage Doctors" and user["type"] == "admin":
            render_manage_doctors(db)
        elif page == "Manage Appointments" and user["type"] == "admin":
            render_manage_appointments(db)

        # Logout button
        if st.sidebar.button("Logout"):
            logout()


if __name__ == "__main__":
    main()
