import argparse
import json
import os
import logging
from datetime import datetime
from typing import Dict

from runner import ExperimentRunner
from analyzer import StatisticalAnalyzer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('experiment.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5-coder:14b"
DEFAULT_HOST = "http://192.168.100.52:11434"


def make_client(host: str):
    """Ollama 클라이언트 생성"""
    from ollama import Client
    return Client(host=host, timeout=600)


def check_ollama_connection(client, model: str) -> bool:
    """Ollama 연결 및 모델 상태 확인"""
    try:
        client.chat(
            model=model,
            messages=[{'role': 'user', 'content': 'Hello'}],
            options={'num_predict': 10}
        )
        logger.info(f"✅ Ollama 연결 성공 (모델: {model})")
        return True

    except Exception as e:
        logger.error(f"❌ Ollama 연결 실패: {e}")
        print("\n🔧 해결 방법:")
        print("1. 원격 컴퓨터에서 'ollama serve' 실행 확인")
        print(f"2. --host 옵션으로 주소 지정 (예: --host http://192.168.0.10:11434)")
        print(f"3. 'ollama pull {model}' 명령어로 모델 다운로드 확인")
        return False


def save_results(results: Dict, stats_result: Dict, args) -> str:
    """실험 결과를 JSON 파일로 저장"""
    os.makedirs('results', exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/pilot_{timestamp}.json"

    output_data = {
        'metadata': {
            'timestamp': timestamp,
            'model': args.model,
            'host': args.host,
            'repeats': args.repeats,
            'mode': args.mode,
            'eval_mode': args.eval_mode,
            'system_info': {
                'platform': 'macOS',
                'environment': 'Ollama + VSCode'
            }
        },
        'summary': stats_result,
        'raw_results': {
            agent_key: [
                {
                    'scores': r.scores,
                    'drift_rate': r.drift_rate,
                    'execution_times': r.execution_times,
                    'total_interactions': len(r.interaction_log),
                    'test_details': r.test_details or [],
                    'verifier_log': r.verifier_log or [],
                } for r in results.get(result_key, [])
            ]
            for agent_key, result_key in [
                ('baseline',    'baseline_results'),
                ('statedoc',    'statedoc_results'),
                ('semantic',    'semantic_results'),
                ('semantic_v2', 'semantic_v2_results'),
                ('semantic_v3', 'semantic_v3_results'),
            ]
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"실험 결과 저장: {filename}")
    return filename


def print_results(stats_result: Dict):
    """실험 결과를 포맷팅하여 출력"""
    print(f"\n{'='*60}")
    print("📊 실험 결과 요약")
    print(f"{'='*60}")
    print(f"베이스라인 평균 드리프트:         {stats_result['baseline_mean_drift']:.3f}점 (±{stats_result['baseline_std']:.3f})")
    print(f"LayeredMemory 평균 드리프트:     {stats_result['statedoc_mean_drift']:.3f}점 (±{stats_result['statedoc_std']:.3f})")
    if stats_result.get('semantic_mean_drift') is not None:
        print(f"SemanticCompressor 평균 드리프트: {stats_result['semantic_mean_drift']:.3f}점 (±{stats_result['semantic_std']:.3f})")
    print(f"📈 개선 효과 (vs LayeredMemory): {stats_result['improvement']:.3f}점")
    if stats_result.get('improvement_semantic') is not None:
        print(f"📈 개선 효과 (vs Semantic):      {stats_result['improvement_semantic']:.3f}점")

    if stats_result['p_value'] != 1.0:
        print(f"P-value: {stats_result['p_value']:.4f}")
        print(f"효과 크기 (Cohen's d): {stats_result['effect_size']:.3f} ({stats_result['effect_interpretation']})")
        significance = "✅ 예" if stats_result['significant'] else "❌ 아니오"
        print(f"통계적 유의성 (p < 0.05): {significance}")
    else:
        print("통계적 검정: 샘플 크기 부족으로 생략")

    print(f"샘플 크기: {stats_result['sample_size']}회 반복")
    print(f"{'='*60}")


def print_recommendations(stats_result: Dict, args):
    """결과에 따른 권장사항 출력"""
    improvement = stats_result['improvement']
    significant = stats_result['significant']

    # 절대 하락량 기준: 0.5점 이상 개선 + 유의미 → 성공
    if improvement > 0.5 and significant:
        print(f"\n🎉 성공적인 결과!")
        print(f"상태 문서 접근법이 의미 드리프트를 {improvement:.3f}점 감소시켰습니다.")
        print("📝 이 결과로 교수님께 보고서를 작성할 수 있습니다.")
        print("\n📋 다음 단계 권장사항:")
        print("1. 더 많은 반복 실험으로 신뢰성 강화")
        print("2. 다른 도메인(웹 API, 알고리즘)으로 확장")
        print("3. 더 큰 모델(13B, 34B)로 검증")

    # 0.2점 이상 개선이지만 유의미하지 않은 경우
    elif improvement > 0.2:
        print(f"\n🤔 제한적인 개선 효과")
        print(f"상태 문서가 {improvement:.3f}점 개선 효과를 보였으나 통계적 유의성이 부족합니다.")
        print("\n🔧 개선 방안:")
        print(f"1. --repeats {args.repeats * 2}로 실험 반복 횟수 증가")
        print("2. 더 복잡한 시나리오로 차이 극대화")
        print("3. 다른 모델로 실험 (codellama:13b 등)")

    else:
        print(f"\n⚠️  예상보다 낮은 효과")
        print("상태 문서의 효과가 명확하지 않습니다.")
        print("\n🔧 문제 해결 방안:")
        print("1. 실험 시나리오 복잡도 증가")
        print("2. 상태 문서 구조 개선")
        print("3. 평가 기준 재검토")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='LLM 코딩 에이전트 의미 드리프트 연구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py --host http://192.168.0.10:11434
  python main.py --host http://192.168.0.10:11434 --repeats 5
  python main.py --host http://192.168.0.10:11434 --model codellama:13b
        """
    )

    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        help=f'Ollama 서버 주소 (기본값: {DEFAULT_HOST})'
    )
    parser.add_argument(
        '--mode',
        choices=['pilot'],
        default='pilot',
        help='실험 모드 (현재는 pilot만 지원)'
    )
    parser.add_argument(
        '--repeats',
        type=int,
        default=3,
        help='실험 반복 횟수 (기본값: 3, 권장: 5 이상)'
    )
    parser.add_argument(
        '--model',
        default=DEFAULT_MODEL,
        help=f'사용할 Ollama 모델 (기본값: {DEFAULT_MODEL})'
    )
    parser.add_argument(
        '--eval-mode',
        choices=['llm', 'exec'],
        default='llm',
        help='평가 방식: llm=LLM 채점(기본), exec=코드 실행 테스트'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='빠른 검증 모드: step3 이후만 실행 (step0~2 생략, ~3배 빠름)'
    )
    parser.add_argument(
        '--agents',
        default=None,
        help='실행할 에이전트 (콤마 구분, 기본=전체). 예: Baseline,SemanticCompressorV2'
    )
    parser.add_argument(
        '--scenario',
        choices=['order', 'budget'],
        default='order',
        help='실험 시나리오: order=OrderSystem(기본), budget=BudgetTracker(설계 의도 보존 측정)'
    )

    args = parser.parse_args()

    print("🔬 LLM 코딩 에이전트 의미 드리프트 연구")
    print("=" * 50)
    print(f"Ollama 서버: {args.host}")

    client = make_client(args.host)

    if not check_ollama_connection(client, args.model):
        return 1

    estimated_time = args.repeats * 15
    print(f"\n⏰ 예상 소요 시간: {estimated_time//60}시간 {estimated_time%60}분")
    print("실험이 진행되는 동안 컴퓨터를 사용하셔도 됩니다 ☕")

    start_time = datetime.now()
    eval_mode = args.eval_mode
    print(f"평가 방식: {'코드 실행 테스트' if eval_mode == 'exec' else 'LLM 채점'}")
    runner = ExperimentRunner(model=args.model, client=client, eval_mode=eval_mode)

    selected_agents = [a.strip() for a in args.agents.split(',')] if args.agents else None

    if args.scenario == 'budget':
        print("📒 BudgetTracker 시나리오 (설계 의도 보존 측정)")
        raw = runner.run_budget_experiment(
            num_repeats=args.repeats,
            agents=selected_agents,
        )
        # analyzer가 기대하는 키 형식으로 변환
        results = {
            'scenario': raw.get('scenario', 'BudgetTracker Intent'),
            'baseline_results':    raw.get('Baseline', []),
            'statedoc_results':    raw.get('LayeredMemory', []),
            'semantic_results':    raw.get('SemanticCompressor', []),
            'semantic_v2_results': raw.get('SemanticCompressorV2', []),
            'semantic_v3_results': raw.get('SemanticCompressorV3', []),
        }
    elif args.quick:
        print("⚡ 빠른 검증 모드")
        results = runner.run_quick_experiment(
            num_repeats=args.repeats,
            agents=selected_agents,
        )
    else:
        results = runner.run_pilot_experiment(num_repeats=args.repeats)
    end_time = datetime.now()

    analyzer = StatisticalAnalyzer()
    stats_result = analyzer.analyze_results(results)

    execution_duration = (end_time - start_time).total_seconds() / 60
    logger.info(f"실험 완료. 소요 시간: {execution_duration:.1f}분")

    print_results(stats_result)
    filename = save_results(results, stats_result, args)
    print(f"\n💾 상세 결과 저장: {filename}")

    print_recommendations(stats_result, args)

    print(f"\n🏁 실험 완료! 총 소요 시간: {execution_duration:.1f}분")
    return 0


if __name__ == '__main__':
    exit(main())
