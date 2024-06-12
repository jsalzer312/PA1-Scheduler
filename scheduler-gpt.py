# Brayden Antonelli
# Christopher Bowerfind
# James Salzer
# Jonathan Connor
import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from collections import deque

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
    arrivals_logged = set()
    ready_queue = []
    
    while current_time < run_for:
        # Check for new arrivals and add them to the ready queue
        for process in processes:
            if process.arrival_time == current_time and process.pid not in arrivals_logged:
                arrivals_logged.add(process.pid)
                ready_queue.append(process)
                events.append((current_time, f"{process.name} arrived"))

        # Process selection
        if ready_queue:
            process = ready_queue.pop(0)
            events.append((current_time, f"{process.name} selected (burst {process.burst_time})"))
            
            process.start_time = current_time
            process.completion_time = current_time + process.burst_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
            process.response_time = process.start_time - process.arrival_time
            process.remaining_time = 0  # Process is completed
            
            # Move current time forward to the end of the process burst time
            end_time = current_time + process.burst_time
            while current_time < end_time:
                # Log arrivals that happen during the burst time
                for proc in processes:
                    if proc.arrival_time == current_time and proc.pid not in arrivals_logged:
                        arrivals_logged.add(proc.pid)
                        ready_queue.append(proc)
                        events.append((current_time, f"{proc.name} arrived"))
                
                current_time += 1
            
            events.append((current_time, f"{process.name} finished"))
        else:
            # Handle idle time
            events.append((current_time, "Idle"))
            current_time += 1
    
    # Log the final event
    events.append((run_for, f"Finished"))
    
    return processes, events




def srtf_scheduling(processes, run_for):
    current_time = 0
    completed = 0
    n = len(processes)
    events = []
    arrivals_logged = set()
    ready_queue = []
    last_selected_process = None

    while completed != n:
        # Check for new arrivals and add them to the ready queue
        new_arrivals = []
        for process in processes:
            if process.arrival_time == current_time and process.pid not in arrivals_logged:
                arrivals_logged.add(process.pid)
                new_arrivals.append(process)
                ready_queue.append(process)
                events.append((current_time, f"{process.name} arrived"))

        # Sort the ready queue by remaining time, then by arrival time
        ready_queue.sort(key=lambda x: (x.remaining_time, x.arrival_time))

        if ready_queue:
            process = ready_queue.pop(0)
            if process.start_time == -1:
                process.start_time = current_time
                process.response_time = current_time - process.arrival_time

            if process != last_selected_process or process.remaining_time == process.burst_time:
                events.append((current_time, f"{process.name} selected (burst {process.remaining_time})"))

            exec_time = 1
            current_time += exec_time
            process.remaining_time -= exec_time
            last_selected_process = process

            # Check for new arrivals during execution
            for p in processes:
                if current_time == p.arrival_time and p.pid not in arrivals_logged:
                    arrivals_logged.add(p.pid)
                    ready_queue.append(p)
                    events.append((current_time, f"{p.name} arrived"))

            if process.remaining_time == 0:
                process.completion_time = current_time
                process.turnaround_time = process.completion_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time
                events.append((current_time, f"{process.name} finished"))
                completed += 1
            else:
                ready_queue.append(process)
        else:
            events.append((current_time, "Idle"))
            current_time += 1
            last_selected_process = None

    for idle_time in range(current_time, run_for):
        events.append((idle_time, "Idle"))

    events.append((run_for, f"Finished"))
    return processes, events

def round_robin_scheduling(processes, quantum, run_for):
    current_time = 0
    queue = deque()
    events = []
    arrivals_logged = set()
    next_process_idx = 0
    n = len(processes)
    completed = 0

    processes.sort(key=lambda x: x.arrival_time)

    while current_time < run_for:
        # Check for new arrivals and add them to the queue
        while next_process_idx < n and processes[next_process_idx].arrival_time <= current_time:
            if processes[next_process_idx].pid not in arrivals_logged:
                events.append((processes[next_process_idx].arrival_time, f"{processes[next_process_idx].name} arrived"))
                arrivals_logged.add(processes[next_process_idx].pid)
            queue.append(processes[next_process_idx])
            next_process_idx += 1

        if not queue:
            events.append((current_time, "Idle"))
            current_time += 1
            continue

        # Select the next process from the queue
        process = queue.popleft()

        if process.start_time == -1:
            process.start_time = current_time
            process.response_time = current_time - process.arrival_time

        # Execute the process for the quantum time
        exec_time = min(quantum, process.remaining_time)
        events.append((current_time, f"{process.name} selected (burst {process.remaining_time})"))
        current_time += exec_time
        process.remaining_time -= exec_time

        # Check for new arrivals during the execution
        while next_process_idx < n and processes[next_process_idx].arrival_time <= current_time:
            if processes[next_process_idx].pid not in arrivals_logged:
                events.append((processes[next_process_idx].arrival_time, f"{processes[next_process_idx].name} arrived"))
                arrivals_logged.add(processes[next_process_idx].pid)
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

    events.append((run_for, f"Finished"))
    return processes, events

def calculate_metrics(processes):
    for p in processes:
        p.turnaround_time = p.completion_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
        if p.response_time == -1:
            p.response_time = p.start_time - p.arrival_time
    return processes

def display_results(processes, events, algorithm, quantum=None):
    root = tk.Tk()
    root.title("Scheduling Results")

    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    summary_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=80, height=40)
    summary_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Header information
    summary_text.insert(tk.END, f"{len(processes)} processes\n")
    if(algorithm == "rr"):
        algorithm = "Round Robin"
    if(algorithm=="fcfs"):
        algorithm = "First-Come First-Served"
    if(algorithm=="sjf"):
        algorithm="Shortest Job First"

    summary_text.insert(tk.END, f"Using {algorithm}\n")
    if algorithm == 'Round Robin':
        summary_text.insert(tk.END, f"Quantum {quantum}\n")
        summary_text.insert(tk.END, "\n")
    

    # Events
    for time, event in events:
        summary_text.insert(tk.END, f"Time {time:4} : {event}\n")

    summary_text.insert(tk.END, "\nMetrics\n")
    # Metrics
    for process in sorted(processes, key=lambda x: x.pid):
        summary_text.insert(tk.END, f"{process.name} wait {process.waiting_time:4} turnaround {process.turnaround_time:4} response {process.response_time:4}\n")

    root.mainloop()

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

    display_results(scheduled_processes, events, algorithm, quantum)

if __name__ == "__main__":
    main()
