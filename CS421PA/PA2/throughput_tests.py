import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np

# Sabit dosya boyutu (bit cinsinden)
FILE_SIZE_BITS = 4266854 * 8

def run_test(dmax, timeout, window_size, loss_rate):
    # Receiver ve sender komutlarını göster
    receiver_cmd = f"python SR_receiver.py 5000 {window_size} {loss_rate} {dmax}"
    print(f"\nStarting receiver with command: {receiver_cmd}")
    sender_cmd = f"python SR_sender.py image.png 5000 {window_size} {timeout}"
    print(f"Starting sender with command: {sender_cmd}")

    # Kullanıcıdan süre bilgisini al
    time_elapsed = float(input("Enter the time elapsed (in seconds) shown by receiver: "))

    # Throughput hesapla ve Mbps cinsine çevir
    throughput = (FILE_SIZE_BITS / time_elapsed) / 1_000_000
    return round(throughput, 2)


def main():
    results = []
    loss_rates = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
    window_sizes = [10, 30, 50, 70, 90]
    timeout_values = [60, 100, 140, 180, 220]
    loss_throughputs = []
    window_throughputs = []
    timeout_throughputs = []
    test_no = 1

    # Test Set 1: Loss Rate değişimi
    print("=== Test Set 1: Varying Loss Rate ===")
    for p in loss_rates:
        thr = run_test(dmax=150, timeout=180, window_size=30, loss_rate=p)
        loss_throughputs.append(thr)
        results.append({
            'Test no': test_no, 'Dmax': 150, 'timeout': 180,
            'window size (N)': 30, 'loss rate (p)': p,
            'Throughput (Mbps)': thr
        })
        test_no += 1

    # Test Set 2: Pencere boyutu değişimi
    print("\n=== Test Set 2: Varying Window Size ===")
    for N in window_sizes:
        thr = run_test(dmax=150, timeout=180, window_size=N, loss_rate=0.1)
        window_throughputs.append(thr)
        results.append({
            'Test no': test_no, 'Dmax': 150, 'timeout': 180,
            'window size (N)': N, 'loss rate (p)': 0.1,
            'Throughput (Mbps)': thr
        })
        test_no += 1

    # Test Set 3: Timeout değişimi
    print("\n=== Test Set 3: Varying Timeout ===")
    for t in timeout_values:
        thr = run_test(dmax=150, timeout=t, window_size=30, loss_rate=0.1)
        timeout_throughputs.append(thr)
        results.append({
            'Test no': test_no, 'Dmax': 150, 'timeout': t,
            'window size (N)': 30, 'loss rate (p)': 0.1,
            'Throughput (Mbps)': thr
        })
        test_no += 1

    # Sonuçları DataFrame'e çevir ve terminale yazdır
    df = pd.DataFrame(results)
    print("\nResults Table:")
    print(df.to_string(index=False))

    # Plot: Throughput vs Loss Rate
    plt.figure(figsize=(10, 6))
    plt.plot(loss_rates, loss_throughputs, 'b-o')
    max_idx = np.argmax(loss_throughputs)
    min_idx = np.argmin(loss_throughputs)
    plt.plot(loss_rates[max_idx], loss_throughputs[max_idx], 'go', markersize=10,
             label=f"Max: {loss_throughputs[max_idx]:.2f} Mbps")
    plt.plot(loss_rates[min_idx], loss_throughputs[min_idx], 'ro', markersize=10,
             label=f"Min: {loss_throughputs[min_idx]:.2f} Mbps")
    plt.grid(True)
    plt.xlabel("Loss Rate (p)")
    plt.ylabel("Throughput (Mbps)")
    plt.title("Throughput vs Loss Rate")
    plt.legend()
    plt.show()

    # Plot: Throughput vs Window Size
    plt.figure(figsize=(10, 6))
    plt.plot(window_sizes, window_throughputs, 'b-o')
    max_idx = np.argmax(window_throughputs)
    min_idx = np.argmin(window_throughputs)
    plt.plot(window_sizes[max_idx], window_throughputs[max_idx], 'go', markersize=10,
             label=f"Max: {window_throughputs[max_idx]:.2f} Mbps")
    plt.plot(window_sizes[min_idx], window_throughputs[min_idx], 'ro', markersize=10,
             label=f"Min: {window_throughputs[min_idx]:.2f} Mbps")
    plt.grid(True)
    plt.xlabel("Window Size (N)")
    plt.ylabel("Throughput (Mbps)")
    plt.title("Throughput vs Window Size")
    plt.legend()
    plt.show()

    # Plot: Throughput vs Timeout
    plt.figure(figsize=(10, 6))
    plt.plot(timeout_values, timeout_throughputs, 'b-o')
    max_idx = np.argmax(timeout_throughputs)
    min_idx = np.argmin(timeout_throughputs)
    plt.plot(timeout_values[max_idx], timeout_throughputs[max_idx], 'go', markersize=10,
             label=f"Max: {timeout_throughputs[max_idx]:.2f} Mbps")
    plt.plot(timeout_values[min_idx], timeout_throughputs[min_idx], 'ro', markersize=10,
             label=f"Min: {timeout_throughputs[min_idx]:.2f} Mbps")
    plt.grid(True)
    plt.xlabel("Timeout (ms)")
    plt.ylabel("Throughput (Mbps)")
    plt.title("Throughput vs Timeout")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()
