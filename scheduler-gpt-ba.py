import sys
import os

class Process:
    def __init__(self, pid, name, arrival_time, burst_time):
        self.pid = pid
        self.name = name
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.start_time = -1
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.response_time = -1

def parse_input(file_content):
    lines = file_content.strip().split('\n')
    if not lines:
        raise ValueError("Error: Missing input data")

    process_count = 0
    run_for = 0
    algorithm = ''
    quantum = None
    processes = []

    for line in lines:
        parts = line.split()
        if parts[0] == 'processcount':
            process_count = int(parts[1])
        elif parts[0] == 'runfor':
            run_for = int(parts[1])
        elif parts[0] == 'use':
            algorithm = parts[1]
        elif parts[0] == 'quantum':
            if len(parts) < 2:
                raise ValueError("Error: Missing quantum parameter when use is 'rr'")
            quantum = int(parts[1])
        elif parts[0] == 'process':
            if 'name' not in parts or 'arrival' not in parts or 'burst' not in parts:
                raise ValueError("Error: Missing parameter")
            name = parts[2]
            arrival_time = int(parts[4])
            burst_time = int(parts[6])
            pid = len(processes) + 1
            processes.append(Process(pid, name, arrival_time, burst_time))
        elif parts[0] == 'end':
            break

    if process_count != len(processes):
        raise ValueError("Error: Mismatch in process count")

    if algorithm == 'rr' and quantum is None:
        raise ValueError("Error: Missing quantum parameter when use is 'rr'")
    
    return process_count, run_for, algorithm, quantum, processes

def fifo_scheduling(processes, run_for):
    processes.sort(key=lambda x: x.arrival_time)
    current_time = 0
    events = []

    for process in processes:
        if current_time < process.arrival_time:
            for idle_time in range(current_time, process.arrival_time):
                events.append((idle_time, "Idle"))
            current_time = process.arrival_time

        events.append((current_time, f"{process.name} selected (burst {process.burst_time})"))
        process.start_time = current_time
        process.completion_time = current_time + process.burst_time
        process.turnaround_time = process.completion_time - process.arrival_time
        process.waiting_time = process.turnaround_time - process.burst_time
        process.response_time = process.start_time - process.arrival_time
        current_time += process.burst_time
        events.append((current_time, f"{process.name} finished"))

    for idle_time in range(current_time, run_for):
        events.append((idle_time, "Idle"))

    events.append((run_for, "Finished at time"))
    return processes, events

def srtf_scheduling(processes, run_for):
    current_time = 0
    completed = 0
    n = len(processes)
    events = []

    while completed != n:
        idx = -1
        min_remaining_time = float('inf')
        for i in range(n):
            if (processes[i].arrival_time <= current_time and processes[i].remaining_time < min_remaining_time and processes[i].remaining_time > 0):
                min_remaining_time = processes[i].remaining_time
                idx = i

        if idx == -1:
            events.append((current_time, "Idle"))
            current_time += 1
            continue

        process = processes[idx]
        if process.start_time == -1:
            process.start_time = current_time
        if process.response_time == -1:
            process.response_time = current_time - process.arrival_time

        if process.remaining_time == process.burst_time:
            events.append((current_time, f"{process.name} selected (burst {process.remaining_time})"))

        process.remaining_time -= 1
        current_time += 1

        if process.remaining_time == 0:
            process.completion_time = current_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
            events.append((current_time, f"{process.name} finished"))
            completed += 1

    for idle_time in range(current_time, run_for):
        events.append((idle_time, "Idle"))

    events.append((run_for, "Finished at time"))
    return processes, events

def round_robin_scheduling(processes, quantum, run_for):
    from collections import deque

    current_time = 0
    queue = deque()
    events = []
    arrivals_logged = set()

    processes.sort(key=lambda x: x.arrival_time)
    next_process_idx = 0
    n = len(processes)
    completed = 0

    while current_time < run_for:
        while next_process_idx < n and processes[next_process_idx].arrival_time <= current_time:
            if processes[next_process_idx].arrival_time not in arrivals_logged:
                events.append((current_time, f"{processes[next_process_idx].name} arrived"))
                arrivals_logged.add(processes[next_process_idx].arrival_time)
            queue.append(processes[next_process_idx])
            next_process_idx += 1

        if not queue:
            events.append((current_time, "Idle"))
            current_time += 1
            continue

        process = queue.popleft()

        if process.start_time == -1:
            process.start_time = current_time
        if process.response_time == -1:
            process.response_time = current_time - process.arrival_time

        events.append((current_time, f"{process.name} selected (burst {process.remaining_time})"))

        exec_time = min(quantum, process.remaining_time)
        process.remaining_time -= exec_time
        current_time += exec_time

        while next_process_idx < n and processes[next_process_idx].arrival_time <= current_time:
            if processes[next_process_idx].arrival_time not in arrivals_logged:
                events.append((current_time, f"{processes[next_process_idx].name} arrived"))
                arrivals_logged.add(processes[next_process_idx].arrival_time)
            queue.append(processes[next_process_idx])
            next_process_idx += 1

        if process.remaining_time > 0:
            queue.append(process)
        else:
            process.completion_time = current_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
            events.append((current_time, f"{process.name} finished"))
            completed += 1

        if completed == n:
            break

    for idle_time in range(current_time, run_for):
        events.append((idle_time, "Idle"))

    events.append((run_for, "Finished at time"))
    return processes, events

def calculate_metrics(processes):
    for p in processes:
        p.turnaround_time = p.completion_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
        if p.response_time == -1:
            p.response_time = p.start_time - p.arrival_time
    return processes

def main():
    if len(sys.argv) < 2:
        print("Usage: scheduler-get.py <input file>")
        return

    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r') as file:
            file_content = file.read()
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        return
    
    try:
        process_count, run_for, algorithm, quantum, processes = parse_input(file_content)
    except ValueError as e:
        print(e)
        return

    if algorithm == 'fcfs':
        scheduled_processes, events = fifo_scheduling(processes, run_for)
    elif algorithm == 'sjf':
        scheduled_processes, events = srtf_scheduling(processes, run_for)
    elif algorithm == 'rr':
        scheduled_processes, events = round_robin_scheduling(processes, quantum, run_for)
    else:
        print("Error: Unknown scheduling algorithm specified.")
        return

    scheduled_processes = calculate_metrics(scheduled_processes)

    # Create the output filename with the .out extension
    base_filename = os.path.splitext(input_file)[0]
    output_filename = base_filename + ".out"

    with open(output_filename, "w") as f:
        f.write(f"{process_count} processes\n")
        f.write(f"Using {algorithm.upper() if algorithm != 'rr' else 'Round-Robin'}\n")
        if algorithm == 'rr':
            f.write(f"Quantum {quantum}\n")

        # Track arrivals
        arrivals = {p.arrival_time: p.name for p in processes}
        
        for time, event in events:
            if time in arrivals and "arrived" not in event:
                f.write(f"Time {time:4} : {arrivals[time]} arrived\n")
            f.write(f"Time {time:4} : {event}\n")

        for p in scheduled_processes:
            f.write(f"{p.name} wait {p.waiting_time:4} turnaround {p.turnaround_time:4} response {p.response_time:4}\n")

        unfinished_processes = [p for p in processes if p.remaining_time > 0]
        if unfinished_processes:
            for p in unfinished_processes:
                f.write(f"{p.name} did not finish\n")

if __name__ == "__main__":
    main()
