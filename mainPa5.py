import streamlit as st
from streamlit_navigation_bar import st_navbar
import bcrypt
import sqlite3
import USB_ExampleClassStreamlit
from ThreeSpaceAPIStreamlit import *
from time import sleep
import csv
import os
#import winsound
import re


st.set_page_config(page_title="LetSense", layout="wide")

# Connect to SQLite database (or create it)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, email TEXT)''')
conn.commit()

# Function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Function to check passwords
def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode(), hashed_password.encode())

# Letrep Logo
col1, col2, col3 = st.columns(3)

# Only display the logo if the user is not logged in
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    with col2:
        st.image('./WebsiteLogo.png', width=370)


# Only display the login page title if the user is not logged in
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("Login Page")

# Registration form
if 'register' not in st.session_state:
    st.session_state['register'] = False

if 'logged_in' not in st.session_state:
       st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
       if st.button('Register'):
              st.session_state['register'] = True

if st.session_state['register']:
    new_username = st.text_input('New Username')
    new_password = st.text_input('New Password', type='password')
    email = st.text_input('Email')
    if st.button('Submit Registration'):
        hashed_password = hash_password(new_password)
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (new_username, hashed_password, email))
        conn.commit()
        st.success('User registered successfully')
        st.session_state['register'] = False

