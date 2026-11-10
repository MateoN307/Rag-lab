---
course: ENG-3C1
due: 2026-10-16
tags: [lab, embedded, uart]
---

# Lab 2: UART Logger

Goal: receive text over a serial link at 115200 baud and store it in a ring buffer. A timer prints a status line every 500 ms.

![[uart-wiring.png]]

Wiring for the SmartPad-7 dev board used in class:

- PA9 is TX, goes to the RX pin of the USB-serial adapter
- PA10 is RX, goes to the TX pin of the adapter
- GND to GND, nothing else

Serial settings:

- Baud rate: 115200
- Data bits: 8, no parity, 1 stop bit
- Buffer size: 256 bytes

This builds on [[Lecture 04 - Interrupts|the interrupts lecture]]. The interrupt handler puts each byte in the buffer; the main loop prints them.

Code sketch:

```c
#define BUF_SIZE 256
static volatile uint8_t buf[BUF_SIZE];
static volatile uint16_t head = 0, tail = 0;

static int buf_push(uint8_t b) {
    uint16_t next = (head + 1) % BUF_SIZE;
    if (next == tail) return -1;   /* full: drop the byte */
    buf[head] = b;
    head = next;
    return 0;
}
```

Grading notes:

- Dropped bytes must be counted and printed. This is worth 10% of the lab.
- Demo on the bench, not in the simulator.

Mistakes the TA listed in last year's feedback:

- Forgot to clear the flag, so the handler ran forever.
- Called `printf` inside the handler, and the board hung.

Status: buffer code done. Still need the drop counter.
