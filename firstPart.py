import threading

class Resource:
    def __init__(self, total_resources):
        self.total_resources = total_resources
        self.available_resources = total_resources[:]
        self.lock = threading.Lock()

    def state_safe_is(self, processes):
        work = self.available_resources[:]
        finish = [False] * len(processes)
        safe_sequence = []

        while True:
            found = False
            for i, process in enumerate(processes):
                if not finish[i] and all(need <= work for need, work in zip(process.need, work)):
                    work = [work[j] + process.allocated[j] for j in range(len(self.total_resources))]
                    finish[i] = True
                    safe_sequence.append(process.id)
                    found = True

            if not found:
                break

        return all(finish), safe_sequence

    def request_resources(self, process, request, processes):
        # Temporary allocation
        temp_allocated = [process.allocated[i] + request[i] for i in range(len(self.total_resources))]
        temp_need = [process.max_resources[i] - temp_allocated[i] for i in range(len(self.total_resources))]

        # Check if request can be granted
        if all(temp_need[i] >= 0 for i in range(len(self.total_resources))):
            # Try to allocate resources
            with self.lock:
                # Temporarily allocate resources
                for i in range(len(self.total_resources)):
                    self.available_resources[i] -= request[i]
                    process.allocated[i] += request[i]

                # Check for safety
                safe, _ = self.state_safe_is(processes)

                if safe:
                    return True
                else:
                    # Rollback allocation
                    for i in range(len(self.total_resources)):
                        self.available_resources[i] += request[i]
                        process.allocated[i] -= request[i]

                    return False
        else:
            return False

    def release_resources(self, process, release):
        with self.lock:
            for i in range(len(self.total_resources)):
                self.available_resources[i] += release[i]
                process.allocated[i] -= release[i]


class Process:
    def __init__(self, id, max_resources, allocated_resources):
        self.id = id
        self.max_resources = max_resources
        self.allocated = allocated_resources
        self.need = [max_resources[i] - allocated_resources[i] for i in range(len(max_resources))]
        self.lock = threading.Lock()


def display_state(processes, available_resources):
    print("Available Resources:", available_resources)
    print("Processes:")
    for process in processes:
        print(f"Process {process.id}: Max: {process.max_resources}, Allocated: {process.allocated}, Need: {process.need}")


def process_thread(process, request, processes, resources):
    if resources.request_resources(process, request, processes):
        print(f"Process {process.id} request granted. Safe sequence:", end=" ")
        _, safe_sequence = resources.state_safe_is(processes)
        print(safe_sequence)
    else:
        print(f"Process {process.id} request denied. System would be in an unsafe state.")


def race_condition_monitor(processes, resources):
    while True:
        for process in processes:
            with process.lock:
                total_allocated = sum(process.allocated)
                if total_allocated > sum(process.max_resources):
                    print(f"Race condition detected in Process {process.id}. Total allocated ({total_allocated}) exceeds max resources ({sum(process.max_resources)})")
                    return


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

    display_state(processes, resources.available_resources)

    monitor_thread = threading.Thread(target=race_condition_monitor, args=(processes, resources))
    monitor_thread.start()

    while True:
        try:
            process_id = int(input("Enter process ID to request resources: "))
            request = list(map(int, input("Enter resource request (space-separated): ").split()))
            if process_id < 0 or process_id >= len(processes):
                raise ValueError("Invalid process ID")

            process = processes[process_id]
            request_thread = threading.Thread(target=process_thread, args=(process, request, processes, resources))
            request_thread.start()
            request_thread.join()

            display_state(processes, resources.available_resources)

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected. Exiting.")
            break
        except Exception as e:
            print(f"Error: {e}")
