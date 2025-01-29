import numpy as np
import matplotlib.pyplot as plt

# Example signal (replace with your actual signal)
signal = np.random.rand(100)  # Replace with your signal
fs = 10  # Sampling frequency (Hz)
n = len(signal)
frequencies = np.fft.fftfreq(n, d=1/fs)
fft_values = np.fft.fft(signal)

# Only take the positive frequencies and corresponding amplitudes
positive_frequencies = frequencies[:n // 2]
amplitudes = np.abs(fft_values)[:n // 2]

# Plotting the frequency response using a stem plot
plt.stem(positive_frequencies, amplitudes, basefmt=" ", use_line_collection=True)
plt.title("Amplitude vs Frequency")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.grid()
plt.show()
