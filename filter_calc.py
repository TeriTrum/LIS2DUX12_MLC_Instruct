"""Calculate LIS2DUX12 MLC coefficients (AN5903 sections 1.2 / 1.2.1).
Install: python -m pip install numpy scipy
kind: low, high, band
order: 1 (IIR1), 2 (IIR2)
fs: LIS2DUX12 odr
cutoff: cutoff frequency (fc)
Example: python filter_calc.py --kind low --order 1 --fs 200 --cutoff 70
         python filter_calc.py --kind band --order 2 --fs 100 --cutoff 0.2 1

The displayed decimals are short representations of float16 coefficients,
like the examples in ST Table 3; they round-trip to the same float16 value.
No plots or raw bit patterns. fs means MLC ODR.
"""
import argparse
import numpy as np
from scipy import signal


def design(kind, fs, cutoff, order):
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError('fs must be positive and finite')
    if kind == 'hp-fixed':
        return np.array([0.5, -0.5, 0.0]), np.array([1., 0., 0.]), 1., 'Fixed HP'
    if cutoff is None:
        cutoff = [2., 20.] if kind == 'band' else [5.]
    c = np.asarray(cutoff, dtype=float)
    if len(c) != (2 if kind == 'band' else 1):
        raise ValueError('band needs two cutoffs; low/high need one')
    if not np.isfinite(c).all() or np.any(c <= 0) or np.any(c >= fs / 2):
        raise ValueError('Cutoffs must satisfy 0 < f < fs/2')
    if kind == 'band' and c[0] >= c[1]:
        raise ValueError('Band edges must satisfy f1 < f2')
    if kind in ('high', 'band') and 2*c[0]/fs < 0.02:
        print('AN5903 caution: normalized cutoff < 0.02. For HP consider IIR1;')
        print('for BP raise the low edge or redesign and check stability carefully.')
    # Equivalent to butter(N, cutoff/(fs/2), btype=...) in AN5903.
    n = 1 if kind == 'band' else order
    b, a = signal.butter(n, c if kind == 'band' else c[0],
                         btype={'low':'lowpass','high':'highpass','band':'bandpass'}[kind],
                         fs=fs, output='ba')
    b, a = b / a[0], a / a[0]
    if kind == 'band':
        gain = float(b[0])
        assert np.allclose(b/gain, [1., 0., -1.])
        return np.array([1., 0., -1.]), a, gain, 'BP (butter N=1; actual order=2)'
    return np.pad(b, (0, 3-len(b))), np.pad(a, (0, 3-len(a))), 1., f'{kind.upper()} IIR{order}'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--kind', choices=['low', 'high', 'band', 'hp-fixed'], default='high')
    parser.add_argument('--fs', type=float, default=200.)
    parser.add_argument('--order', type=int, choices=[1, 2], default=2,
                        help='LP/HP order. BP always uses butter N=1 (actual order 2).')
    parser.add_argument('--cutoff', type=float, nargs='+')
    args = parser.parse_args()
    try:
        b, a, gain, name = design(args.kind, args.fs, args.cutoff, args.order)
    except ValueError as error:
        parser.error(str(error))
    with np.errstate(over='ignore'):
        values = np.array([*b, a[1], a[2], gain], dtype=np.float16)
    if not np.isfinite(values).all():
        parser.error('Coefficient overflow in float16')

    print(f'\n{name} | MLC ODR = {args.fs:g} Hz')
    edges = [args.fs / 4] if args.kind == 'hp-fixed' else (args.cutoff or ([2., 20.] if args.kind == 'band' else [5.]))
    print('Cutoff: ' + ', '.join(f'{edge:g}' for edge in edges) + ' Hz')
    print('\nCoefficient    Value (float16)')
    for label, value in zip(['b1', 'b2', 'b3', 'a2', 'a3', 'Gain'], values):
        # Format the float16 scalar itself, NOT float(value): preserve short
        # decimals that convert back to the same half-precision coefficient.
        formatted = np.format_float_positional(value, unique=True, trim='-')
        print(f'{label:<14} {formatted}')
    aq = np.array([1., float(values[3]), float(values[4])])
    if np.any(np.abs(np.roots(aq)) >= 1):
        print('WARNING: filter is not strictly stable after float16 rounding.')


if __name__ == '__main__':
    main()
