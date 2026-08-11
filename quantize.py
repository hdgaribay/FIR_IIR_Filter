import numpy as np
import scipy.signal
import FIR, IIR

fs = 48000

def quantize(num_bits,fractional_bits,value):
    scaling = 2**fractional_bits
    coefficients = np.round(np.asarray(value)*scaling)
    lo,hi = -2**(num_bits-1),2**(num_bits-1)-1 # range of two's complement signed coefficients
    if np.any(coefficients < lo) or np.any(coefficients > hi):
        print(f"CLIP: range [{coefficients.min():.0f},{coefficients.max():.0f}], limit{[lo,hi]}")
    coefficients = np.clip(coefficients,lo,hi) # quantize coefficients
    return coefficients/scaling,coefficients.astype(int) # returns both real valued and integer version

# Examine quantization effects on Remez filter taps using several Q1.(B-1) formats.
for num_bits in [8,10,12,14,16]:
    G = 4
    qscaled, qint = quantize(num_bits,num_bits-1,FIR.taps*G) # also grab integer coefficients for HDL
    qtaps = qscaled/G
    [f,H] = scipy.signal.freqz(qtaps,worN = 8192,fs = fs)
    mag = 20*np.log10(np.abs(H))
    print(f"{num_bits:2d}-bit  ripple {mag[f<=3000].max()-mag[f<=3000].min():.4f} dB" f"worst stopband {mag[f>=4000].max():6.2f} dB")

def quantize_sos(sos,nb_num,nf_num,nb_den,nf_den):
    sq = np.copy(sos)
    sq[:,0:3], _  = quantize(nb_num,nf_num,sos[:,0:3])
    sq[:,4:6], _  = quantize(nb_den,nf_den,sos[:,4:6])
    sq[:,3] = 1.0
    return sq

sosq = quantize_sos(IIR.sos,16,14,16,14) # quantized second order section coefficients
# examine sos quantized results
[f,H] = scipy.signal.freqz_sos(sosq,worN = 8192, fs = fs)
mag = 20 * np.log10(np.abs(H))
print("Ripple:", mag[f<=3000].max()-mag[f<=3000].min())
print("Worst Stopband:", mag[f>=4000].max())

def round_to_nearest(acc,acc_shift):
    if acc_shift == 0:
        return acc
    half = 1 << (acc_shift-1)
    if acc >= 0:
        return (acc + half) >> acc_shift
    else:
        return -(((-acc) + half) >> acc_shift)
# fixed point fir implementation
def fir_fixed(x_int,coeff_int,acc_shift):
    num_taps = len(coeff_int)
    num_samples = len(x_int)
    output_int = []
    max_acc = 0
    for n in range(num_samples):
        acc = 0
        for k in range(num_taps):
            if n-k >= 0:
                acc += np.int64(x_int[n-k]) * np.int64(coeff_int[k])
        max_acc = max(max_acc, abs(acc))  # continuously update max acc after each sample
        y = round_to_nearest(acc,acc_shift)
        output_int.append(y)
    print("max |acc|:", max_acc, "-> needs", int(np.ceil(np.log2(max_acc))) + 1, "bits")
    return np.array(output_int,dtype = np.int64)

t = np.arange(0,0.3,1/fs)
chirp = scipy.signal.chirp(t,0,0.3,fs/2,"linear")
tones = (np.sin(2*np.pi*1000*t) + np.sin(2*np.pi*3000*t) + np.sin(2*np.pi*10000*t))/3
np.random.seed(0)
noise = np.random.uniform(-1,1,len(t))
x = np.concatenate([chirp,tones,noise]) * 0.9 # test_signal
quant_x = np.round(x * 32767).astype(np.int64)
_,quant_coeff = quantize(16,15,FIR.taps * 4)
output = fir_fixed(quant_x,quant_coeff, 17)

y_float = np.convolve(FIR.taps, x)[:len(x)] # truncate to length of input (fir_fixed runs until input stops) 
err = output - np.round(y_float * 2**15) # error in LSB's
print("max err (LSBs):", np.abs(err).max())
assert np.abs(err).max() < 20, "fixed-point model diverges from float — check acc_shift"

np.savetxt("stimulus.txt", quant_x, fmt="%d") # input to HDL
np.savetxt("golden.txt",   output,  fmt="%d") # ground truth
print(len(quant_x), "samples")
print("input  range:", quant_x.min(), quant_x.max())
print("output range:", output.min(), output.max())

# write quantized coeff's in hex for HDL
with open("coeffs.hex", "w") as f:
    for v in quant_coeff:
        f.write(format(v & 0xFFFF, "04x") + "\n") # keep lowest 16 bits, format as hex


