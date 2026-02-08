"""
Ollama TPS Benchmark: Model × Context Window Performance Matrix

Measures:
- Cold start: Model load time (from disk → GPU memory)
- Prompt eval TPS: tokens/sec for processing input
- Generation TPS: tokens/sec for producing output
- Memory usage per configuration

Tests different models and num_ctx values to find optimal configurations
for each Test-Smith node role.
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass

import requests

OLLAMA_API = "http://localhost:11434"

# Prompt sizes to test different input lengths
PROMPTS = {
    "short": ("Explain quantum computing in one paragraph."),
    "medium": (
        "You are a research analyst. Analyze the following information and provide "
        "a comprehensive summary with key findings, gaps, and contradictions.\n\n"
        "Source 1: Quantum computing uses quantum-mechanical phenomena such as "
        "superposition and entanglement to perform computation. A quantum computer "
        "is used to perform such computation, which can be implemented theoretically "
        "or physically. The field of quantum computing started in the 1980s when "
        "Richard Feynman and Yuri Manin expressed the idea that a quantum computer "
        "had the potential to simulate things a classical computer could not feasibly do.\n\n"
        "Source 2: D-Wave Systems is a Canadian quantum computing company, based in "
        "Burnaby, British Columbia. D-Wave was the world's first company to sell "
        "computers to exploit quantum effects in their operation. D-Wave's early "
        "customers include Lockheed Martin, University of Southern California, "
        "Google/NASA, and Los Alamos National Laboratory.\n\n"
        "Source 3: IBM Quantum is IBM's initiative to build universal quantum computers "
        "for business, engineering and science. IBM has developed several quantum "
        "processors, including the 127-qubit Eagle (2021), the 433-qubit Osprey (2022), "
        "and the 1,121-qubit Condor (2023). Their quantum roadmap targets error-corrected "
        "quantum computing by 2029.\n\n"
        "Provide your analysis:"
    ),
}

# Models to benchmark
DEFAULT_MODELS = ["llama3", "command-r", "qwen3-next"]

# Context window sizes to test
DEFAULT_CTX_SIZES = [2048, 4096, 8192, 32768, 131072]

# Generation length
NUM_PREDICT = 200


@dataclass
class BenchmarkResult:
    model: str
    num_ctx: int
    prompt_name: str
    cold_load_ms: float | None
    warm_load_ms: float
    prompt_eval_tps: float
    generation_tps: float
    prompt_tokens: int
    generated_tokens: int
    total_time_ms: float
    vram_mb: float | None


def unload_all_models() -> None:
    """Unload all models from memory."""
    try:
        resp = requests.get(f"{OLLAMA_API}/api/ps", timeout=10)
        if resp.ok:
            data = resp.json()
            for m in data.get("models", []):
                name = m.get("name", "")
                if name:
                    requests.post(
                        f"{OLLAMA_API}/api/generate",
                        json={"model": name, "prompt": "", "keep_alive": 0},
                        timeout=30,
                    )
                    print(f"  Unloaded: {name}")
    except Exception as e:
        print(f"  Warning: Could not unload models: {e}")
    time.sleep(2)


def get_loaded_model_info() -> dict | None:
    """Get info about currently loaded models."""
    try:
        resp = requests.get(f"{OLLAMA_API}/api/ps", timeout=10)
        if resp.ok:
            data = resp.json()
            models = data.get("models", [])
            if models:
                return models[0]
    except Exception:
        pass
    return None


def run_inference(
    model: str,
    prompt: str,
    num_ctx: int,
    num_predict: int = NUM_PREDICT,
    keep_alive: int = 300,
) -> dict | None:
    """Run a single inference and return timing data."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": keep_alive,
        "options": {
            "num_ctx": num_ctx,
            "num_predict": num_predict,
        },
    }
    try:
        resp = requests.post(
            f"{OLLAMA_API}/api/generate",
            json=payload,
            timeout=600,
        )
        if resp.ok:
            return resp.json()
        else:
            print(f"  ERROR: HTTP {resp.status_code}: {resp.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        print("  ERROR: Request timed out (600s)")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def ns_to_ms(ns: int) -> float:
    return ns / 1_000_000


def benchmark_single(
    model: str,
    num_ctx: int,
    prompt_name: str,
    prompt_text: str,
    cold_start: bool = False,
) -> BenchmarkResult | None:
    """Run benchmark for a single model/ctx/prompt combination."""
    cold_load_ms = None

    if cold_start:
        # Measure cold start: unload → load + generate
        unload_all_models()
        result = run_inference(model, prompt_text, num_ctx)
        if result is None:
            return None
        cold_load_ms = ns_to_ms(result.get("load_duration", 0))
    else:
        # Warm start: model already in memory
        result = run_inference(model, prompt_text, num_ctx)
        if result is None:
            return None

    load_ms = ns_to_ms(result.get("load_duration", 0))
    prompt_eval_count = result.get("prompt_eval_count", 0)
    prompt_eval_ns = result.get("prompt_eval_duration", 0)
    eval_count = result.get("eval_count", 0)
    eval_ns = result.get("eval_duration", 0)
    total_ns = result.get("total_duration", 0)

    prompt_tps = (prompt_eval_count / (prompt_eval_ns / 1e9)) if prompt_eval_ns > 0 else 0
    gen_tps = (eval_count / (eval_ns / 1e9)) if eval_ns > 0 else 0

    # Get VRAM usage
    vram_mb = None
    info = get_loaded_model_info()
    if info:
        vram_bytes = info.get("size_vram", info.get("size", 0))
        vram_mb = vram_bytes / (1024 * 1024)

    return BenchmarkResult(
        model=model,
        num_ctx=num_ctx,
        prompt_name=prompt_name,
        cold_load_ms=cold_load_ms,
        warm_load_ms=load_ms,
        prompt_eval_tps=round(prompt_tps, 1),
        generation_tps=round(gen_tps, 1),
        prompt_tokens=prompt_eval_count,
        generated_tokens=eval_count,
        total_time_ms=round(ns_to_ms(total_ns), 0),
        vram_mb=round(vram_mb, 0) if vram_mb else None,
    )


def check_model_available(model: str) -> bool:
    """Check if model is available in Ollama."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        return model in result.stdout
    except Exception:
        return False


def format_table(results: list[BenchmarkResult]) -> str:
    """Format results as a readable table."""
    lines = []

    # Header
    lines.append(
        f"{'Model':<15} {'ctx':>7} {'prompt':>8} "
        f"{'cold_load':>10} {'warm_load':>10} "
        f"{'prmpt_tps':>10} {'gen_tps':>8} "
        f"{'p_tok':>6} {'g_tok':>6} "
        f"{'total_ms':>9} {'vram_mb':>8}"
    )
    lines.append("-" * 120)

    for r in results:
        cold = f"{r.cold_load_ms:.0f}" if r.cold_load_ms else "-"
        vram = f"{r.vram_mb:.0f}" if r.vram_mb else "-"
        lines.append(
            f"{r.model:<15} {r.num_ctx:>7} {r.prompt_name:>8} "
            f"{cold:>10} {r.warm_load_ms:>10.0f} "
            f"{r.prompt_eval_tps:>10.1f} {r.generation_tps:>8.1f} "
            f"{r.prompt_tokens:>6} {r.generated_tokens:>6} "
            f"{r.total_time_ms:>9.0f} {vram:>8}"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ollama TPS Benchmark")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Models to benchmark",
    )
    parser.add_argument(
        "--ctx-sizes",
        nargs="+",
        type=int,
        default=DEFAULT_CTX_SIZES,
        help="Context window sizes to test",
    )
    parser.add_argument(
        "--prompts",
        nargs="+",
        choices=list(PROMPTS.keys()),
        default=["medium"],
        help="Prompt sizes to test",
    )
    parser.add_argument(
        "--cold-start",
        action="store_true",
        help="Include cold start measurement (slow - unloads model each time)",
    )
    parser.add_argument(
        "--num-predict",
        type=int,
        default=NUM_PREDICT,
        help="Number of tokens to generate",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs per configuration (for averaging)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    # Check Ollama connectivity
    try:
        requests.get(f"{OLLAMA_API}/api/version", timeout=5)
    except Exception:
        print("ERROR: Cannot connect to Ollama at", OLLAMA_API)
        sys.exit(1)

    # Filter to available models
    available = [m for m in args.models if check_model_available(m)]
    skipped = [m for m in args.models if m not in available]
    if skipped:
        print(f"Skipping unavailable models: {skipped}")
    if not available:
        print("No available models to benchmark!")
        sys.exit(1)

    print("=" * 120)
    print("Ollama TPS Benchmark")
    print("=" * 120)
    print(f"Models:       {available}")
    print(f"Context sizes: {args.ctx_sizes}")
    print(f"Prompts:      {args.prompts}")
    print(f"Generate:     {args.num_predict} tokens")
    print(f"Cold start:   {args.cold_start}")
    print(f"Runs:         {args.runs}")
    print("=" * 120)

    all_results: list[BenchmarkResult] = []

    for model in available:
        print(f"\n{'=' * 60}")
        print(f"Model: {model}")
        print(f"{'=' * 60}")

        # First: warm up the model with smallest context
        print(f"  Warming up {model}...")
        unload_all_models()
        warmup = run_inference(model, "Hello", min(args.ctx_sizes), num_predict=1)
        if warmup:
            cold_load = ns_to_ms(warmup.get("load_duration", 0))
            print(f"  Cold load time: {cold_load:.0f}ms")
        else:
            print(f"  WARNING: Failed to load {model}, skipping")
            continue

        for ctx_size in args.ctx_sizes:
            for prompt_name in args.prompts:
                prompt_text = PROMPTS[prompt_name]
                label = f"  {model} ctx={ctx_size} prompt={prompt_name}"
                print(f"{label}...", end="", flush=True)

                run_results = []
                for run_idx in range(args.runs):
                    if args.cold_start and run_idx == 0:
                        r = benchmark_single(
                            model, ctx_size, prompt_name, prompt_text, cold_start=True
                        )
                    else:
                        r = benchmark_single(
                            model, ctx_size, prompt_name, prompt_text, cold_start=False
                        )

                    if r:
                        run_results.append(r)

                if run_results:
                    # Use last result (or average if multiple runs)
                    best = run_results[-1]
                    if len(run_results) > 1:
                        avg_gen_tps = sum(r.generation_tps for r in run_results) / len(run_results)
                        avg_prompt_tps = sum(r.prompt_eval_tps for r in run_results) / len(
                            run_results
                        )
                        best = BenchmarkResult(
                            model=best.model,
                            num_ctx=best.num_ctx,
                            prompt_name=best.prompt_name,
                            cold_load_ms=run_results[0].cold_load_ms,
                            warm_load_ms=best.warm_load_ms,
                            prompt_eval_tps=round(avg_prompt_tps, 1),
                            generation_tps=round(avg_gen_tps, 1),
                            prompt_tokens=best.prompt_tokens,
                            generated_tokens=best.generated_tokens,
                            total_time_ms=best.total_time_ms,
                            vram_mb=best.vram_mb,
                        )
                    all_results.append(best)
                    print(
                        f" gen={best.generation_tps:.1f} tps, "
                        f"prompt={best.prompt_eval_tps:.1f} tps, "
                        f"total={best.total_time_ms:.0f}ms"
                    )
                else:
                    print(" FAILED")

    # Print results
    print("\n" + "=" * 120)
    print("RESULTS")
    print("=" * 120)
    print(format_table(all_results))

    # Print analysis
    print("\n" + "=" * 120)
    print("ANALYSIS: Context Window Impact on TPS")
    print("=" * 120)
    for model in available:
        model_results = [r for r in all_results if r.model == model]
        if len(model_results) < 2:
            continue
        base = model_results[0]
        print(f"\n{model}:")
        for r in model_results:
            ratio = r.generation_tps / base.generation_tps if base.generation_tps > 0 else 0
            print(
                f"  ctx={r.num_ctx:>7}: gen={r.generation_tps:>6.1f} tps "
                f"({ratio:>5.2f}x vs ctx={base.num_ctx}), "
                f"vram={r.vram_mb or '?'}MB"
            )

    # Node optimization recommendations
    print("\n" + "=" * 120)
    print("NODE OPTIMIZATION RECOMMENDATIONS")
    print("=" * 120)

    node_profiles = {
        "planner": {"input": "short", "output": "short", "needs_quality": "medium"},
        "evaluator": {"input": "medium", "output": "short", "needs_quality": "medium"},
        "reflection": {"input": "medium", "output": "medium", "needs_quality": "high"},
        "analyzer": {"input": "long", "output": "long", "needs_quality": "high"},
        "synthesizer": {"input": "long", "output": "long", "needs_quality": "high"},
    }
    for node, profile in node_profiles.items():
        print(
            f"\n  {node}: input={profile['input']}, output={profile['output']}, quality={profile['needs_quality']}"
        )

    if args.json:
        json_data = [
            {
                "model": r.model,
                "num_ctx": r.num_ctx,
                "prompt": r.prompt_name,
                "cold_load_ms": r.cold_load_ms,
                "warm_load_ms": r.warm_load_ms,
                "prompt_eval_tps": r.prompt_eval_tps,
                "generation_tps": r.generation_tps,
                "prompt_tokens": r.prompt_tokens,
                "generated_tokens": r.generated_tokens,
                "total_time_ms": r.total_time_ms,
                "vram_mb": r.vram_mb,
            }
            for r in all_results
        ]
        json_path = "reports/benchmark_ollama_tps.json"
        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"\nJSON results saved to: {json_path}")


if __name__ == "__main__":
    main()
