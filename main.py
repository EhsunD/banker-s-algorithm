import threading
import time
import random

class Process:
    def __init__(self, id, max_resources, allocated_resources):
        self.id = id
        self.max_resources = max_resources
        self.allocated_resources = allocated_resources
        self.need = [max_resources[i] - allocated_resources[i] for i in range(len(max_resources))]

class Resource:
    def __init__(self, total_resources):
        self.total_resources = total_resources
        self.available_resources = total_resources[:]

class DynamicResource(Resource):
    def __init__(self, total_resources):
        super().__init__(total_resources)

    def add_resources(self, additional_resources):
        for i in range(len(self.total_resources)):
            self.total_resources[i] += additional_resources[i]
            self.available_resources[i] += additional_resources[i]

def is_safe_state(processes, available_resources):
    work = available_resources[:]
    finish = [False] * len(processes)
    safe_sequence = []

    while True:
        found = False
        for i in range(len(processes)):
            if not finish[i] and all(need <= work for need, work in zip(processes[i].need, work)):
                work = [work[j] + processes[i].allocated_resources[j] for j in range(len(work))]
                finish[i] = True
                safe_sequence.append(i)
                found = True
                break

        if not found:
            break

    return all(finish), safe_sequence

def request_resources(process, request, processes, resources):
    if all(request[i] <= process.need[i] for i in range(len(request))):
        if all(request[i] <= resources.available_resources[i] for i in range(len(request))):
            for i in range(len(request)):
                resources.available_resources[i] -= request[i]
                process.allocated_resources[i] += request[i]
                process.need[i] -= request[i]

            safe, safe_sequence = is_safe_state(processes, resources.available_resources)

            if safe:
                print(f"Process {process.id} request granted. Safe sequence: {safe_sequence}")
            else:
                for i in range(len(request)):
                    resources.available_resources[i] += request[i]
                    process.allocated_resources[i] -= request[i]
                    process.need[i] += request[i]
                print(f"Process {process.id} request denied. System would be in an unsafe state.")
        else:
            print(f"Process {process.id} request denied. Not enough available resources.")
    else:
        print(f"Process {process.id} request denied. Request exceeds maximum need.")

def process_thread(process, request, processes, resources):
    print(f"Process {process.id} requests resources: {request}")
    request_resources(process, request, processes, resources)
    display_state(processes, resources)

def race_condition_monitor(processes, resources):
    while True:
        time.sleep(2)
        race_detected = False
        for process in processes:
            if sum(process.allocated_resources) > sum(process.max_resources):
                race_detected = True
                print(f"Race condition detected for Process {process.id}.")
                break
        if not race_detected:
            print("No race conditions detected.")

def display_state(processes, resources):
    print("Available Resources:", resources.available_resources)
    print("Processes:")
    for process in processes:
        print(f"Process {process.id}: Max: {process.max_resources}, Allocated: {process.allocated_resources}, Need: {process.need}")
    print()

def dynamic_resource_changer(resource, interval):
    while True:
        time.sleep(interval)
        additional_resources = [random.randint(0, 2) for _ in range(len(resource.total_resources))]
        resource.add_resources(additional_resources)
        print(f"Resources added: {additional_resources}")
        print(f"New total resources: {resource.total_resources}")
        print(f"New available resources: {resource.available_resources}")
        print()

def simulate_parallel_requests(requests, processes, resources):
    for process, request in requests:
        thread = threading.Thread(target=process_thread, args=(process, request, processes, resources))
        thread.start()
        thread.join()

if __name__ == "__main__":
    total_resources = [10, 5, 7]
    resources = Resource(total_resources)
    processes = [
        Process(0, [7, 5, 3], [0, 1, 0]),
        Process(1, [3, 2, 2], [2, 0, 0]),
        Process(2, [9, 0, 2], [3, 0, 2]),
        Process(3, [2, 2, 2], [2, 1, 1]),
        Process(4, [4, 3, 3], [0, 0, 2])
    ]

    print("Initial State:")
    display_state(processes, resources)

    dynamic_resource = DynamicResource(total_resources)
    race_condition_thread = threading.Thread(target=race_condition_monitor, args=(processes, resources))
    resource_change_thread = threading.Thread(target=dynamic_resource_changer, args=(dynamic_resource, 5))

    race_condition_thread.start()
    resource_change_thread.start()

    requests = [
        (processes[0], [0, 2, 0]),
        (processes[4], [0, 3, 0]),
        (processes[1], [1, 0, 2]),
        (processes[3], [0, 1, 0])
    ]

    simulate_parallel_requests(requests, processes, resources)

    race_condition_thread.join()
    resource_change_thread.join()
