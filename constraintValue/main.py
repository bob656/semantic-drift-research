"""
main.py — 수치 계약 보존 실험 진입점

사용 예시:
  python constraintValue/main.py --host http://192.168.100.52:11434
  python constraintValue/main.py --host http://192.168.100.52:11434 --repeats 5
  python constraintValue/main.py --host http://192.168.100.52:11434 --agents Baseline
"""
import argparse
import logging
import sys
import os

# constraintValue 폴더를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runner import NumericExperimentRunner, save_results  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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
                    messages=[{'role': 'user', 'content': 'Hello'}],
                    options={'num_predict': 5})
        print(f"✅ 연결 성공 (모델: {model})")
        return True
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False


def print_summary(results: dict) -> None:
    print(f"\n{'='*60}")
    print("📊 수치 계약 보존 실험 결과 요약")
    print(f"{'='*60}")

    for name, result_list in results.items():
        if name == 'scenario' or not result_list:
            continue
        scores_final = [r.scores[-1] for r in result_list]
        scores_init  = [r.scores[0]  for r in result_list]
        drifts       = [r.drift_rate  for r in result_list]

        avg_init  = sum(scores_init)  / len(scores_init)
        avg_final = sum(scores_final) / len(scores_final)
        avg_drift = sum(drifts)       / len(drifts)

        print(f"\n[{name}]")
        print(f"  초기 점수:  {avg_init:.2f}/10")
        print(f"  최종 점수:  {avg_final:.2f}/10")
        print(f"  드리프트율: {avg_drift:.3f}")

        # 수치별 보존율
        preserved_counts = {}
        total_steps = 0
        for r in result_list:
            for step_details in r.details:
                total_steps += 1
                for d in step_details:
                    if 'PRESERVED' in d:
                        key = d.split()[1]
                        preserved_counts[key] = preserved_counts.get(key, 0) + 1

        if preserved_counts and total_steps > 0:
            print(f"  수치별 보존율:")
            for key, count in preserved_counts.items():
                rate = count / (total_steps) * 100
                print(f"    {key}: {rate:.0f}%")

    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='수치 계약 보존 실험 — LLM Constant Value Error 측정',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--host',    default=DEFAULT_HOST)
    parser.add_argument('--model',   default=DEFAULT_MODEL)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--agents',  default=None,
                        help='실행할 에이전트 (콤마 구분). 예: Baseline,NumericContract')
    args = parser.parse_args()

    print("🔢 수치 계약 보존 실험")
    print("=" * 50)
    print(f"Ollama 서버: {args.host}")
    print(f"모델: {args.model}")

    client = make_client(args.host)
    if not check_connection(client, args.model):
        return 1

    selected = ([a.strip() for a in args.agents.split(',')]
                if args.agents else None)

    runner = NumericExperimentRunner(model=args.model, client=client)
    results = runner.run(num_repeats=args.repeats, agents=selected)

    print_summary(results)
    save_results(results, args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
