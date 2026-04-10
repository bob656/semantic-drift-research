"""
loop_main.py — 4단계 순환 평가 실험 진입점

사용 예시:
  python constraintValue/loop_main.py --host http://192.168.100.52:11434
  python constraintValue/loop_main.py --host http://192.168.100.52:11434 --repeats 5
  python constraintValue/loop_main.py --host http://192.168.100.52:11434 --threshold 8.0 --max-retries 3
"""
import argparse
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop_runner import LoopRunner, save_results

logging.basicConfig(
    level=logging.WARNING,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), '..', 'experiment.log'),
            encoding='utf-8'),
    ]
)

DEFAULT_MODEL = "qwen2.5-coder:14b"
DEFAULT_HOST  = "http://192.168.100.52:11434"


def make_client(host: str):
    from ollama import Client
    return Client(host=host, timeout=600)


def check_connection(client, model: str) -> bool:
    try:
        client.chat(model=model,
                    messages=[{'role': 'user', 'content': 'Hi'}],
                    options={'num_predict': 5})
        print(f"✅ 연결 성공 (모델: {model})")
        return True
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False


def print_final_summary(aggregators: dict) -> None:
    print(f"\n{'='*60}")
    print("📊 4단계 순환 평가 — 최종 결과")
    print(f"{'='*60}")

    rows = []
    for name, agg in aggregators.items():
        s = agg.summary()
        rows.append((
            name,
            s['drift_rate']['mean'],
            s['drift_rate']['std'],
            s['recovery_success']['mean'],
            s['asl']['mean'],
            s['final_score']['mean'],
            s['drift_occurred_runs'],
            s['n_runs'],
        ))

    print(f"\n{'에이전트':<20} {'Drift Rate':>12} {'Recovery':>10} {'ASL':>6} {'최종점수':>10} {'드리프트발생':>12}")
    print("-" * 75)
    for name, dr, dr_std, rec, asl, fs, d_runs, n in rows:
        print(f"{name:<20} {dr:.3f}±{dr_std:.3f}  {rec:>8.3f}  {asl:>5.1f}  {fs:>8.2f}/10  {d_runs:>5}/{n}")

    print(f"\n{'='*60}")

    if len(rows) == 2:
        b = rows[0]
        n = rows[1]
        dr_diff = b[1] - n[1]
        print(f"\n개선 효과 (Drift Rate 감소): {dr_diff:+.3f}")
        print(f"ASL 향상: {n[3] - b[3]:+.1f} 루프")


def main():
    parser = argparse.ArgumentParser(
        description='4단계 순환 평가 실험 — 수치 계약 보존',
    )
    parser.add_argument('--host',        default=DEFAULT_HOST)
    parser.add_argument('--model',       default=DEFAULT_MODEL)
    parser.add_argument('--repeats',     type=int,   default=3)
    parser.add_argument('--threshold',   type=float, default=7.0)
    parser.add_argument('--max-retries', type=int,   default=2,
                        dest='max_retries')
    parser.add_argument('--agents',      default=None,
                        help='콤마 구분. 예: Baseline,NumericContract')
    args = parser.parse_args()

    print("🔄 4단계 순환 평가 실험")
    print("=" * 50)
    print(f"서버: {args.host} | 모델: {args.model}")
    print(f"기준: {args.threshold}/10 | 재시도: {args.max_retries}회")

    client = make_client(args.host)
    if not check_connection(client, args.model):
        return 1

    selected = ([a.strip() for a in args.agents.split(',')]
                if args.agents else None)

    runner = LoopRunner(
        model=args.model,
        client=client,
        threshold=args.threshold,
        max_retries=args.max_retries,
    )
    aggregators = runner.run(num_repeats=args.repeats, agents=selected)

    print_final_summary(aggregators)
    save_results(aggregators, args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
