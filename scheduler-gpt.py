import sys
from collections import deque

class Process:
    def __init__(self, name, arrival_time, burst_time):
        self.name = name
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.start_time = -1
        self.finish_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = -1

def parse_input(filename):
    processes = []
    algorithm = None
    process_count = None
    run_for = None
    quantum = None
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split()
            if parts[0] == 'process':
                if len(parts) < 7:
                    print("Error: Invalid process line in input file.")
                    return None, None, None, None, None
                name = parts[2]
                arrival_time = int(parts[4])
                burst_time = int(parts[6])
                processes.append(Process(name, arrival_time, burst_time))
            elif parts[0] == 'use':
                algorithm = parts[1]
            elif parts[0] == 'processcount':
                process_count = int(parts[1])
            elif parts[0] == 'runfor':
                run_for = int(parts[1])
            elif parts[0] == 'quantum':
                quantum = int(parts[1])
            elif parts[0] == 'end':
                break
    if algorithm is None or process_count is None or run_for is None or not processes:
        print("Error: Missing or incomplete information in input file.")
        return None, None, None, None, None
    if algorithm == 'rr' and quantum is None:
        print("Error: Missing quantum parameter when use is 'rr'")
        return None, None, None, None, None
    return algorithm, process_count, run_for, quantum, processes

def run_fcfs(processes, run_for):
    current_time = 0
    log = []
    processes.sort(key=lambda x: x.arrival_time)

    for process in processes:
        if current_time < process.arrival_time:
            while current_time < process.arrival_time:
                log.append(f"Time {current_time} : Idle")
                current_time += 1
        process.start_time = current_time
        process.response_time = current_time - process.arrival_time
        log.append(f"Time {current_time} : {process.name} selected (burst {process.burst_time})")
        current_time += process.burst_time
        process.finish_time = current_time
        log.append(f"Time {current_time} : {process.name} finished")

    while current_time < run_for:
        log.append(f"Time {current_time} : Idle")
        current_time += 1

    return processes, log

def run_rr(processes, run_for, quantum):
    current_time = 0
    log = []
    ready_queue = deque()
    processes.sort(key=lambda x: x.arrival_time)
    next_process_index = 0

    while current_time < run_for:
        while next_process_index < len(processes) and processes[next_process_index].arrival_time <= current_time:
            ready_queue.append(processes[next_process_index])
            log.append(f"Time {current_time} : {processes[next_process_index].name} arrived")
            next_process_index += 1

        if ready_queue:
            current_process = ready_queue.popleft()
            if current_process.start_time == -1:
                current_process.start_time = current_time
                current_process.response_time = current_time - current_process.arrival_time

            execute_time = min(quantum, current_process.remaining_time)
            log.append(f"Time {current_time} : {current_process.name} selected (burst {current_process.remaining_time})")
            current_time += execute_time
            current_process.remaining_time -= execute_time

            while next_process_index < len(processes) and processes[next_process_index].arrival_time <= current_time:
                ready_queue.append(processes[next_process_index])
                log.append(f"Time {current_time} : {processes[next_process_index].name} arrived")
                next_process_index += 1

            if current_process.remaining_time > 0:
                ready_queue.append(current_process)
            else:
                current_process.finish_time = current_time
                log.append(f"Time {current_time} : {current_process.name} finished")
        else:
            log.append(f"Time {current_time} : Idle")
            current_time += 1

    return processes, log

def run_sjf(processes, run_for):
    current_time = 0
    log = []
    ready_queue = []
    processes.sort(key=lambda x: x.arrival_time)
    next_process_index = 0

    while current_time < run_for:
        while next_process_index < len(processes) and processes[next_process_index].arrival_time <= current_time:
            ready_queue.append(processes[next_process_index])
            log.append(f"Time {current_time} : {processes[next_process_index].name} arrived")
            next_process_index += 1

        ready_queue.sort(key=lambda x: (x.remaining_time, x.arrival_time))

        if ready_queue:
            current_process = ready_queue.pop(0)
            if current_process.start_time == -1:
                current_process.start_time = current_time
                current_process.response_time = current_time - current_process.arrival_time

            log.append(f"Time {current_time} : {current_process.name} selected (burst {current_process.remaining_time})")
            current_time += 1
            current_process.remaining_time -= 1

            if current_process.remaining_time == 0:
                current_process.finish_time = current_time
                log.append(f"Time {current_time} : {current_process.name} finished")
            else:
                ready_queue.append(current_process)
        else:
            log.append(f"Time {current_time} : Idle")
            current_time += 1

    return processes, log

def calculate_metrics(processes):
    for process in processes:
        process.turnaround_time = process.finish_time - process.arrival_time
        process.waiting_time = process.turnaround_time - process.burst_time

def generate_output(filename, algorithm, run_for, quantum, processes, log):
    processes.sort(key=lambda x: x.name)  # Ensure processes are listed in the original order
    with open(filename, 'w') as f:
        f.write(f"{len(processes)} processes\n")
        f.write(f"Using {algorithm.upper()}\n")
        if algorithm == 'rr':
            f.write(f"Quantum {quantum}\n")
        for entry in log:
            f.write(entry + '\n')
        f.write(f"Finished at time {run_for}\n")
        for process in processes:
            if process.finish_time == -1:
                f.write(f"{process.name} did not finish\n")
            else:
                f.write(f"{process.name} wait {process.waiting_time} turnaround {process.turnaround_time} response {process.response_time}\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: python scheduler-gpt.py inputFile.in")
        sys.exit(1)

    input_filename = sys.argv[1]
    output_filename = input_filename.replace('.in', '.out')

    algorithm, process_count, run_for, quantum, processes = parse_input(input_filename)
    if algorithm == 'fcfs':
        processes, log = run_fcfs(processes, run_for)
    elif algorithm == 'rr':
        if quantum is None:
            print("Error: Quantum time missing for Round Robin scheduling.")
            sys.exit(1)
        processes, log = run_rr(processes, run_for, quantum)
    elif algorithm == 'sjf':
        processes, log = run_sjf(processes, run_for)
    else:
        print("Unsupported algorithm.")
        sys.exit(1)

    calculate_metrics(processes)
    generate_output(output_filename, algorithm, run_for, quantum, processes, log)

if __name__ == "__main__":
    main()
