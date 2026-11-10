# Lecture 07: Sampling

Anchor: a film camera. It takes still frames at a fixed rate, and a fast spinning wheel can look like it runs backward on screen. Sampling a signal has the same problem.

## Nyquist rule

To recover a band-limited signal with maximum frequency $f_{max}$, the sampling rate must satisfy

$$
f_s > 2 f_{max}
$$

The limit $2 f_{max}$ is the Nyquist rate. Exactly equal is the borderline case, which the lecture says to avoid.

## Aliasing

When $f_s$ is too low, a high frequency lands on a lower frequency that looks identical in the samples. This is aliasing.

Example from class:

- Tone: 3 kHz
- Sampling rate: 4 kHz (below the Nyquist rate of 6 kHz)
- The samples look exactly like a 1 kHz tone, because $|3 - 4| = 1$ kHz.

Once the samples are taken, no filter can tell the two tones apart. The fix has to happen before sampling: an anti-aliasing low-pass filter.

## Practical steps

1. Set the anti-aliasing filter cutoff just below $f_s / 2$.
2. Sample at $f_s$.
3. Check the spectrum of the samples for mirrored peaks.

## Checklist

- [x] State the Nyquist rule
- [x] Find the alias of a 3 kHz tone sampled at 4 kHz (1 kHz)
- [ ] Find the alias of a 7 kHz tone sampled at 10 kHz
