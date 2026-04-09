"""
실험 결과 시각화 — 3-way 비교 (Baseline vs SemanticV2 vs SemanticV3)
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# ── 데이터 로드 ──────────────────────────────────────
with open('results/pilot_20260409_150038.json') as f:
    data = json.load(f)
raw = data['raw_results']

# ── 색상 ─────────────────────────────────────────────
C_BASE = '#E07B54'
C_V2   = '#4A90D9'
C_V3   = '#7B5EA7'
C_PASS = '#5BAD6F'
C_FAIL = '#D95B5B'
C_BG   = '#F8F8F8'
C_GRID = '#E0E0E0'

AGENTS = [
    ('baseline',    'Baseline',       C_BASE),
    ('semantic_v2', 'SemanticV2',     C_V2),
    ('semantic_v3', 'SemanticV3\n(히스토리+Verifier)', C_V3),
]

STEP_LABELS = ['step0\n(초기)', 'step1\n(카테고리)', 'step2\n(월별요약)',
               'step3\n(예산한도)', 'step4\n(수정기능)', 'step5\n(아카이브)']

# ════════════════════════════════════════════════════
# Fig 1 — 연구 개요 (개념도)
# ════════════════════════════════════════════════════
fig1, ax = plt.subplots(figsize=(14, 5))
ax.set_xlim(0, 14); ax.set_ylim(0, 5)
ax.axis('off'); fig1.patch.set_facecolor(C_BG); ax.set_facecolor(C_BG)
ax.set_title('실험 개요: 설계 의도 드리프트 측정 프레임워크', fontsize=15, fontweight='bold', pad=15)

steps_def = [
    (1.2, '초기 설계 의도\n명시 (step0)',     '#FFE5CC', '#E07B54'),
    (3.8, '기능 추가\n(step1~3)',             '#E8F4FD', '#4A90D9'),
    (6.6, '의도 충돌\n(step4: 수정기능)',     '#FDECEA', '#D95B5B'),
    (9.4, '의도 충돌\n(step5: 아카이브)',     '#FDECEA', '#D95B5B'),
    (12.2,'DRIFT_PROBE\n측정',               '#E8F5E9', '#5BAD6F'),
]
for x, label, fc, ec in steps_def:
    rect = mpatches.FancyBboxPatch((x-1.1, 1.6), 2.2, 1.9,
        boxstyle="round,pad=0.1", facecolor=fc, edgecolor=ec, linewidth=2)
    ax.add_patch(rect)
    ax.text(x, 2.55, label, ha='center', va='center', fontsize=10, fontweight='bold', color='#333')
for i in range(len(steps_def)-1):
    x1 = steps_def[i][0]+1.1; x2 = steps_def[i+1][0]-1.1
    ax.annotate('', xy=(x2,2.55), xytext=(x1,2.55),
                arrowprops=dict(arrowstyle='->', color='#888', lw=2))
ax.text(7.0, 0.8,
    '"감사 추적(Audit Trail): 거래 삭제/직접수정 불가"  -  step0에서만 명시, 이후 단계에서 언급 없음',
    ha='center', fontsize=10, color='#555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFFDE7', edgecolor='#FBC02D', alpha=0.8))
ax.text(6.6, 4.0, '[충돌]', ha='center', fontsize=9, color=C_FAIL, fontweight='bold')
ax.text(9.4, 4.0, '[충돌]', ha='center', fontsize=9, color=C_FAIL, fontweight='bold')
plt.tight_layout()
plt.savefig('results/fig1_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print('fig1 완료')

# ════════════════════════════════════════════════════
# Fig 2 — 단계별 점수 3-way 라인차트
# ════════════════════════════════════════════════════
fig2, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
fig2.suptitle('BudgetTracker 단계별 점수 변화 (7b 모델, 5회 반복)', fontsize=13, fontweight='bold')
fig2.patch.set_facecolor(C_BG)

for ax_i, (agent_key, label, color) in enumerate(AGENTS):
    ax = axes[ax_i]
    ax.set_facecolor(C_BG)
    ax.grid(True, color=C_GRID, linewidth=0.8, zorder=0)

    runs = raw.get(agent_key, [])
    all_scores = [r['scores'] for r in runs if r.get('scores')]

    for s in all_scores:
        ax.plot(range(len(s)), s, color=color, alpha=0.2, linewidth=1.2, zorder=2)

    if all_scores:
        maxl = max(len(s) for s in all_scores)
        avg = [np.mean([s[i] for s in all_scores if len(s)>i]) for i in range(maxl)]
        ax.plot(range(len(avg)), avg, color=color, linewidth=3,
                marker='o', markersize=7, zorder=3, label='평균')
        final_mean = np.mean([s[-1] for s in all_scores])
        ax.axhline(final_mean, color=color, linewidth=1.2, linestyle='--', alpha=0.5)
        ax.text(5.05, final_mean+0.2, f'μ={final_mean:.1f}', fontsize=8, color=color, fontweight='bold')

    ax.axvspan(3.5, 5.5, alpha=0.07, color=C_FAIL, zorder=1)
    ax.text(4.5, 0.4, '충돌 구간', ha='center', fontsize=8, color=C_FAIL, style='italic')

    ax.set_title(label, fontsize=11, fontweight='bold', color=color)
    ax.set_xticks(range(6)); ax.set_xticklabels(STEP_LABELS, fontsize=7.5)
    ax.set_ylim(-0.5, 11.5); ax.set_ylabel('점수 (0~10)', fontsize=9)

plt.tight_layout()
plt.savefig('results/fig2_step_scores.png', dpi=150, bbox_inches='tight')
plt.close()
print('fig2 완료')

# ════════════════════════════════════════════════════
# Fig 3 — DRIFT_PROBE 통과율 3-way 막대차트
# ════════════════════════════════════════════════════
fig3, ax = plt.subplots(figsize=(13, 6))
fig3.patch.set_facecolor(C_BG); ax.set_facecolor(C_BG)
ax.grid(True, color=C_GRID, linewidth=0.8, axis='y', zorder=0)

# 실험 결과 집계
probe_results = {
    'baseline':    {'archive': 2, 'cancel': 2, 'update': 0, 'total': 5},
    'semantic_v2': {'archive': 0, 'cancel': 4, 'update': 0, 'total': 5},
    'semantic_v3': {'archive': 3, 'cancel': 3, 'update': 1, 'total': 5},
}

probe_labels = ['archive_not_delete\n(부재 계약: 삭제 금지)',
                'cancel_no_delete\n(부재 계약: 취소=보존)',
                'update_preserves_original\n(부재 계약: 원본 보존)']
x = np.arange(3); width = 0.25

for i, (agent_key, label, color) in enumerate(AGENTS):
    d = probe_results[agent_key]
    vals = [d['archive']/d['total']*100,
            d['cancel']/d['total']*100,
            d['update']/d['total']*100]
    bars = ax.bar(x + (i-1)*width, vals, width,
                  label=label.replace('\n(히스토리+Verifier)',''),
                  color=color, alpha=0.85, zorder=3)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, v+2,
                f'{v:.0f}%', ha='center', va='bottom', fontsize=9,
                fontweight='bold', color=color)

ax.set_xticks(x); ax.set_xticklabels(probe_labels, fontsize=10)
ax.set_ylim(0, 120); ax.set_ylabel('DRIFT_PROBE 통과율 (%)', fontsize=11)
ax.set_title('부재 계약(Absence Contract) 보존율 비교\n'
             'V3(히스토리+Verifier)가 archive 계약 보존에서 V2 대비 개선',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=11)

ax.annotate('V2: AST 재추출로\n부재 계약 소실 (0%)',
            xy=(0+width, 2), xytext=(0.6, 35),
            fontsize=8.5, color=C_V2,
            arrowprops=dict(arrowstyle='->', color=C_V2, lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#EEF6FF', edgecolor=C_V2))
ax.annotate('V3: pinned 계약으로\n보존 (60%)',
            xy=(0+2*width, 60), xytext=(1.0, 80),
            fontsize=8.5, color=C_V3,
            arrowprops=dict(arrowstyle='->', color=C_V3, lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F3EEF9', edgecolor=C_V3))

plt.tight_layout()
plt.savefig('results/fig3_drift_probe.png', dpi=150, bbox_inches='tight')
plt.close()
print('fig3 완료')

# ════════════════════════════════════════════════════
# Fig 4 — 계약 유형 분류 (이론)
# ════════════════════════════════════════════════════
fig4, ax = plt.subplots(figsize=(13, 5))
ax.set_xlim(0, 13); ax.set_ylim(0, 5)
ax.axis('off'); fig4.patch.set_facecolor(C_BG); ax.set_facecolor(C_BG)
ax.set_title('행동 계약 유형 분류 및 드리프트 취약성 (이론적 기여)', fontsize=13, fontweight='bold')

ax.annotate('', xy=(12.5,2.5), xytext=(0.5,2.5),
            arrowprops=dict(arrowstyle='->', color='#888', lw=2.5))
ax.text(6.5, 0.25, '<-- 안정                                                              취약 -->',
        ha='center', fontsize=9, color='#888')

contracts = [
    (1.5, 'Type 계약',    'price: float',        '#E8F5E9','#5BAD6F', 'AST 추출\n가능', 95),
    (4.2, 'Numeric 계약', 'total=price*qty',      '#E8F4FD','#4A90D9', 'AST 부분\n추출', 75),
    (7.0, 'State 계약',   'PENDING→CONFIRMED\n→SHIPPED', '#FFF8E1','#F9A825', '상태 전이\n추출 가능', 50),
    (10.5,'Absence 계약', '"삭제 금지"\n"덮어쓰기 금지"', '#FDECEA','#D95B5B', 'AST에 없음\n추출 불가', 15),
]
for x, ctype, ex, fc, ec, note, pct in contracts:
    rect = mpatches.FancyBboxPatch((x-1.25, 1.3), 2.5, 2.5,
        boxstyle="round,pad=0.15", facecolor=fc, edgecolor=ec, linewidth=2.5, zorder=2)
    ax.add_patch(rect)
    ax.text(x, 3.3, ctype, ha='center', va='center', fontsize=10, fontweight='bold', color='#333')
    ax.text(x, 2.55, ex, ha='center', va='center', fontsize=8.5, color='#555', style='italic')
    # 보존율 바
    rect_bg = mpatches.Rectangle((x-1.05, 1.35), 2.1, 0.38, color='#E0E0E0', zorder=3)
    rect_fg = mpatches.Rectangle((x-1.05, 1.35), 2.1*(pct/100), 0.38, color=ec, alpha=0.75, zorder=4)
    ax.add_patch(rect_bg); ax.add_patch(rect_fg)
    ax.text(x, 1.54, f'{pct}%', ha='center', fontsize=7.5, color='#333', fontweight='bold', zorder=5)
    ax.text(x, 0.75, note, ha='center', fontsize=7.5, color='#666')

ax.annotate('이번 실험 핵심 발견\n(V2 vs V3 차이 구간)',
            xy=(10.5, 1.2), xytext=(8.5, 0.2),
            fontsize=8, color=C_FAIL, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=C_FAIL, lw=1.5))

plt.tight_layout()
plt.savefig('results/fig4_contract_taxonomy.png', dpi=150, bbox_inches='tight')
plt.close()
print('fig4 완료')

# ════════════════════════════════════════════════════
# Fig 5 — 종합 요약 (논문 메인 그림)
# ════════════════════════════════════════════════════
fig5 = plt.figure(figsize=(16, 9))
fig5.patch.set_facecolor(C_BG)
fig5.suptitle('실험 결과 종합 (BudgetTracker 시나리오 · 7b · 5회)\n'
              '핵심 발견: 부재 계약은 V2(AST 덮어쓰기)에서 소실 → V3(히스토리+Verifier)에서 부분 회복',
              fontsize=13, fontweight='bold')
gs = gridspec.GridSpec(2, 3, figure=fig5, hspace=0.5, wspace=0.35)

# (A) 최종 점수 박스플롯
ax_a = fig5.add_subplot(gs[0, 0])
ax_a.set_facecolor(C_BG)
ax_a.grid(True, color=C_GRID, linewidth=0.8, axis='y', zorder=0)

final_data = []
for agent_key, label, color in AGENTS:
    runs = raw.get(agent_key, [])
    all_scores = [r['scores'] for r in runs if r.get('scores')]
    final_data.append([s[-1] for s in all_scores])

colors_box = [C_BASE, C_V2, C_V3]
bp = ax_a.boxplot(final_data, patch_artist=True, widths=0.5,
                  medianprops=dict(color='white', linewidth=2.5), zorder=3)
for box, c in zip(bp['boxes'], colors_box):
    box.set_facecolor(c)
for w in bp['whiskers']+bp['caps']:
    w.set_color('#888')
for flier in bp['fliers']:
    flier.set(marker='o', markerfacecolor='#888', markersize=5)

ax_a.set_xticks([1,2,3])
ax_a.set_xticklabels(['Baseline','V2','V3'], fontsize=9)
ax_a.set_ylabel('step5 최종 점수', fontsize=9)
ax_a.set_title('(A) 최종 점수 분포', fontsize=10, fontweight='bold')
ax_a.set_ylim(-1, 12)
for i, (d, c) in enumerate(zip(final_data, colors_box)):
    ax_a.text(i+1, np.mean(d)+0.4, f'μ={np.mean(d):.1f}',
              ha='center', fontsize=8, color=c, fontweight='bold')

# (B) 드리프트 분포
ax_b = fig5.add_subplot(gs[0, 1])
ax_b.set_facecolor(C_BG)
ax_b.grid(True, color=C_GRID, linewidth=0.8, axis='y', zorder=0)

drift_data = []
for agent_key, _, _ in AGENTS:
    runs = raw.get(agent_key, [])
    drift_data.append([r['drift_rate'] for r in runs])

bp2 = ax_b.boxplot(drift_data, patch_artist=True, widths=0.5,
                   medianprops=dict(color='white', linewidth=2.5), zorder=3)
for box, c in zip(bp2['boxes'], colors_box):
    box.set_facecolor(c)
for w in bp2['whiskers']+bp2['caps']:
    w.set_color('#888')
ax_b.set_xticks([1,2,3])
ax_b.set_xticklabels(['Baseline','V2','V3'], fontsize=9)
ax_b.set_ylabel('드리프트 점수 (클수록 나쁨)', fontsize=9)
ax_b.set_title('(B) 드리프트율 분포\nV3 분산 큼 = Verifier 불안정성', fontsize=10, fontweight='bold')
for i, (d, c) in enumerate(zip(drift_data, colors_box)):
    ax_b.text(i+1, np.mean(d)+0.3, f'μ={np.mean(d):.1f}',
              ha='center', fontsize=8, color=c, fontweight='bold')

# (C) 단계별 평균 라인
ax_c = fig5.add_subplot(gs[0, 2])
ax_c.set_facecolor(C_BG)
ax_c.grid(True, color=C_GRID, linewidth=0.8, zorder=0)
for agent_key, label, color in AGENTS:
    all_scores = [r['scores'] for r in raw.get(agent_key,[]) if r.get('scores')]
    if not all_scores: continue
    maxl = max(len(s) for s in all_scores)
    avg = [np.mean([s[i] for s in all_scores if len(s)>i]) for i in range(maxl)]
    short_label = label.split('\n')[0]
    ax_c.plot(range(len(avg)), avg, color=color, linewidth=2.5,
              marker='o', markersize=6, label=short_label, zorder=3)
ax_c.axvspan(3.5, 5.5, alpha=0.07, color=C_FAIL, zorder=1)
ax_c.set_xticks(range(6)); ax_c.set_xticklabels([f's{i}' for i in range(6)], fontsize=8)
ax_c.set_ylim(0, 11.5); ax_c.set_ylabel('평균 점수', fontsize=9)
ax_c.set_title('(C) 단계별 평균 점수', fontsize=10, fontweight='bold')
ax_c.legend(fontsize=8, loc='lower left')

# (D) DRIFT_PROBE 히트맵
ax_d = fig5.add_subplot(gs[1, :])
ax_d.set_facecolor(C_BG)

probe_matrix = np.array([
    [40,  40,  0],   # Baseline
    [0,   80,  0],   # SemanticV2
    [60,  60,  20],  # SemanticV3
])
# 행=에이전트, 열=계약

im = ax_d.imshow(probe_matrix, cmap='RdYlGn', vmin=0, vmax=100, aspect='auto', zorder=2)

ax_d.set_yticks([0,1,2])
ax_d.set_yticklabels(['Baseline','SemanticV2','SemanticV3\n(히스토리+Verifier)'],
                      fontsize=10, fontweight='bold')
ax_d.set_xticks([0,1,2])
ax_d.set_xticklabels([
    'archive_not_delete\n(부재 계약: 삭제 금지)',
    'cancel_no_delete\n(부재 계약: 취소=보존)',
    'update_preserves_original\n(부재 계약: 원본 보존)'
], fontsize=10)
ax_d.set_title('(D) DRIFT_PROBE 부재 계약 통과율 히트맵 (%)',
               fontsize=11, fontweight='bold')

for i in range(3):
    for j in range(3):
        v = probe_matrix[i, j]
        tc = 'white' if v < 35 or v > 75 else 'black'
        ax_d.text(j, i, f'{v}%', ha='center', va='center',
                  fontsize=13, fontweight='bold', color=tc, zorder=3)

# V2 0% 강조 박스
ax_d.add_patch(plt.Rectangle((-0.5, 0.5), 1, 1,
    fill=False, edgecolor=C_FAIL, linewidth=3, zorder=4))
ax_d.text(0, 1.62, 'AST 재추출로 소실', ha='center', fontsize=8.5,
          color=C_FAIL, fontweight='bold')

# V3 개선 강조 박스
ax_d.add_patch(plt.Rectangle((-0.5, 1.5), 2, 1,
    fill=False, edgecolor=C_V3, linewidth=3, zorder=4))
ax_d.text(0.5, 2.62, 'pinned 히스토리로 개선', ha='center', fontsize=8.5,
          color=C_V3, fontweight='bold')

plt.colorbar(im, ax=ax_d, orientation='vertical', label='통과율 (%)', shrink=0.8)
plt.savefig('results/fig5_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print('fig5 완료')

# ════════════════════════════════════════════════════
# Fig 6 — V3 Verifier 작동 원리 (신규)
# ════════════════════════════════════════════════════
fig6, ax = plt.subplots(figsize=(14, 6))
ax.set_xlim(0, 14); ax.set_ylim(0, 6)
ax.axis('off'); fig6.patch.set_facecolor(C_BG); ax.set_facecolor(C_BG)
ax.set_title('SemanticCompressorV3: 계약 히스토리 + Verifier 구조', fontsize=13, fontweight='bold')

# 저장소 박스
stores = [
    (2.0, 4.5, 2.5, 0.9, '[PINNED]\n부재 계약\n(절대 보존)', '#FDECEA', '#D95B5B'),
    (2.0, 3.2, 2.5, 0.9, '[ACTIVE]\n현재 유효 계약',          '#E8F4FD', '#4A90D9'),
    (2.0, 1.9, 2.5, 0.9, '[ARCHIVED]\n축약된 이전 계약',      '#F5F5F5', '#9E9E9E'),
]
for x, y, w, h, label, fc, ec in stores:
    rect = mpatches.FancyBboxPatch((x-w/2, y), w, h,
        boxstyle="round,pad=0.1", facecolor=fc, edgecolor=ec, linewidth=2, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y+h/2, label, ha='center', va='center',
            fontsize=9, fontweight='bold', color='#333')

ax.text(2.0, 1.4, 'Contract Store', ha='center', fontsize=10,
        fontweight='bold', color='#333')
rect_store = mpatches.FancyBboxPatch((0.6, 1.7), 2.8, 3.9,
    boxstyle="round,pad=0.2", fill=False, edgecolor='#888', linewidth=1.5, linestyle='--')
ax.add_patch(rect_store)

# Coder
coder_rect = mpatches.FancyBboxPatch((5.5, 3.0), 2.5, 1.5,
    boxstyle="round,pad=0.15", facecolor='#E8F5E9', edgecolor='#5BAD6F', linewidth=2, zorder=2)
ax.add_patch(coder_rect)
ax.text(6.75, 3.75, 'Coder LLM\n계약 참조 후\n코드 수정', ha='center', va='center',
        fontsize=9, fontweight='bold', color='#333')

# Verifier
ver_rect = mpatches.FancyBboxPatch((5.5, 1.0), 2.5, 1.5,
    boxstyle="round,pad=0.15", facecolor='#FFF8E1', edgecolor='#F9A825', linewidth=2, zorder=2)
ax.add_patch(ver_rect)
ax.text(6.75, 1.75, 'Verifier LLM\nKEEP/UPDATE\n/ARCHIVE 판정', ha='center', va='center',
        fontsize=9, fontweight='bold', color='#333')

# 판정 결과
verdicts = [
    (10.5, 4.6, 'KEEP',    '#E8F5E9', '#5BAD6F', '계약 유지'),
    (10.5, 3.5, 'UPDATE',  '#FFF8E1', '#F9A825', '내용 교체'),
    (10.5, 2.4, 'ARCHIVE', '#F5F5F5', '#9E9E9E', '축약 보관'),
    (10.5, 1.3, 'PINNED\n강제 KEEP', '#FDECEA', '#D95B5B', '절대 보존'),
]
for x, y, label, fc, ec, desc in verdicts:
    rect = mpatches.FancyBboxPatch((x-1.1, y), 2.2, 0.7,
        boxstyle="round,pad=0.1", facecolor=fc, edgecolor=ec, linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y+0.35, label, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#333')

ax.text(10.5, 0.9, '판정 결과', ha='center', fontsize=9, fontweight='bold', color='#555')

# 화살표
arrows = [
    ((3.35, 3.95), (5.5, 3.75)),   # Store → Coder
    ((5.5, 3.0),   (3.35, 3.2)),   # Coder → Store (수정 코드)
    ((6.75, 3.0),  (6.75, 2.5)),   # Coder → Verifier
    ((8.0, 1.75),  (9.4, 4.0)),    # Verifier → KEEP
    ((8.0, 1.75),  (9.4, 3.5)),    # Verifier → UPDATE
    ((8.0, 1.75),  (9.4, 2.4)),    # Verifier → ARCHIVE
    ((8.0, 1.75),  (9.4, 1.65)),   # Verifier → PINNED
]
for (x1,y1),(x2,y2) in arrows:
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle='->', color='#888', lw=1.5))

# 핵심 특징
ax.text(12.5, 5.2, '핵심:', ha='center', fontsize=9, fontweight='bold', color='#333')
ax.text(12.5, 4.8, 'PINNED 계약은\nVerifier도 제거 불가', ha='center', fontsize=8.5,
        color='#D95B5B', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDECEA', edgecolor='#D95B5B'))

plt.tight_layout()
plt.savefig('results/fig6_v3_architecture.png', dpi=150, bbox_inches='tight')
plt.close()
print('fig6 완료')

print('\n저장 완료:')
for i, name in enumerate(['fig1_overview', 'fig2_step_scores', 'fig3_drift_probe',
                           'fig4_contract_taxonomy', 'fig5_summary', 'fig6_v3_architecture'], 1):
    print(f'  results/{name}.png')
