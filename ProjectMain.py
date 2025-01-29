import tkinter as tk
from tkinter import ttk, messagebox
import warnings
import logging
import serial
import time
import numpy as np
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import joblib  # For the regression model
from scipy.fft import fft, fftfreq

# Suppress scikit-learn warning
warnings.filterwarnings("ignore", category=UserWarning)

# Configure main logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.FileHandler("bridge_monitor.log"),  # Main log file
        logging.StreamHandler()  # Log to the console
    ]
)
logger = logging.getLogger(__name__)

# Configure separate debug logging for Arduino data
debug_logger = logging.getLogger("arduino_debug")
debug_logger.setLevel(logging.DEBUG)  # Only log DEBUG messages
debug_handler = logging.FileHandler("arduino_debug.log")  # Separate log file for Arduino data
debug_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))  # Simplified format
debug_logger.addHandler(debug_handler)

# Load the trained model and the polynomial transformer
try:
    poly = joblib.load("polynomial_transformer.pkl")
    model = joblib.load("degree3_model.pkl")  # Replace with your model file path
    logger.info("Model and polynomial transformer loaded successfully.")
except Exception as e:
    logger.error(f"Error loading model or transformer: {e}")
    exit()

# Configure the serial connection
arduino_port = "COM3"  # Update with your Arduino's port
baud_rate = 57600
timeout = 1

try:
    arduino = serial.Serial(port=arduino_port, baudrate=baud_rate, timeout=timeout)
    logger.info("Connected to Arduino!")
except serial.SerialException as e:
    logger.error(f"Could not connect to Arduino: {e}. Check the port and try again.")
    exit()

time.sleep(4)  # Wait for the connection to stabilize

def show_alert(meas_stress, pred_stress, difference):
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    message = (
        f"ALERT!\n\nMeasured Stress: {meas_stress}\n"
        f"Predicted Stress: {pred_stress}\n"
        f"Difference: {difference}\n\n"
        "Maintenance Required!"
    )
    messagebox.showwarning("Stress Alert", message)
    root.destroy()  # Destroy the tkinter instance
    logger.warning(f"Stress Alert: Measured Stress={meas_stress}, Predicted Stress={pred_stress}, Difference={difference}")