# Login form
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button('Login'):
        c.execute('SELECT password, email FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        if result and check_password(result[0], password):
            st.success(f'Welcome {username}')
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['email'] = result[1]
            st.rerun()
        else:
            st.error('Username/password is incorrect')

#Display pages only when the user is logged in            
if st.session_state['logged_in']:
    pages = ["Home", "Instructions", "Data Collection", "About"]
    page = st_navbar(pages)
    #st.write(f"You selected: {page}")

    # Display the selected page content
    if page == "Home":
        st.title("Home Page")
        st.write("")
        st.write(f"Welcome {st.session_state['username']}!")
        st.write("")
        st.write("Returning users, you can click the Data Collection tab to begin. New users, please click the instructions page and follow the steps for guidance regarding sensor setup and data collection.")
        st.write("")
    elif page == "Instructions":
        st.title("Instructions Page")
        st.write("")
        st.write("Please follow the steps below for accurate data collection and ensure Wifi is connected for 6 hours.")
        st.write("")
        st.write("- Include instructions regarding sensor placement (add videos)")
        st.write("- Include instructions regarding sensor calibration")
        st.write("")
        st.write("Once you have placed the sensors on your body and have calibrated the sensors correctly, you may click the Data Collection tab to begin collecting data.")
        st.write("Please refer to the user manual if there is any misconfusion or trouble with sensor connection.")
        st.write("")
    elif page == "Data Collection":
        st.title("Data Collection Page")
        st.write("")
        st.write("When you have both sensors placed correctly and are ready, please fill out the following and begin data collection.")

        # Initialize constants and globals
        MICROSECONDS_IN_A_SECOND = 1000000
        PORT = None  # Autodetect the port, modify if necessary
        TIMEOUT = 0.7
        LOGICAL_IDS = [0, 1]  # Assuming two sensors
        DESIRED_SAMPLES_PER_SECOND = 100

        # Function to find the next iteration number for saving CSV files
        def find_next_iteration_number():
            pattern = re.compile(r'IMU\d{2}_Duration_Collection_(\d{2})\.csv')
            highest_iteration = 0

            for filename in os.listdir('.'):
                match = pattern.match(filename)
                if match:
                    iteration_number = int(match.group(1))
                    if iteration_number > highest_iteration:
                        highest_iteration = iteration_number

            return highest_iteration + 1

        # Function to start recording
        def start_recording(patient_name, date, session):
            iteration = find_next_iteration_number()
            fileName = str(patient_name + '_' + date + '_Session#' + session)

            # Open new CSV files for writing
            st.session_state.csvfile_0 = open(f'IMU00_{fileName}.csv', 'w', newline='')
            st.session_state.csvfile_1 = open(f'IMU01_{fileName}.csv', 'w', newline='')

            # Create new CSV writers
            st.session_state.writer_0 = csv.writer(st.session_state.csvfile_0)
            st.session_state.writer_1 = csv.writer(st.session_state.csvfile_1)

            #winsound.Beep(400, 50)  # Beep at 400 Hz for 50 milliseconds
            #winsound.Beep(800, 70)  # Beep at 800 Hz for 70 milliseconds

            st.session_state.data_collection_active = True
            return iteration

        # Function to stop recording
        def stop_recording():
            #winsound.Beep(700, 50)  # Beep at 700 Hz for 50 milliseconds
            #winsound.Beep(300, 70)  # Beep at 300 Hz for 70 milliseconds

            if st.session_state.csvfile_0:
                st.session_state.csvfile_0.close()
            if st.session_state.csvfile_1:
                st.session_state.csvfile_1.close()

            st.session_state.data_collection_active = False
            st.session_state.writer_0 = None
            st.session_state.writer_1 = None
            st.session_state.csvfile_0 = None
            st.session_state.csvfile_1 = None

        # Function to record data
        def record_data(senTSS):
            for id in LOGICAL_IDS:
                packet = senTSS.getOldestStreamingPacket(logicalID=id)
                if packet is not None:
                    if id == 0 and st.session_state.writer_0 is not None:
                        st.session_state.writer_0.writerow(packet)
                    elif id == 1 and st.session_state.writer_1 is not None:
                        st.session_state.writer_1.writerow(packet)

        patient_name = st.text_input("Please enter your name:")
        date = st.text_input("Please enter the date (e.g., 11_7_24):")
        session = st.text_input("Please enter the session number:")

        # Display an alert if patient name or date is not provided
        if not patient_name or not date or not session:
            st.warning("Please fill in 'Name', 'Date', and 'Session' before starting data collection.")

        st.write("")
        st.subheader("Click the button below to toggle data collection")

        # Toggle button to start/stop data collection
        toggle_button_label = "Start Data Collection" if 'data_collection_active' not in st.session_state or not st.session_state.data_collection_active else "Stop Data Collection"

        if st.button(toggle_button_label):
            if 'data_collection_active' not in st.session_state or not st.session_state.data_collection_active:
                # Start the data collection
                if patient_name and date and session:
                    iteration = start_recording(patient_name, date, session)
                    #st.success("Recording started. Data collection has successfully begun.")

                    # Setup for the sensor
                    senCom = USB_ExampleClassStreamlit.UsbCom(PORT, timeout=TIMEOUT)
                    senTSS = None

                    try:
                        st.write("Initializing sensor...")
                        senTSS = ThreeSpaceSensor(senCom, streamingBufferLen=1000)
                        st.write("Sensor initialized successfully")
                        st.success("Recording started. Data collection has successfully begun.")
                        st.write("Upon finishing data collection, please press the Start Data Collection button to toggle to the Stop Data Collection Button, then press the Stop Data Collection button in order to save the data that was recorded during your session. Once data has been succesfully saved, you will get a message saying that data collection has successfully ended.")
                    except Exception as e:
                        st.error(f"Error initializing sensor: {str(e)}")
                        st.error("Make sure the sensor is connected to the correct COM port.")
                        st.error("If the sensor is powered off, turn it on and try again.")

                    if senTSS:
                        senTSS.comClass.sensor.reset_input_buffer()
                        for id in LOGICAL_IDS:
                            senTSS.startStreaming(logicalID=id)

                        # Collect data in the background
                        while st.session_state.data_collection_active:
                            record_data(senTSS)
                            sleep(0.01)  # Adjust this based on your desired sample rate
            else:
                # Stop the data collection
                stop_recording()
                st.success("Recording stopped. Data collection has successfully ended. Thank you!")
                st.balloons()

        st.write("")
    elif page == "About":
        st.title("About Page")
        st.write("")
        st.write("LETREP 25 is developing a wearable sensor system using two inertial measurement units (IMUs) to track a patient’s lumbar range of motion (ROM) and accurately collect data at home during activities of daily living. The data taken by the sensors will be integrated into a comprehensive app for doctors to analyze and improve patient care.")
        st.write("")
        st.image('./IMG_1694.JPG', width=500)
        st.write("The team consists of (left to right) Ko Sasaki, Kigen Karani, Brooke Madsen, Lindsey Hall, Emma Boulanger, Ty Shannon, Alexa Neilon, Kaci Monk")
        st.write("")
        st.write("")
        st.write("If you believe that you were hurt or became sick because of the procedures done during data collection, you should immediately contact your personal physician, then notify Dr. Sasaki at (903) 233-3945. It is important for you to understand that LeTourneau University will not compensate for the cost of any care or treatment that might be necessary.")
        st.write("If you have questions at any time, you may contact Dr. Kotaro Sasaki at (903) 233-3945, KoSasaki@letu.edu or Wendy Whitmire, Office of Sponsored Programs, LeTourneau University, (903) 233-3981, WendyWhitmire@letu.edu with any questions, concerns, or complaints about the research procedures.")
        st.write("")

# Shutdown button
if st.button('Shutdown App'):
    st.stop()
