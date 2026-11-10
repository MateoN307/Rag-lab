---
course: ENG-3C1
tags: [embedded, timers, math]
---

# Lecture 05: Timers

Anchor: a kitchen timer that counts toward a number you pick. The hardware counter does the same thing, but it counts at the clock speed.

The timer clock is first divided by a prescaler (PSC). The counter then counts up to an auto-reload value (ARR), wraps back to zero, and fires an update event.

Core formula, with $f_{clk}$ the clock frequency:

$$
f_{timer} = \frac{f_{clk}}{(PSC + 1)(ARR + 1)}
$$

The period is $T = 1/f_{timer}$.

Worked example from class:

- $f_{clk} = 48\,\text{MHz}$
- $PSC = 47$
- $ARR = 999$

$$
f_{timer} = \frac{48 \times 10^6}{48 \times 1000} = 1000\ \text{Hz}
$$

So the update event fires every 1 ms.

Common mistake: forgetting the $+1$ terms. Without them, $48\,\text{MHz} / (47 \times 999)$ gives about 1022 Hz, not 1000 Hz. The counter starts at 0, so it has one more step than the ARR value suggests.

PWM duty cycle, where CCR is the compare register:

$$
D = \frac{CCR}{ARR + 1}
$$

With ARR = 999, a CCR of 250 gives $D = 250/1000 = 0.25$, a 25% duty cycle.

## Checklist

- [x] Compute $f_{timer}$ for PSC = 47 and ARR = 999
- [x] Compute $f_{timer}$ for PSC = 99 and ARR = 4999 at 48 MHz (answer: 96 Hz)
- [ ] Explain why ARR is off by one
