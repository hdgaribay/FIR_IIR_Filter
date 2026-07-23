import numpy as np
import matplotlib.pyplot as plt
fs = 48000
fc =3500
N = 63
beta = 5.65 # beta value for 60dB stopband atten.
# windowed sinc method
n = np.arange(N) - N-1/2 # create symmetric time index
coeff = 2 * (fc/fs) * np.sinc(2*(fc/fs)*n) # impulse response of lowpass filter
kaiser_window = np.kaiser(N-1,beta) 
coeff *= kaiser_window # window