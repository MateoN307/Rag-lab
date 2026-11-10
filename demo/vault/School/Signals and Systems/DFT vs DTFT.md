# DFT vs DTFT

These two look almost the same, and that is the trap. Keep them apart with one question: is the signal finite, and is the frequency axis continuous?

## DTFT (discrete-time Fourier transform)

For an aperiodic signal $x[n]$ of infinite length:

$$
X(e^{j\omega}) = \sum_{n=-\infty}^{\infty} x[n]\, e^{-j\omega n}
$$

- Input: infinite sequence.
- Output: a continuous function of $\omega$. You can evaluate it at any frequency.

## DFT (discrete Fourier transform)

For a finite sequence of $N$ samples:

$$
X[k] = \sum_{n=0}^{N-1} x[n]\, e^{-j 2\pi k n / N}, \quad k = 0, 1, \ldots, N-1
$$

- Input: $N$ samples.
- Output: $N$ values, at the frequencies $\omega_k = 2\pi k / N$.
- The DFT is the DTFT sampled at $N$ equally spaced frequencies.

## Worked example

Let $x[n] = [1, 1, 1, 1, 0, 0, 0, 0]$, so $N = 8$.

- $X[0] = 1 + 1 + 1 + 1 = 4$
- $X[1]$ uses $e^{-j\pi n/4}$ over the same samples, which gives a complex value of magnitude about 2.61.

The DTFT of the same finite sequence is a smooth curve that you can read at $\omega = \pi/4$ or any other value. The DFT only gives you the 8 values at $\omega_k = 2\pi k/8$.

## Quick test

- "Compute the spectrum at 0.3 rad" points to the DTFT.
- "Compute the 8-point spectrum" points to the DFT.
- If the question says "length $N$", it is the DFT.

Related: [[Fourier Series]], [[Lecture 07 - Sampling]].
