# Lecture 04: Interrupts

Anchor: a doorbell. You keep doing your work until the bell rings. Then you stop, answer the door, and go back to exactly where you were.

## Key terms

- **ISR** (interrupt service routine): the function the CPU runs when an interrupt fires.
- **Vector table**: an array of ISR addresses. The interrupt number is the index into it.
- **Latency**: time from the interrupt request to the first instruction of the ISR. On the test board it measured 12 cycles.

## Rules for writing an ISR

1. Keep it short.
2. Clear the interrupt flag first, or the interrupt fires again forever.
3. Do not call blocking functions.
   - Pass the real work to the main loop with a flag or a buffer.
   - Work to defer:
     - parsing a packet
     - updating a display
   - Work to keep in the ISR:
     - read the data register
     - push one byte into a buffer

Example:

```c
volatile uint8_t rx_flag = 0;

void USART1_IRQHandler(void) {
    USART1->SR &= ~USART_SR_RXNE;   /* clear the flag */
    rx_buffer[rx_head++] = USART1->DR;
    rx_flag = 1;
}
```

The word `volatile` tells the compiler to re-read `rx_flag` from memory each time, because the ISR changes it outside the normal flow of the program.

## Polling vs interrupts

- Polling: the main loop checks a status bit over and over. Simple, but it wastes CPU time.
- Interrupts: hardware tells the CPU when something happens. Better for rare events such as a byte arriving on a serial line.

## Checklist from class

- [x] Explain the difference between polling and interrupts
- [x] Name the three steps the CPU does on entry (save context, look up the vector table, run the ISR)
- [ ] Explain why `volatile` is needed on variables shared with an ISR

Note: the practice set asked for latency in cycles. The answer used the 12-cycle figure above.
