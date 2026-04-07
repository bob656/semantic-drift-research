"""
statistical_analyzer.py — 실험 결과의 통계적 분석

N번 반복 실험에서 수집한 드리프트율 데이터를 분석하여
Baseline / LayeredMemory / SemanticCompressor 간의 차이가
통계적으로 유의미한지 검증합니다.

사용하는 통계 기법:
  1. 독립표본 t-검정 (Welch's t-test)
     두 그룹의 평균 드리프트율이 우연인지 실제 차이인지 판단합니다.
     p-value < 0.05 이면 "통계적으로 유의미한 차이"로 해석합니다.

  2. Cohen's d (효과 크기)
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
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """실험 결과의 통계적 분석"""

    def analyze_results(self, results: Dict) -> Dict:
        """
        Baseline / LayeredMemory / SemanticCompressor 드리프트율을 비교 분석합니다.

        Parameters
        ----------
        results : ExperimentRunner.run_pilot_experiment()의 반환값
                  {'baseline_results': [...], 'statedoc_results': [...],
                   'semantic_results': [...]}  ← semantic_results는 없을 수도 있음

        Returns
        -------
        dict : 통계 지표 딕셔너리
        """
        baseline_drifts = [r.drift_rate for r in results['baseline_results']]
        statedoc_drifts = [r.drift_rate for r in results['statedoc_results']]
        semantic_drifts = [r.drift_rate for r in results.get('semantic_results', [])]

        baseline_mean = float(np.mean(baseline_drifts))
        statedoc_mean = float(np.mean(statedoc_drifts))
        semantic_mean = float(np.mean(semantic_drifts)) if semantic_drifts else None

        baseline_std = float(np.std(baseline_drifts, ddof=1)) if len(baseline_drifts) > 1 else 0.0
        statedoc_std = float(np.std(statedoc_drifts, ddof=1)) if len(statedoc_drifts) > 1 else 0.0
        semantic_std = float(np.std(semantic_drifts, ddof=1)) if len(semantic_drifts) > 1 else 0.0

        # Baseline vs LayeredMemory
        improvement_layered = baseline_mean - statedoc_mean
        t_layered, p_layered, d_layered = self._ttest(baseline_drifts, statedoc_drifts)

        # Baseline vs SemanticCompressor
        improvement_semantic = (baseline_mean - semantic_mean) if semantic_mean is not None else None
        t_semantic, p_semantic, d_semantic = (
            self._ttest(baseline_drifts, semantic_drifts)
            if semantic_drifts else (0.0, 1.0, 0.0)
        )

        # LayeredMemory vs SemanticCompressor (직접 비교)
        t_vs, p_vs, d_vs = (
            self._ttest(statedoc_drifts, semantic_drifts)
            if semantic_drifts else (0.0, 1.0, 0.0)
        )

        return {
            # ── 기본 통계 ──
            'baseline_mean_drift':  baseline_mean,
            'statedoc_mean_drift':  statedoc_mean,
            'semantic_mean_drift':  semantic_mean,
            'improvement':          improvement_layered,   # 하위 호환
            'baseline_std':         baseline_std,
            'statedoc_std':         statedoc_std,
            'semantic_std':         semantic_std,

            # ── Baseline vs LayeredMemory ──
            't_statistic':          float(t_layered),
            'p_value':              float(p_layered),
            'effect_size':          float(d_layered),
            'effect_interpretation': self._interpret_effect_size(d_layered),
            'significant':          bool(p_layered < 0.05) if p_layered != 1.0 else False,

            # ── Baseline vs SemanticCompressor ──
            'improvement_semantic': improvement_semantic,
            't_semantic':           float(t_semantic),
            'p_semantic':           float(p_semantic),
            'd_semantic':           float(d_semantic),
            'significant_semantic': bool(p_semantic < 0.05) if p_semantic != 1.0 else False,

            # ── LayeredMemory vs SemanticCompressor ──
            't_vs':                 float(t_vs),
            'p_vs':                 float(p_vs),
            'd_vs':                 float(d_vs),

            # ── 원본 시계열 ──
            'baseline_scores':      [r.scores for r in results['baseline_results']],
            'statedoc_scores':      [r.scores for r in results['statedoc_results']],
            'semantic_scores':      [r.scores for r in results.get('semantic_results', [])],
            'sample_size':          len(baseline_drifts)
        }

    def _ttest(self, a: List[float], b: List[float]):
        """독립표본 t-검정 + Cohen's d 반환. 샘플 부족 시 (0, 1, 0) 반환."""
        if len(a) < 3 or len(b) < 3:
            return 0.0, 1.0, 0.0
        try:
            t_stat, p_value = stats.ttest_ind(a, b)
            if math.isnan(t_stat) or math.isnan(p_value):
                return 0.0, 1.0, 0.0
            pooled_std = np.sqrt(
                ((len(a)-1) * np.var(a, ddof=1) + (len(b)-1) * np.var(b, ddof=1)) /
                (len(a) + len(b) - 2)
            )
            improvement = float(np.mean(a)) - float(np.mean(b))
            cohens_d = improvement / pooled_std if pooled_std > 0 else 0.0
            return float(t_stat), float(p_value), float(cohens_d)
        except Exception as e:
            logger.warning(f"통계 검정 실패: {e}")
            return 0.0, 1.0, 0.0

    def _interpret_effect_size(self, cohens_d: float) -> str:
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "작은 효과"
        elif abs_d < 0.5:
            return "중간 효과"
        elif abs_d < 0.8:
            return "큰 효과"
        else:
            return "매우 큰 효과"
