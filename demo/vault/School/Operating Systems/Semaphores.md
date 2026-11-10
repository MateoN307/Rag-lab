# Semaphores

A semaphore is an integer counter with two operations: wait (also called P) and signal (also called V).

Two kinds:

- **Binary semaphore**: the value is 0 or 1. It looks like a mutex, but it has no owner, so any thread may signal it.
- **Counting semaphore**: it starts at N. It limits how many threads can use a resource at the same time.

Rules:

- `wait()`: if the value is 0, block. Otherwise decrement it.
- `signal()`: increment the value. If a thread is waiting, wake one of them.

## Bounded buffer example

A buffer with 3 slots needs 3 semaphores:

- `empty` starts at 3 (free slots)
- `full` starts at 0 (filled slots)
- `mutex` starts at 1 (protects the buffer itself)

Producer pseudocode:

```
producer:
    wait(empty)
    wait(mutex)
    put item in buffer
    signal(mutex)
    signal(full)
```

The consumer mirrors this, with `wait(full)` first and `signal(empty)` last.

## Mutex or semaphore?

Students mix these up, so see the [[Mutexes|mutex notes]] too. Quick test: if the thread that signals can be a different thread from the one that waited, it is a semaphore. If only the owner may release it, it is a mutex.
