# Lecture 09: CPU Scheduling

Anchor: a checkout line at a grocery store. One cashier serves customers in some order. The scheduler is the rule that picks who goes next, and the goal is to keep everyone's waiting short while the cashier stays busy.

In this course the "cashier" is the CPU, and the "customers" are processes or threads that are ready to run. The scheduler runs every time the CPU becomes free, or when a running process is interrupted.

## Vocabulary

- **Burst time**: how long a process needs the CPU before it blocks or finishes.
- **Arrival time**: when the process enters the ready queue.
- **Waiting time**: time spent in the ready queue, not running. Waiting time = turnaround time - burst time.
- **Turnaround time**: time from arrival until the process completes.
- **Response time**: time from arrival until the process first gets the CPU.
- **Preemptive**: the scheduler can take the CPU away before the process finishes its burst.
- **Quantum**: the maximum time slice a process gets in round robin.
- **Context switch**: saving one process's state and loading another's. It costs time, and the CPU does no useful work during it.

## Metrics we optimize

1. CPU utilization: keep the CPU busy as much of the time as possible.
2. Throughput: number of processes finished per second.
3. Turnaround time: lower is better for batch jobs.
4. Response time: lower is better for interactive jobs, such as a keyboard handler.
5. Fairness: no process should wait forever.

No algorithm wins on all five. The trade-offs show up in the comparison table below.

## Algorithms

### First-Come, First-Served (FCFS)

- Runs processes in arrival order. No preemption.
- Simple: a FIFO queue is enough.
- Weakness: one long job at the front makes every short job behind it wait. This is the convoy effect.

### Shortest Job First (SJF)

- Picks the ready process with the smallest next burst.
- Non-preemptive SJF gives the lowest possible average waiting time for a fixed set of jobs.
- Problem: the CPU does not know the burst length in advance. Systems estimate it, usually with an exponential average of past bursts.

The lecture's estimate formula, where $t_n$ is the length of the n-th actual burst and $\tau_n$ is the estimate for it:

$$
\tau_{n+1} = \alpha t_n + (1 - \alpha)\tau_n
$$

The lecture uses $\alpha = 0.5$, so recent bursts count as much as the whole past put together.

### Shortest Remaining Time First (SRTF)

- The preemptive version of SJF. A newly arrived job with a shorter remaining time can interrupt the running job.
- Gives a lower average waiting time than SJF, but causes more context switches.

### Round Robin (RR)

- Each process gets one quantum. When the quantum expires, the process goes to the back of the queue.
- Quantum too large: RR becomes FCFS.
- Quantum too small: the CPU spends most of its time on context switches.
- Typical general-purpose systems use a quantum of 10 to 100 ms. The worked example below uses 4 ms so the numbers stay small.

### Priority scheduling

- The highest-priority ready process runs first.
- Risk: starvation. A low-priority job may never run if high-priority jobs keep arriving.
- Fix: aging. Raise a job's priority the longer it waits.

### Multilevel feedback queue (MLFQ)

- Several queues, each with its own quantum. New jobs start in the top queue.
- A job that uses its whole quantum drops one level.
- A job that gives up the CPU early (for example, while it waits for input) stays high. This is how MLFQ favours interactive jobs without being told which jobs they are.

## Worked example 1: FCFS vs SJF

Three processes, all arriving at time 0:

| Process | Burst (ms) |
| --- | --- |
| P1 | 24 |
| P2 | 3 |
| P3 | 3 |

FCFS order is P1, P2, P3.

- P1 waits 0 ms
- P2 waits 24 ms
- P3 waits 27 ms
- Average waiting time: (0 + 24 + 27) / 3 = 17 ms

SJF order is P2, P3, P1.

- P2 waits 0 ms
- P3 waits 3 ms
- P1 waits 6 ms
- Average waiting time: (0 + 3 + 6) / 3 = 3 ms

Same work, same CPU. Only the order changed, and the average dropped from 17 ms to 3 ms.

## Worked example 2: Round Robin with quantum 4 ms

Same three processes, all arriving at time 0, queue order P1, P2, P3.

Timeline:

- 0 to 4: P1 runs (20 ms left)
- 4 to 7: P2 runs and finishes
- 7 to 10: P3 runs and finishes
- 10 to 14, 14 to 18, 18 to 22, 22 to 26: P1 runs (4 ms left at 26)
- 26 to 30: P1 runs and finishes

Results:

| Process | Finish (ms) | Turnaround (ms) | Waiting (ms) | First run (ms) |
| --- | --- | --- | --- | --- |
| P1 | 30 | 30 | 6 | 0 |
| P2 | 7 | 7 | 4 | 4 |
| P3 | 10 | 10 | 7 | 7 |

- Average waiting time: (6 + 4 + 7) / 3 = 5.67 ms
- Average turnaround time: (30 + 7 + 10) / 3 = 15.67 ms

Compare with FCFS. Under FCFS, P2 first runs at 24 ms and P3 at 27 ms. Under RR they first run at 4 ms and 7 ms. RR is worse than SJF on average waiting time (3 ms), but it is much better for response time, and it does not need to know burst lengths in advance.

## Comparison

| Algorithm | Preemptive | Avg wait (example) | Starvation risk | Best for |
| --- | --- | --- | --- | --- |
| FCFS | no | 17 ms | low | simple batch work |
| SJF | no | 3 ms | high for long jobs | batch jobs with known bursts |
| SRTF | yes | 3 ms | high for long jobs | batch jobs, more switches |
| RR (q = 4 ms) | yes | 5.67 ms | none | interactive work |
| Priority | either | depends | high without aging | real-time with aging |
| MLFQ | yes | depends | low with a periodic boost | general-purpose systems |

## Code: average waiting time for FCFS order

```python
def average_waiting(bursts):
    waiting = 0
    total = 0
    for burst in bursts:
        total += waiting
        waiting += burst
    return total / len(bursts)

print(average_waiting([24, 3, 3]))   # 17.0
print(average_waiting([3, 3, 24]))   # 3.0
```

Each process waits for the sum of all bursts before it. The function keeps that running sum, so each process adds its wait to `total`.

## Common mistakes

- Using turnaround time where the question asks for waiting time. Subtract the burst.
- Forgetting that a process that finishes exactly at the end of a quantum does not go back in the queue.
- Thinking SJF is always practical. It is optimal only if the bursts are known, which they usually are not.
- Calling a very large quantum "round robin". With quantum larger than every burst, the behaviour is identical to FCFS.

## Questions to review

- Why does SJF give the lowest average waiting time, and why can't we use it directly?
- What happens to the convoy effect if the quantum is set to 1000 ms?
- How does aging stop starvation in priority scheduling?
- In MLFQ, what happens to a job that uses three full quanta in a row?

## Summary checklist

- [x] Compute waiting and turnaround times for FCFS
- [x] Redo the round robin timeline with quantum 4 ms
- [ ] Explain why round robin with a huge quantum behaves like FCFS
- [ ] Work out where a job ends up in MLFQ after three full quanta

Related: [[Midterm study checklist]], [[Course summary - Operating Systems|course summary]].
