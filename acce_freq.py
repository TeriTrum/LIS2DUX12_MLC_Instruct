"""Plot AccV magnitude and its one-sided FFT from acceleration TXT/CSV.
Install: python -m pip install numpy matplotlib
Run: python acce_freq.py "data.txt" --fs 200
Input: three comma-separated numeric columns ax,ay,az; optional first header.
Default units: mg (no unit conversion or resampling is performed).
FFT: subtract segment mean, periodic Hann window, coherent-gain correction.
Amplitude is appropriate for bin-centred steady sinusoids; transient fall
spectra are descriptive, not a direct measure of impact peak acceleration.
"""
import argparse
import io
from pathlib import Path
import numpy as np


def read_data(path):
    lines = [line.strip() for line in path.read_text(encoding='utf-8-sig').splitlines()
             if line.strip()]
    if not lines:
        raise ValueError('File is empty')
    try:
        [float(v) for v in lines[0].split(',')]
    except ValueError:
        lines = lines[1:]
    if not lines:
        raise ValueError('No numeric data after header')
    data = np.loadtxt(io.StringIO('\n'.join(lines)), delimiter=',', ndmin=2)
    if data.shape[1] != 3 or not np.isfinite(data).all():
        raise ValueError('Expected exactly 3 finite numeric columns: ax, ay, az')
    return data


def amplitude_spectrum(data, fs, remove_mean=True):
    n = len(data)
    centered = data - data.mean(axis=0) if remove_mean else data.copy()
    # Periodic Hann; no zero padding. Bin spacing = fs / n.
    window = 0.5 - 0.5*np.cos(2*np.pi*np.arange(n)/n)
    spectrum = np.fft.rfft(centered * window[:, None], axis=0)
    amplitude = np.abs(spectrum) / window.sum()
    # Double positive frequencies, but not DC or the even-length Nyquist bin.
    if n % 2 == 0:
        amplitude[1:-1] *= 2
    else:
        amplitude[1:] *= 2
    return np.fft.rfftfreq(n, d=1/fs), amplitude


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', type=Path)
    parser.add_argument('--fs', type=float, default=200., help='Actual sample rate in Hz')
    parser.add_argument('--start', type=float, default=0., help='Segment start seconds, inclusive')
    parser.add_argument('--end', type=float, help='Segment end seconds, exclusive')
    parser.add_argument('--max-freq', type=float, help='Display limit only; does not filter the data')
    parser.add_argument('--unit', default='mg', help='Input unit label only; no conversion')
    parser.add_argument('--keep-dc', action='store_true', help='Do not subtract the segment mean')
    parser.add_argument('--no-show', action='store_true', help='Run without opening GUI')
    args = parser.parse_args()
    if not np.isfinite(args.fs) or args.fs <= 0:
        parser.error('--fs must be positive and finite')
    if not np.isfinite(args.start) or args.start < 0:
        parser.error('--start must be nonnegative and finite')
    if args.end is not None and (not np.isfinite(args.end) or args.end <= args.start):
        parser.error('--end must be finite and greater than --start')
    if args.max_freq is not None and (not np.isfinite(args.max_freq) or args.max_freq <= 0):
        parser.error('--max-freq must be positive and finite')
    try:
        full = read_data(args.file)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    first = int(np.ceil(args.start*args.fs))
    last = len(full) if args.end is None else min(len(full), int(np.ceil(args.end*args.fs)))
    data = full[first:last]
    n = len(data)
    if n < 4:
        parser.error('Selected segment must contain at least 4 samples')
    # Compute magnitude BEFORE removing the mean for FFT.
    accv = np.linalg.norm(data, axis=1)
    f, amp = amplitude_spectrum(accv[:, None], args.fs, not args.keep_dc)
    print(f'File: {args.file.name}; total samples: {len(full)}')
    print(f'Selected: {n} samples; {first/args.fs:g} to {last/args.fs:g} s (end exclusive)')
    print(f'fs={args.fs:g} Hz; FFT bin spacing={args.fs/n:g} Hz; Nyquist={args.fs/2:g} Hz')
    print('Periodic Hann window; ' + ('mean retained' if args.keep_dc else 'segment mean subtracted for FFT only'))
    print('Mean AccV:', accv.mean(), args.unit)
    print('Spectrum alone does not identify noise or an optimal filter cutoff.')

    if args.no_show:
        import matplotlib
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
    t = np.arange(first, last)/args.fs
    upper = min(args.fs/2, args.max_freq or args.fs/2)
    axes[0].plot(t, accv, color='tab:blue', linewidth=1)
    axes[0].set(xlabel='Time (s)', ylabel=f'AccV ({args.unit})')
    axes[1].plot(f, amp[:, 0], color='tab:orange', linewidth=1)
    axes[1].set(title='AccV: one-sided FFT', xlabel='Frequency (Hz)',
                ylabel=f'Amplitude ({args.unit})', xlim=(0, upper))
    for ax in axes:
        ax.grid(alpha=.25)
    mode = 'mean retained' if args.keep_dc else 'mean removed'
    fig.suptitle(f'{args.file.name}\nfs={args.fs:g} Hz | N={n} | Hann | FFT: {mode}')
    if not args.no_show:
        plt.show()
    plt.close(fig)


if __name__ == '__main__':
    main()
