"""통계 분석 모듈"""
import numpy as np
from scipy import stats
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class StatisticalAnalyzer:
    """실험 결과의 통계적 분석"""
    
    def analyze_results(self, results: Dict) -> Dict:
        """통계적 유의성 검증 및 효과 크기 계산"""
        baseline_drifts = [r.drift_rate for r in results['baseline_results']]
        statedoc_drifts = [r.drift_rate for r in results['statedoc_results']]
        
        # 기본 통계량 계산
        baseline_mean = float(np.mean(baseline_drifts))
        statedoc_mean = float(np.mean(statedoc_drifts))
        improvement = baseline_mean - statedoc_mean
        
        baseline_std = float(np.std(baseline_drifts, ddof=1)) if len(baseline_drifts) > 1 else 0.0
        statedoc_std = float(np.std(statedoc_drifts, ddof=1)) if len(statedoc_drifts) > 1 else 0.0
        
        # 통계적 검정 (샘플 크기가 충분한 경우)
        if len(baseline_drifts) >= 3 and len(statedoc_drifts) >= 3:
            try:
                # 독립표본 t-검정
                t_stat, p_value = stats.ttest_ind(baseline_drifts, statedoc_drifts)
                
                # Cohen's d (효과 크기) 계산
                pooled_std = np.sqrt(
                    ((len(baseline_drifts)-1)*np.var(baseline_drifts, ddof=1) + 
                     (len(statedoc_drifts)-1)*np.var(statedoc_drifts, ddof=1)) / 
                    (len(baseline_drifts) + len(statedoc_drifts) - 2)
                )
                
                cohens_d = improvement / pooled_std if pooled_std > 0 else 0.0
                    
            except Exception as e:
                logger.warning(f"통계 검정 실패: {e}")
                t_stat, p_value, cohens_d = 0.0, 1.0, 0.0
        else:
            logger.info("샘플 크기가 작아 통계 검정을 생략합니다")
            t_stat, p_value, cohens_d = 0.0, 1.0, 0.0
        
        # 효과 크기 해석
        effect_interpretation = self._interpret_effect_size(cohens_d)
        
        return {
            'baseline_mean_drift': baseline_mean,
            'statedoc_mean_drift': statedoc_mean,
            'improvement': improvement,
            'baseline_std': baseline_std,
            'statedoc_std': statedoc_std,
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'effect_size': float(cohens_d),
            'effect_interpretation': effect_interpretation,
            'significant': bool(p_value < 0.05) if p_value != 1.0 else False,
            'baseline_scores': [r.scores for r in results['baseline_results']],
            'statedoc_scores': [r.scores for r in results['statedoc_results']],
            'sample_size': len(baseline_drifts)
        }
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Cohen's d 효과 크기 해석"""
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "작은 효과"
        elif abs_d < 0.5:
            return "중간 효과"
        elif abs_d < 0.8:
            return "큰 효과"
        else:
            return "매우 큰 효과"
