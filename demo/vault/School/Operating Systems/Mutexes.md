# Mutexes

A mutex (short for mutual exclusion) lets one thread at a time enter a critical section.

Key rule: a mutex has an owner. Only the thread that locked it may unlock it. This is the main difference from a semaphore. See [[Semaphores]] for the other kind.

Steps for a lock:

1. Try to take the lock.
2. If it is free, you own it. Enter the critical section.
3. If it is held, block until the owner unlocks it.
4. Unlock when you leave the critical section. Do not hold it across slow I/O.

Example, using POSIX threads:

```c
pthread_mutex_lock(&account_lock);
balance = balance + deposit;
pthread_mutex_unlock(&account_lock);
```

Without the lock, two deposits can read the same balance, and one of the two writes is lost. This is called a lost update.

## Spinlocks

A spinlock busy-waits instead of blocking. A test-and-set loop looks like this:

```c
while (test_and_set(&flag)) { /* spin */ }
```

Spinning wastes CPU time while it waits. Use a spinlock only when the critical section is very short, and never on a single-core system where the owner cannot run while you spin.

## Exam tip

Question type: "Why does thread B's deposit disappear?" Answer: both threads read the balance before either wrote it back. The mutex makes the read-modify-write one step from the point of view of other threads.
