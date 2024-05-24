import sys
from collections import deque

class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining_time = burst
        self.start_time = -1
        self.finish_time = None
        self.response_time = None
        self.wait_time = 0
        self.turnaround_time = 0

    def calculate_metrics(self):
        self.turnaround_time = self.finish_time - self.arrival
        self.wait_time = self.turnaround_time - self.burst
        self.response_time = self.start_time - self.arrival if self.start_time != -1 else 0

    def __repr__(self):
        return f"{self.name}(arrival={self.arrival}, burst={self.burst}, remaining={self.remaining_time})"

def parse_input(file_path):
    processes = []
    time_to_run = 0
    scheduler_type = None
    quantum = None
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: File not found '{file_path}'")
        print("Usage: scheduler-gpt.py <input file>")
        sys.exit(1)
    
    for line in lines:
        parts = line.split()
        if not parts or parts[0].startswith('#'):
            continue
        
        if parts[0] == 'processcount':
            continue
        elif parts[0] == 'runfor':
            time_to_run = int(parts[1])
        elif parts[0] == 'use':
            scheduler_type = parts[1]
        elif parts[0] == 'quantum':
            quantum = int(parts[1])
        elif parts[0] == 'process':
            name = parts[2]
            arrival = int(parts[4])
            burst = int(parts[6])
            processes.append(Process(name, arrival, burst))
        elif parts[0] == 'end':
            break
    
    if scheduler_type == 'rr' and quantum is None:
        print("Error: Missing quantum parameter when use is 'rr'")
        sys.exit(1)
    
    return processes, time_to_run, scheduler_type, quantum

def fifo_scheduler(processes, total_time):
    time = 0
    output = [f"  {len(processes)} processes", "Using First-Come First-Served"]
    queue = deque(sorted(processes, key=lambda x: x.arrival))
    current_process = None

    while time < total_time:
        # Check if there is a process running or if the queue can dispatch one
        if current_process is None or current_process.remaining_time == 0:
            if current_process:
                current_process.finish_time = time
                output.append(f"Time  {time} : {current_process.name} finished")
                current_process = None

            while queue and queue[0].arrival <= time:
                if current_process is None:
                    current_process = queue.popleft()
                    current_process.start_time = time
                    current_process.response_time = time - current_process.arrival
                    output.append(f"Time  {time} : {current_process.name} arrived")
                    output.append(f"Time  {time} : {current_process.name} selected (burst   {current_process.burst})")
                else:
                    proc = queue.popleft()
                    output.append(f"Time  {proc.arrival} : {proc.name} arrived")

        if current_process:
            current_process.remaining_time -= 1

        # Increment time if there's no current process (idle time)
        if current_process is None:
            output.append(f"Time  {time} : Idle")
            time += 1
            continue

        time += 1

    output.append(f"Finished at time  {time}")

    # Calculate metrics for all processes
    for process in list(queue) + ([current_process] if current_process else []):
        if process.finish_time is None:
            process.finish_time = time
        process.calculate_metrics()
        output.append(f"{process.name} wait  {process.wait_time} turnaround  {process.turnaround_time} response  {process.response_time}")

    return output

def round_robin_scheduler(processes, total_time, quantum):
    time = 0
    queue = deque()
    output = [f"  {len(processes)} processes", "Using Round-Robin", f"Quantum   {quantum}"]
    current_process = None
    process_time_remaining = quantum  # Time remaining in the current quantum

    processes.sort(key=lambda x: x.arrival)

    while time < total_time:
        # Enqueue newly arrived processes
        while processes and processes[0].arrival <= time:
            proc = processes.pop(0)
            queue.append(proc)
            output.append(f"Time   {time} : {proc.name} arrived")

        if current_process is None or process_time_remaining == 0:
            if current_process and current_process.remaining_time > 0:
                queue.append(current_process)
            
            if queue:
                current_process = queue.popleft()
                output.append(f"Time   {time} : {current_process.name} selected (burst   {current_process.remaining_time})")
                process_time_remaining = quantum  # Reset quantum

        if current_process:
            # Process the current task
            current_process.remaining_time -= 1
            process_time_remaining -= 1

            if current_process.remaining_time == 0:
                current_process.finish_time = time + 1
                output.append(f"Time   {time + 1} : {current_process.name} finished")
                current_process = None
                process_time_remaining = 0  # Force switch on next cycle if current process finished

        if not current_process and time < total_time - 1:
            output.append(f"Time   {time} : Idle")

        time += 1

    output.append(f"Finished at time  {time}")
    for p in list(queue) + ([current_process] if current_process else []):
        if p.finish_time is None:
            p.finish_time = time
        p.calculate_metrics()
        output.append(f"{p.name} wait   {p.wait_time} turnaround  {p.turnaround_time} response  {p.response_time if p.response_time != -1 else 0}")

    return output

def sjf_scheduler(processes, total_time):
    time = 0
    ready_queue = []
    current_process = None
    output = [f"  {len(processes)} processes", "Using preemptive Shortest Job First"]

    while time < total_time:
        # Add processes to the ready queue as they arrive
        for process in list(processes):
            if process.arrival == time:
                ready_queue.append(process)
                processes.remove(process)
                output.append(f"Time   {time} : {process.name} arrived")

        # Sort ready queue by remaining time, shortest job first
        ready_queue.sort(key=lambda x: (x.remaining_time, x.arrival))

        # Preempt current process if there is a shorter job available
        if ready_queue and (current_process is None or (current_process.remaining_time > 0 and ready_queue[0].remaining_time < current_process.remaining_time)):
            if current_process and current_process.remaining_time > 0:
                ready_queue.append(current_process)
            current_process = ready_queue.pop(0)
            if current_process.start_time == -1:
                current_process.start_time = time
            output.append(f"Time   {time} : {current_process.name} selected (burst   {current_process.remaining_time})")

        # Execute the current process
        if current_process:
            current_process.remaining_time -= 1
            if current_process.remaining_time == 0:
                current_process.finish_time = time + 1
                output.append(f"Time   {time + 1} : {current_process.name} finished")
                current_process = None

        # If no current process and time left, denote idle
        if not current_process and not ready_queue and time < total_time:
            output.append(f"Time   {time} : Idle")

        time += 1

    output.append(f"Finished at time  {total_time}")
    for p in processes + ready_queue + ([current_process] if current_process else []):
        if p.finish_time is None:
            p.finish_time = total_time
        p.calculate_metrics()
        output.append(f"{p.name} wait  {p.wait_time} turnaround  {p.turnaround_time} response  {p.response_time}")

    return output

def main():
    if len(sys.argv) != 2:
        print("Usage: scheduler-gpt.py <input file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = input_file.replace('.in', '.out')
    
    processes, total_time, scheduler_type, quantum = parse_input(input_file)
    
    if scheduler_type == 'fcfs':
        output_lines = fifo_scheduler(processes, total_time)
    elif scheduler_type == 'sjf':
        output_lines = sjf_scheduler(processes, total_time)  # Assume sjf_scheduler is implemented
    elif scheduler_type == 'rr':
        output_lines = round_robin_scheduler(processes, total_time, quantum)
    
    with open(output_file, 'w') as file:
        for line in output_lines:
            file.write(line + '\n')

if __name__ == '__main__':
    main()
