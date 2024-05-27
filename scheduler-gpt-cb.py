import sys

class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.start_time = -1
        self.finish_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = -1

def parse_input(filename):
    processes = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        
    process_count = int(lines[0].split()[1])
    run_for = int(lines[1].split()[1])
    use_algorithm = lines[2].split()[1]
    
    quantum = None
    if use_algorithm == 'rr':
        if len(lines[3].split()) < 2:
            print("Error: Missing quantum parameter when use is 'rr'")
            sys.exit(1)
        quantum = int(lines[3].split()[1])
        process_lines_start = 4
    else:
        process_lines_start = 3
    
    for i in range(process_lines_start, process_lines_start + process_count):
        parts = lines[i].split()
        name = parts[2]
        arrival = int(parts[4])
        burst = int(parts[6])
        processes.append(Process(name, arrival, burst))
    
    return processes, run_for, use_algorithm, quantum

def fcfs_scheduler(processes, run_for):
    current_time = 0
    completed_processes = []
    while current_time < run_for and processes:
        for process in sorted(processes, key=lambda x: x.arrival):
            if process.arrival <= current_time:
                process.start_time = current_time
                current_time += process.burst
                process.finish_time = current_time
                process.turnaround_time = process.finish_time - process.arrival
                process.waiting_time = process.start_time - process.arrival
                process.response_time = process.start_time - process.arrival
                completed_processes.append(process)
                processes.remove(process)
                break
        else:
            current_time += 1  # If no process is ready, increment time
            
    return completed_processes, current_time

def sjf_scheduler(processes, run_for):
    current_time = 0
    completed_processes = []
    while current_time < run_for and processes:
        ready_queue = [p for p in processes if p.arrival <= current_time]
        if ready_queue:
            process = min(ready_queue, key=lambda p: p.burst)
            if process.start_time == -1:
                process.start_time = current_time
            current_time += process.burst
            process.finish_time = current_time
            process.turnaround_time = process.finish_time - process.arrival
            process.waiting_time = process.start_time - process.arrival
            process.response_time = process.start_time - process.arrival
            completed_processes.append(process)
            processes.remove(process)
        else:
            current_time += 1  # If no process is ready, increment time
            
    return completed_processes, current_time

def rr_scheduler(processes, run_for, quantum):
    current_time = 0
    completed_processes = []
    queue = []
    
    timeline = []

    while current_time < run_for and (processes or queue):
        ready_queue = [p for p in processes if p.arrival <= current_time]
        for process in ready_queue:
            if process not in queue:
                queue.append(process)
            processes.remove(process)
        
        if queue:
            process = queue.pop(0)
            if process.start_time == -1:
                process.start_time = current_time
            if process.response_time == -1:
                process.response_time = current_time - process.arrival
            time_slice = min(quantum, process.remaining)
            process.remaining -= time_slice
            timeline.append(f"Time {current_time}: {process.name} selected (burst {process.remaining + time_slice})")
            current_time += time_slice
            
            if process.remaining == 0:
                process.finish_time = current_time
                process.turnaround_time = process.finish_time - process.arrival
                process.waiting_time = process.turnaround_time - process.burst
                completed_processes.append(process)
            else:
                queue.append(process)
        else:
            timeline.append(f"Time {current_time}: Idle")
            current_time += 1  # If no process is ready, increment time

    # Ensure final time accounts for total run duration, even if idle
    if current_time < run_for:
        timeline.append(f"Finished at time {run_for}")
    else:
        timeline.append(f"Finished at time {current_time}")

    return completed_processes, current_time, timeline

def print_results(processes, algorithm, quantum, run_for, final_time, timeline):
    output = []
    output.append(f"{len(processes)} processes")
    output.append(f"Using {algorithm.upper()}")
    if algorithm == 'rr':
        output.append(f"Quantum {quantum}")
    
    output.extend(timeline)
    
    output.append(f"Finished at time {final_time}")
    sorted_processes = sorted(processes, key=lambda p: p.name)
    for process in sorted_processes:
        if process.finish_time <= run_for:
            output.append(f"{process.name} wait {process.waiting_time} turnaround {process.turnaround_time} response {process.response_time}")
        else:
            output.append(f"{process.name} did not finish")
    
    return "\n".join(output)

def main():
    if len(sys.argv) != 2:
        print("Usage: scheduler-gpt.py <input file>")
        sys.exit(1)
        
    filename = sys.argv[1]
    if not filename.endswith('.in'):
        print("Error: Input file must have extension .in")
        sys.exit(1)
        
    processes, run_for, use_algorithm, quantum = parse_input(filename)
    
    if use_algorithm == 'fcfs':
        completed_processes, final_time = fcfs_scheduler(processes, run_for)
        timeline = []
    elif use_algorithm == 'sjf':
        completed_processes, final_time = sjf_scheduler(processes, run_for)
        timeline = []
    elif use_algorithm == 'rr':
        if quantum is None:
            print("Error: Missing quantum parameter when use is 'rr'")
            sys.exit(1)
        completed_processes, final_time, timeline = rr_scheduler(processes, run_for, quantum)
    else:
        print(f"Error: Invalid scheduling algorithm '{use_algorithm}'")
        sys.exit(1)
    
    output_filename = filename.replace('.in', '.out')
    with open(output_filename, 'w') as file:
        result = print_results(completed_processes, use_algorithm, quantum, run_for, final_time, timeline)
        file.write(result)

if __name__ == "__main__":
    main()
