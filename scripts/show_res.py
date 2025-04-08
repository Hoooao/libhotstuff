import os
import re
import subprocess
import matplotlib.pyplot as plt

def find_cli_folders(base_dir):
    """Find all folders ending with `_cli` in the given directory."""
    cli_folders = []
    for root, dirs, _ in os.walk(base_dir):
        for d in dirs:
            if d.endswith("_cli") and d.startswith("ben_4rep2cli_1000blk"): #and d.contains("async"):
                cli_folders.append(os.path.join(root, d))
    return cli_folders

def extract_data_from_cat(folder_path):
    """Run `cat` on all files in the folder and extract relevant data."""
    results = []
    pattern_array = re.compile(r"\[(.*?)\]")  # Match [<array of numbers>]
    pattern_latency = re.compile(r"lat = (\d+\.?\d*)ms")  # Match lat = <latency>ms
    pattern_filename = re.compile(r"4rep2cli_\d+blk_4_4_8_1550async_tls_cli")  # Match <number>_cli
    try:
        # Run `cat` to read file contents
        output = subprocess.check_output([f"cat {folder_path}/remote/*/log/stderr | python ./thr_hist.py"],shell=True, text=True)
        # Extract data
        arrays = pattern_array.findall(output)
        latencies = pattern_latency.findall(output)

        for array, latency in zip(arrays, latencies):
            results.append({"array": array, "latency": float(latency)})

    except subprocess.CalledProcessError as e:
        print(f"Error reading file {folder_path}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return results

def get_thruput_per_sec():
    base_dir = "./deploy"  
    cli_folders = find_cli_folders(base_dir)

    all_data = {}
    for folder in cli_folders:
        print(f"Processing folder: {folder}")
        folder_data = extract_data_from_cat(folder)
        all_data[folder] = folder_data

    # Print or process the extracted data
    for folder, data in all_data.items():
        print(f"\nFolder: {folder}")
        for entry in data:
            print(f"Array: {entry['array']}, Latency: {entry['latency']}ms")

def parse_results(data):
    """
    Parse the stored results to extract Batch Sizes, Peak Thru, and Latency.
    
    :param data: List of result strings in the specified format.
    :return: Three lists: x_values, max_array_values, latencies.
    """
    x_values = []
    max_array_values = []
    latencies = []
    
    folder_pattern = re.compile(r"4rep2cli_(\d+)blk_")  # Extract the number in folder name
    array_pattern = re.compile(r"Array: \[(.*?)\]")  # Extract numbers in Array
    latency_pattern = re.compile(r"Latency: ([\d.]+)ms")  # Extract Latency value
    f = 0
    a = []
    l= 0
    parsed_data = []
    for entry in data:
        folder_match = folder_pattern.search(entry)
        array_match = array_pattern.search(entry)
        latency_match = latency_pattern.search(entry)
        
        if folder_match:
            # Extract x-value
            f=int(folder_match.group(1))
        if array_match:
            # Extract max from Array
            a = max(list(map(int, array_match.group(1).split(','))))
        if latency_match:
            # Extract Latency
            l = float(latency_match.group(1))
            parsed_data.append((f, a, l))
    parsed_data.sort(key=lambda x: x[0])
    x_values, max_array_values, latencies = zip(*parsed_data)
    return list(x_values), list(max_array_values), list(latencies)

def parse_results_for_inflight_stat(data):
    """
    Parse the stored results to extract Batch Sizes, Peak Thru, and Latency.
    
    :param data: List of result strings in the specified format.
    :return: Three lists: x_values, y_values, latencies.
    """
    x_values = []
    y_values = []
    
    folder_pattern = re.compile(r"ben_4rep2cli_200blk_4_4_8_(\d+)a_tls_cli")  # Extract the number in folder name
    array_pattern = re.compile(r"Array: \[(.*?)\]")  # Extract numbers in Array
    latency_pattern = re.compile(r"Latency: ([\d.]+)ms")  # Extract Latency value
    f = 0
    a = []
    l= 0
    parsed_data = []
    for entry in data:
        folder_match = folder_pattern.search(entry)
        array_match = array_pattern.search(entry)
        latency_match = latency_pattern.search(entry)
        
        if folder_match:
            # Extract x-value
            f=int(folder_match.group(1))
        if array_match:
            # Extract max from Array
            a = max(list(map(int, array_match.group(1).split(','))))
        if latency_match:
            # Extract Latency
            l = float(latency_match.group(1))
            parsed_data.append((f, l))
    parsed_data.sort(key=lambda x: x[0])
    print(parsed_data)
    x_values, y_values = zip(*parsed_data)
    return list(x_values), list(y_values)


def plot_results(x_values, max_array_values, latencies):
    """
    Plot two figures: one with max_array_values and one with latencies.
    
    :param x_values: List of x-axis values (numbers from folder names).
    :param max_array_values: List of maximum values from Arrays.
    :param latencies: List of Latency values.
    """
    # Plot Peak Thru
    plt.figure()
    plt.plot(x_values, max_array_values, marker='o')
    plt.title("Peak Thru vs Batch Size")
    plt.xlabel("Batch Size")
    plt.ylabel("Peak Thru")
    plt.grid(True)
    plt.savefig("res_thru.png", dpi=300)

    # Plot Latency
    plt.figure()
    plt.plot(x_values, latencies, marker='o', color='orange')
    plt.title("Latency vs Batch Size")
    plt.xlabel("Batch Size")
    plt.ylabel("Latency (ms)")
    plt.grid(True)
    plt.savefig("res_lat.png", dpi=300)

def plot_inp_vs_lat(x_values, y_values):
    plt.figure()
    plt.plot(x_values, y_values, marker='o')
    plt.title("Latency vs Req in-flight (blk_size=200)")
    plt.xlabel("Req in-flight")
    plt.ylabel("Latency")
    plt.grid(True)
    plt.savefig("res_in-flt_200.png", dpi=300)

def main():
    with open("infloght_num_200blk_size_res.txt", "r") as f:
        stored_results = f.readlines()
    # Parse the results
    x_values, y_values = parse_results_for_inflight_stat(stored_results)

    # Plot the results
    plot_inp_vs_lat(x_values, y_values)

if __name__ == "__main__":
   main()

# get_thruput_per_sec()