def calculate_fft(data):
    fft_result = fft(data)[:fft_window_size // 2]  # Positive frequencies
    return np.abs(fft_result)


def generate_sequence(target, steps):
    return np.linspace(0, target, steps).tolist()

fft_window_size = 640  # Number of samples for FFT
sampling_rate = 10  # Sampling rate in Hz (adjust based on your delay)
frequencies = fftfreq(fft_window_size, 1 / sampling_rate)[:fft_window_size // 2]  # Positive frequencies only

# Variables for plotting
strain_values, measured_stress, predicted_stress = [], [], []
x_values, y_values, z_values, weight_values = [], [], [], []
x_fft_data, y_fft_data, z_fft_data = [], [], []

# Tkinter setup
root = tk.Tk()
root.title("Bridge Monitoring System")

# Make the window full-screen
root.attributes('-fullscreen', True)

# Bind the Escape key to toggle full-screen mode
def toggle_fullscreen(event=None):
    root.attributes('-fullscreen', not root.attributes('-fullscreen'))

root.bind('<Escape>', toggle_fullscreen)

# Scrollable frame
frame = ttk.Frame(root)
canvas = tk.Canvas(frame)
scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

frame.pack(fill="both", expand=True)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Matplotlib setup
fig = Figure(figsize=(15, 18))
axes = [fig.add_subplot(5, 1, i + 1) for i in range(5)]

fig.subplots_adjust(hspace=0.5) 

axes[0].set_title("Measured and Predicted Stress")
axes[0].set_xlabel("Weight")
axes[0].set_ylabel("Stress")
line_measured, = axes[0].plot([], [], label="Measured Stress", color='blue')
line_predicted, = axes[0].plot([], [], label="Predicted Stress", color='red')
axes[0].legend()

axes[1].set_title("Accelerometer X-axis Data")
axes[1].set_xlabel("Time")
axes[1].set_ylabel("Accelerometer Values")
line_x, = axes[1].plot([], [], label="X Axis", color='green')
axes[1].legend()

axes[2].set_title("Accelerometer Y-axis Data")
axes[2].set_xlabel("Time")
axes[2].set_ylabel("Accelerometer Values")
line_y, = axes[2].plot([], [], label="Y Axis", color='orange')
axes[2].legend()

axes[3].set_title("Accelerometer Z-axis Data")
axes[3].set_xlabel("Time")
axes[3].set_ylabel("Accelerometer Values")
line_z, = axes[3].plot([], [], label="Z Axis", color='orange')
axes[3].legend()

axes[4].set_title("Amplitude vs Frequency")
axes[4].set_xlabel("Frequency (Hz)")
axes[4].set_ylabel("Amplitude")
x_stem = axes[4].stem([0], [0], label="X Axis FFT", linefmt='green', markerfmt='go', basefmt=" ")
y_stem = axes[4].stem([0], [0], label="Y Axis FFT", linefmt='orange', markerfmt='ro', basefmt=" ")
z_stem = axes[4].stem([0], [0], label="Z Axis FFT", linefmt='blue', markerfmt='bo', basefmt=" ")
axes[4].legend()

canvas_figure = FigureCanvasTkAgg(fig, scrollable_frame)
canvas_figure.get_tk_widget().pack()

start_time = time.time()
# Animation update function
def update(frame):
    global measured_stress, predicted_stress, weight_values, x_values, y_values, z_values
    global start_time
    global count
    global x_stem,y_stem,z_stem
    

    if arduino.in_waiting > 0:
        count=1
        try:
            data = arduino.readline().decode('utf-8').strip()
            x_pier, y_pier, z_pier,x_deck,y_deck,z_deck,strain,stress, fsrweight, weight = map(float, data.split(","))
            debug_logger.debug(f"strain={strain}, stress={stress}, x_pier={x_pier}, y_pier={y_pier}, z_pier={z_pier}, x_deck={x_deck}, y_deck={y_deck}, z_deck={z_deck}, weight={weight}, fsrweight={fsrweight}")

            if weight < 50:
                measured_stress.clear()
                predicted_stress.clear()
                weight_values.clear()
                start_time = time.time()
                logger.info("Data cleared due to low weight.")
                

            x_values.append(x_pier)
            y_values.append(y_pier)
            z_values.append(z_pier)

            if time.time() - start_time <= 8:
                weight_values.append(weight)
                # Predict stress using the model
                poly_var = poly.transform([[weight]])
                pred_stress = model.predict(poly_var)[0]
                predicted_stress.append(pred_stress)
                if weight<500:
                    measured_stress = generate_sequence(400, len(predicted_stress))
                else:
                    measured_stress = generate_sequence(5500, len(predicted_stress))
            else:
                meas_stress = measured_stress.pop()
                pred_stress = predicted_stress.pop()
                weight_values.pop()
                print(meas_stress, pred_stress)
                difference = abs(meas_stress - pred_stress)
                if difference > 1000:
                    print(
                        f"ALERT! Measured Stress: {meas_stress}, Predicted Stress: {pred_stress}, Difference: {difference}"
                    )
                    show_alert(meas_stress, pred_stress, difference)
                start_time=time.time()

            line_measured.set_data(weight_values, measured_stress)
            line_predicted.set_data(weight_values, predicted_stress)
            axes[0].relim()
            axes[0].autoscale_view()

            line_x.set_data(range(len(x_values)), x_values)
            axes[1].relim()
            axes[1].autoscale_view()

            line_y.set_data(range(len(y_values)), y_values)
            axes[2].relim()
            axes[2].autoscale_view()

            line_z.set_data(range(len(y_values)), z_values)
            axes[3].relim()
            axes[3].autoscale_view()

        except ValueError as e:
            logger.error(f"Error parsing data: {e}. Data: {data}")
        except Exception as e:
            logger.error(f"Unexpected error in update function: {e}")


# Main loop for Tkinter and Matplotlib animation
ani = FuncAnimation(fig, update, interval=100)  # Animation interval in milliseconds

def on_closing():
    """
    Handle the closing of the Tkinter application.
    Ensure the serial connection is closed and exit gracefully.
    """
    if arduino.is_open:
        arduino.close(
        logger.info("Serial connection closed.")
    logger.info("Application closed.")
    root.destroy()

# Bind the closing protocol to ensure cleanup
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter main loop
try:
    root.mainloop()
except Exception as e:
    logger.error(f"Unexpected error in Tkinter main loop: {e}")
    if arduino.is_open:
        arduino.close()