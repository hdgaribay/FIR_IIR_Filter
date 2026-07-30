import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
fs = 48000
fc = 3500
N = 197
beta = 5.65 # beta value for 60dB stopband atten.

# windowed sinc method
def design_fir(fs,fc,N,beta):
    n = np.arange(N) - (N-1)/2 # create symmetric time index
    coeff = 2 * (fc/fs) * np.sinc(2*(fc/fs)*n) # impulse response of lowpass filter
    kaiser_window = np.kaiser(N,beta) 
    coeff *= kaiser_window 
    coeff /= np.sum(coeff) # normalize coefficients so DC sums to 1
    return coeff

def responses(coeff,fs, worN = 8192):
    f,r = scipy.signal.freqz(b = coeff,worN = 8192, fs = fs) # frequency response
    magdB = 20 * np.log10(np.abs(r))
    phase = np.unwrap(np.angle(r))
    #group delay
    _,gd = scipy.signal.group_delay((coeff,1),w = 8192, fs = fs)
    return dict(
        f = f,
        mag = magdB,
        phase = phase,
        gd = gd,
        h = coeff
    )

# plotting helpers
def plot_mag(R,ax,label = None):
    ax.plot(R["f"],R["mag"],label = label)
    ax.set(xlabel = "Frequency (Hz)", ylabel = "Magnitude (dB)", title = "Magnitude Response")
    ax.grid(True)
def plot_phase(R,ax,label = None):
    ax.plot(R["f"],R["phase"],label = label)
    ax.set(xlabel = "Frequency (Hz)", ylabel = "Phase (rad)", title = "Phase Response")
    ax.grid(True)
def plot_gd(R,ax,label = None):
    ax.plot(R["f"],R["gd"],label = label)
    ax.set(xlabel = "Frequency (Hz)", ylabel = "Group Delay (samples)", title = "Group delay")
    ax.grid(True)
def plot_imp(R,ax,label = None):
    ax.stem(np.arange(len(R["h"])),R["h"],label = label)
    ax.set(xlabel = "n", ylabel = "Amplitude", title = "Impulse Response")
    ax.grid(True)
def pz_plot(z, p, ax, title):
    th = np.linspace(0, 2*np.pi, 512)
    ax.plot(np.cos(th), np.sin(th), 'k--', lw=0.8)      # unit circle
    ax.plot(z.real, z.imag, 'o', mfc='none', label='zeros')
    ax.plot(p.real, p.imag, 'x', label='poles')
    ax.set(xlabel='Re', ylabel='Im', title=title, aspect='equal')
    ax.grid(True); ax.legend()

# Parks-McClellan Method
num_taps = 167
pb_edge = 3000
sb_edge = 4000
edges = [0,pb_edge,sb_edge,0.5 * fs]
weight = [1,100] 
gain = [1,0.001] # desired gain in passband and stopband
taps = scipy.signal.remez(num_taps,edges,gain, weight = weight, fs = fs)

# test filter with a square wave
t = np.arange(0,0.1,1/fs)
test_sig = scipy.signal.square(2*np.pi*100*t)
y_fir = np.convolve(taps,test_sig)[75:75+len(test_sig)]

# plot
def centered(N):
    return np.arange(len(N)) - len((N-1))/2 # center impulse responses of different length

coeff = design_fir(fs,fc,N,beta)      
R1 = responses(coeff, fs, worN = 8192)
R2 = responses(taps,fs,worN = 8192)
fig, ax = plt.subplots(2, 2, figsize=(8,6))

plot_mag(R1, ax[0,0], label = "Windowed"); ax[0,0].axhline(-60, color='r', ls='--', lw=0.8)
plot_mag(R2, ax[0,0],label = "Parks-Mclellan")
plot_phase(R1, ax[0,1], label = "Windowed")
plot_phase(R2,ax[0,1],label = "Parks-Mclellan")
plot_gd(R1, ax[1,0], label = "Windowed")
plot_gd(R2, ax[1,0], label="Parks-McClellan")

ax[1,1].plot(centered(coeff),coeff,label = "Windowed")
ax[1,1].plot(centered(taps),taps, label = "Parks-Mclellan")
ax[1,1].set(xlabel="n (centered)", ylabel="Amplitude", title="Impulse Response")
ax[1,0].set_ylim(70,100)
ax[1,1].grid(True)
ax[0,0].legend(); ax[0,1].legend();ax[1,0].legend(); ax[1,1].legend()

z_fir, p_fir, _ = scipy.signal.tf2zpk(coeff, [1])
fig1,ax1 = plt.subplots(figsize = (8,6))
pz_plot(z_fir,p_fir,ax1,"Pole-Zero Plot")

fig2,ax2 = plt.subplots(figsize = (8,6))
ax2.plot(t,test_sig,"-b",label = "Input"); ax2.set_xlim(0,0.1)
ax2.plot(t,y_fir,"-r",label = "FIR Output (Delay Compensated)")
ax2.set(ylabel = "Amplitude",xlabel = "Time", title = "Input Signal/Filtered Output")
ax2.legend()
ax2.grid(True)

fig.tight_layout()
plt.show()
