import numpy as np
import scipy.signal
from matplotlib import pyplot as plt
from FIR import plot_mag, plot_phase, plot_gd, plot_imp,pz_plot

fs = 48000
wp = 3000
ws = 4000
worN = 8192
gpass = 0.1
gstop = 60
ord,wn = scipy.signal.ellipord(wp,ws,gpass,gstop,fs = fs)
sos = scipy.signal.ellip(ord,gpass,gstop,wn, output= "sos", fs = fs)

def sos_responses(sos,fs, worN = 8192):
    [f, H] = scipy.signal.freqz_sos(sos,worN,fs = fs)
    magdB = 20 * np.log10(np.abs(H))
    phase = np.unwrap(np.angle(H))
    [b,a] = scipy.signal.sos2tf(sos)
    [_,gd] = scipy.signal.group_delay((b,a), w = worN, fs = fs)
    imp = np.zeros(worN)
    imp[0] = 1
    h = scipy.signal.sosfilt(sos,imp)
    return dict(
        f = f,
        mag = magdB,
        phase = phase,
        gd = gd,
        h = h
    )

  
# validate specs
R = sos_responses(sos,fs,worN)
pb = (R["f"] <= 3000)
sb = (R["f"] >= 4000)
worst = R["mag"][sb].max()
print(f"worst stopband: {worst:.2f} dB")
print(f"passband ripple: {max(R["mag"][pb])-min(R["mag"][pb])} dB")

# apply test signal
t = np.arange(0,0.1,1/fs)
test_sig = scipy.signal.square(2*np.pi*100*t)
y_iir = scipy.signal.sosfilt(sos, test_sig)

# plot
fig, ax = plt.subplots(2,2)
plot_mag(R,ax[0,0])
plot_phase(R,ax[0,1])
plot_gd(R,ax[1,0])

ax[1,1].plot(R["h"][:300])   
ax[1,1].set(xlabel="n", ylabel="Amplitude", title="Impulse Response (IIR)")
ax[1,1].grid(True)

fig1,ax1 = plt.subplots(figsize = (8,6))
z_iir, p_iir, _ = scipy.signal.sos2zpk(sos)
pz_plot(z_iir,p_iir,ax1, "IIR Filter Pole-Zero Plot")

fig2,ax2 = plt.subplots(figsize = (8,6))
ax2.plot(t,test_sig,"-b",label = "Input"); ax2.set_xlim(0,0.1)
ax2.plot(t,y_iir,"-r",label = "IIR Output")
ax2.set(ylabel = "Amplitude",xlabel = "Time", title = "Input Signal/Filtered Output")
ax2.legend(loc = "center right")
ax2.grid(True)


fig.tight_layout()
plt.show()
    



