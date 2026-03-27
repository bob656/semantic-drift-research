"""
statistical_analyzer.py — 실험 결과의 통계적 분석

N번 반복 실험에서 수집한 드리프트율 데이터를 분석하여
BaselineAgent와 StateDocAgent 간의 차이가 통계적으로 유의미한지 검증합니다.

사용하는 통계 기법:
  1. 독립표본 t-검정 (Welch's t-test)
     두 그룹(Baseline, StateDoc)의 평균 드리프트율이
     우연에 의한 차이인지, 실제 차이인지 판단합니다.
     p-value < 0.05 이면 "통계적으로 유의미한 차이"로 해석합니다.

  2. Cohen's d (효과 크기)
     차이가 얼마나 큰지를 나타냅니다. p-value와 별개의 개념입니다.
       0.2 미만: 작은 효과
       0.2~0.5:  중간 효과
       0.5~0.8:  큰 효과
       0.8 이상: 매우 큰 효과

샘플 크기와 통계 검정:
  샘플이 3개 미만이면 t-검정을 생략하고 p-value=1.0을 반환합니다.
  신뢰할 수 있는 결과를 위해 --repeats 10 이상을 권장합니다.
"""
import math
import numpy as np
from scipy import stats
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """실험 결과의 통계적 분석"""

    def analyze_results(self, results: Dict) -> Dict:
        """
        Baseline과 StateDoc의 드리프트율을 비교 분석합니다.

        Parameters
        ----------
        results : ExperimentRunner.run_pilot_experiment()의 반환값
                  {'baseline_results': [...], 'statedoc_results': [...]}

        Returns
        -------
        dict : 통계 지표 딕셔너리 (main.py의 print_results, save_results에서 사용)
        """
        # 각 반복 실험에서 드리프트율만 추출
        baseline_drifts = [r.drift_rate for r in results['baseline_results']]
        statedoc_drifts = [r.drift_rate for r in results['statedoc_results']]

        # --- 기본 통계량 ---
        baseline_mean = float(np.mean(baseline_drifts))
        statedoc_mean = float(np.mean(statedoc_drifts))

        # improvement > 0: StateDoc이 더 드리프트가 적음 (가설 지지)
        # improvement < 0: StateDoc이 오히려 더 드리프트가 많음 (가설 기각)
        improvement = baseline_mean - statedoc_mean

        # ddof=1: 표본 표준편차 (모집단 아닌 샘플 기준)
        baseline_std = float(np.std(baseline_drifts, ddof=1)) if len(baseline_drifts) > 1 else 0.0
        statedoc_std = float(np.std(statedoc_drifts, ddof=1)) if len(statedoc_drifts) > 1 else 0.0

        # --- 통계적 검정 (샘플이 충분한 경우만 실행) ---
        if len(baseline_drifts) >= 3 and len(statedoc_drifts) >= 3:
            try:
                # 독립표본 t-검정
                # 두 그룹의 분산이 다를 수 있으므로 equal_var=False(Welch's t-test)가 기본값
                t_stat, p_value = stats.ttest_ind(baseline_drifts, statedoc_drifts)

                # NaN 처리: 두 그룹이 모두 분산 0(예: 드리프트율이 전부 0.0)일 때
                # scipy가 NaN을 반환함 → 검정 불가 상태로 처리
                if math.isnan(t_stat) or math.isnan(p_value):
                    logger.warning("t-검정 결과 NaN — 두 그룹의 분산이 모두 0입니다. 검정을 생략합니다.")
                    t_stat, p_value, cohens_d = 0.0, 1.0, 0.0
                else:
                    # Cohen's d 계산
                    # pooled_std: 두 그룹의 분산을 가중 평균한 합동 표준편차
                    pooled_std = np.sqrt(
                        ((len(baseline_drifts)-1) * np.var(baseline_drifts, ddof=1) +
                         (len(statedoc_drifts)-1) * np.var(statedoc_drifts, ddof=1)) /
                        (len(baseline_drifts) + len(statedoc_drifts) - 2)
                    )

                    # d = 평균 차이 / 합동 표준편차
                    # pooled_std=0이면 두 그룹이 완전히 같은 경우 → d=0
                    cohens_d = improvement / pooled_std if pooled_std > 0 else 0.0

            except Exception as e:
                logger.warning(f"통계 검정 실패: {e}")
                # 검정 실패 시 중립값 설정 (p=1.0은 "차이 없음"을 의미)
                t_stat, p_value, cohens_d = 0.0, 1.0, 0.0
        else:
            # 샘플이 너무 적으면 검정 자체가 의미 없음
            logger.info("샘플 크기가 작아 통계 검정을 생략합니다")
            t_stat, p_value, cohens_d = 0.0, 1.0, 0.0

        effect_interpretation = self._interpret_effect_size(cohens_d)

        return {
            'baseline_mean_drift':  baseline_mean,
            'statedoc_mean_drift':  statedoc_mean,
            'improvement':          improvement,          # 양수면 StateDoc이 더 좋음
            'baseline_std':         baseline_std,
            'statedoc_std':         statedoc_std,
            't_statistic':          float(t_stat),
            'p_value':              float(p_value),       # < 0.05이면 유의미
            'effect_size':          float(cohens_d),
            'effect_interpretation': effect_interpretation,
            'significant':          bool(p_value < 0.05) if not math.isnan(p_value) and p_value != 1.0 else False,
            # 원본 점수 시계열도 포함 (그래프 그릴 때 활용 가능)
            'baseline_scores':      [r.scores for r in results['baseline_results']],
            'statedoc_scores':      [r.scores for r in results['statedoc_results']],
            'sample_size':          len(baseline_drifts)
        }

    def _interpret_effect_size(self, cohens_d: float) -> str:
        """
        Cohen's d 값을 직관적인 텍스트로 변환합니다.

        Jacob Cohen(1988)의 기준:
          d < 0.2  → 작은 효과 (일상에서 거의 느끼지 못하는 수준)
          d < 0.5  → 중간 효과
          d < 0.8  → 큰 효과
          d >= 0.8 → 매우 큰 효과 (이번 실험 결과: 0.816)

        주의: 효과 크기가 크더라도 샘플이 적으면 p-value가 유의미하지 않을 수 있음
        """
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "작은 효과"
        elif abs_d < 0.5:
            return "중간 효과"
        elif abs_d < 0.8:
            return "큰 효과"
        else:
            return "매우 큰 효과"
