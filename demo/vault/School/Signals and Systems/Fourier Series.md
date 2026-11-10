# Fourier Series

Anchor: a chord on a piano. Any repeating sound can be built from simple sine waves at whole-number multiples of one base frequency. The Fourier series gives the "recipe": how much of each harmonic to add.

For a signal $x(t)$ with period $T$, the base (fundamental) angular frequency is

$$
\omega_0 = \frac{2\pi}{T}
$$

The synthesis equation rebuilds the signal from its coefficients:

$$
x(t) = \sum_{k=-\infty}^{\infty} a_k\, e^{j k \omega_0 t}
$$

The analysis equation finds each coefficient:

$$
a_k = \frac{1}{T} \int_{T} x(t)\, e^{-j k \omega_0 t}\, dt
$$

Why the integral: multiplying by $e^{-jk\omega_0 t}$ and averaging over one period picks out only the harmonic $k$. Every other harmonic averages to zero over a full period. This is called orthogonality, and it is the whole reason the method works.

## Worked example: 0-to-1 square wave

- Period $T = 8\ \text{s}$, so $\omega_0 = \pi/4\ \text{rad/s}$.
- Value is 1 for $|t| < 2\ \text{s}$ and 0 elsewhere in the period, centred on $t = 0$ (duty cycle 50%). Centring matters: shifting the pulse changes the phase of each $a_k$.
- The DC term is the average value: $a_0 = 0.5$.
- For $k \neq 0$, the lecture result is

$$
a_k = \frac{\sin(k\pi/2)}{k\pi}
$$

So $a_1 \approx 0.318$ and $a_2 = 0$. Even harmonics vanish for this duty cycle.

## Checklist

- [x] Compute $\omega_0$ for $T = 8\ \text{s}$
- [x] Show that $a_2 = 0$ for the 50% square wave
- [ ] Derive $a_k$ for a duty cycle of 25%
