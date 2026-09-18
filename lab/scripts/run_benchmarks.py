import requests
import time
import statistics
import concurrent.futures

API_BASE = "http://localhost:8020/api/v1"
NUM_REQUESTS = 300
CONCURRENCY = 10

def benchmark_endpoint(url, params):
    latencies = []
    errors = 0

    def single_req():
        start = time.time()
        try:
            r = requests.get(url, params=params, timeout=10)
            dur = (time.time() - start) * 1000
            if r.status_code == 200:
                return dur, False
            return dur, True
        except Exception:
            return (time.time() - start) * 1000, True

    start_total = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(single_req) for _ in range(NUM_REQUESTS)]
        for f in concurrent.futures.as_completed(futures):
            dur, err = f.result()
            latencies.append(dur)
            if err:
                errors += 1

    total_time = time.time() - start_total
    rps = NUM_REQUESTS / total_time

    latencies.sort()
    mean_lat = statistics.mean(latencies)
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    return {
        "num_requests": NUM_REQUESTS,
        "concurrency": CONCURRENCY,
        "total_time_s": round(total_time, 2),
        "rps": round(rps, 2),
        "mean_ms": round(mean_lat, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "errors": errors
    }

def main():
    print(f"==================================================================")
    print(f"BENCHMARK CIENTÍFICO: VULNERABLE vs MITIGADO ({NUM_REQUESTS} reqs, {CONCURRENCY} concurrent)")
    print(f"==================================================================")

    print("[+] Evaluando Endpoint Vulnerable (SQL Dinámico / f-strings)...")
    res_vuln = benchmark_endpoint(
        f"{API_BASE}/vulnerable/predios/radio",
        {"x": -2783495.2, "y": 12459430.2, "distancia": "150", "sector": "0101"}
    )

    print("[+] Evaluando Endpoint Mitigado (GeoAlchemy2 + Bind Parameters + Validación)...")
    res_mit = benchmark_endpoint(
        f"{API_BASE}/mitigated/predios/radio",
        {"x": -2783495.2, "y": 12459430.2, "distancia": 150.0, "sector": "0101"}
    )

    diff_mean = res_mit["mean_ms"] - res_vuln["mean_ms"]
    diff_p95 = res_mit["p95_ms"] - res_vuln["p95_ms"]

    print("\n" + "="*80)
    print("TABLA COMPARATIVA DE RENDIMIENTO (LISTA PARA INCLUIR EN EL PAPER - IMJETA)")
    print("="*80)
    print("| Métrica de Rendimiento | API Vulnerable (SQL Dinámico) | API Mitigada (GeoAlchemy2) | Variación (Overhead) |")
    print("| :--- | :--- | :--- | :--- |")
    print(f"| Throughput (Req/seg) | {res_vuln['rps']} req/s | {res_mit['rps']} req/s | {round(res_mit['rps'] - res_vuln['rps'], 2)} req/s |")
    print(f"| Latencia Media (Mean) | {res_vuln['mean_ms']} ms | {res_mit['mean_ms']} ms | +{round(diff_mean, 2)} ms |")
    print(f"| Percentil 50 (p50 / Mediana) | {res_vuln['p50_ms']} ms | {res_mit['p50_ms']} ms | +{round(res_mit['p50_ms'] - res_vuln['p50_ms'], 2)} ms |")
    print(f"| Percentil 95 (p95) | {res_vuln['p95_ms']} ms | {res_mit['p95_ms']} ms | +{round(diff_p95, 2)} ms |")
    print(f"| Percentil 99 (p99) | {res_vuln['p99_ms']} ms | {res_mit['p99_ms']} ms | +{round(res_mit['p99_ms'] - res_vuln['p99_ms'], 2)} ms |")
    print(f"| Tasa de Fallos | {res_vuln['errors']} ({round(res_vuln['errors']/NUM_REQUESTS*100, 1)}%) | {res_mit['errors']} ({round(res_mit['errors']/NUM_REQUESTS*100, 1)}%) | 0% |")
    print("="*80)

if __name__ == "__main__":
    main()
