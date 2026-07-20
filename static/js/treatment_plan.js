(function() {
    const modalEl = document.getElementById('treatmentPlanModal');
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);
    const loadingEl = document.getElementById('treatmentPlanLoading');
    const contentEl = document.getElementById('treatmentPlanContent');
    const errorEl = document.getElementById('treatmentPlanError');
    const errorText = document.getElementById('treatmentPlanErrorText');
    const footerEl = document.getElementById('treatmentPlanFooter');
    const createBtn = document.getElementById('treatmentPlanCreateBtn');
    const regenerateBtn = document.getElementById('treatmentPlanRegenerateBtn');
    const retryBtn = document.getElementById('retryGeneratePlan');
    const planMeta = document.getElementById('treatmentPlanMeta');
    const emptyEl = document.getElementById('treatmentPlanEmpty');

    let currentCaseType = null;
    let currentCaseId = null;

    function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function renderPlan(planData) {
        var html = '';
        var iconMap = {
            'تقييم': 'assessment',
            'التقييم': 'assessment',
            'أهداف': 'goals',
            'الأهداف': 'goals',
            'الخطة': 'therapy',
            'توصيات': 'recommendations',
            'متابعة': 'followup',
            'المتابعة': 'followup',
        };
        var faIcons = {
            assessment: 'clipboard-list',
            goals: 'bullseye',
            therapy: 'notes-medical',
            recommendations: 'lightbulb',
            followup: 'calendar-check',
        };

        (planData.sections || []).forEach(function(section) {
            var iconKey = 'assessment';
            Object.keys(iconMap).forEach(function(k) {
                if (section.title && section.title.includes(k)) iconKey = iconMap[k];
            });
            var faIcon = faIcons[iconKey] || 'clipboard-list';

            html += '<div class="plan-section-card">';
            html += '<div class="plan-section-header">';
            html += '<div class="plan-section-icon ' + iconKey + '">';
            html += '<i class="fa-solid fa-' + faIcon + '"></i></div>';
            html += '<h6 class="plan-section-title">' + (section.title || '') + '</h6></div>';
            if (section.content) {
                html += '<div class="plan-section-content">' + section.content + '</div>';
            }
            if (section.steps && section.steps.length > 0) {
                html += '<ul class="plan-steps">';
                section.steps.forEach(function(step) {
                    html += '<li class="plan-step">';
                    html += '<span class="plan-step-icon"><i class="fa-solid fa-check"></i></span>';
                    html += '<span class="plan-step-text">' + step + '</span></li>';
                });
                html += '</ul>';
            }
            html += '</div>';
        });
        return html;
    }

    function showPlanView(planData, meta) {
        loadingEl.style.display = 'none';
        errorEl.style.display = 'none';
        emptyEl.style.display = 'none';
        contentEl.innerHTML = renderPlan(planData);
        contentEl.style.display = 'block';

        if (meta) {
            planMeta.textContent = 'آخر تحديث: ' + (meta.created_by || '') + ' - ' + (meta.created_at ? new Date(meta.created_at).toLocaleDateString('ar-DZ') : '');
            planMeta.style.display = 'block';
        } else {
            planMeta.style.display = 'none';
        }

        createBtn.style.display = 'none';
        regenerateBtn.style.display = 'inline-flex';
        footerEl.style.display = 'flex';
    }

    function showEmptyView() {
        loadingEl.style.display = 'none';
        errorEl.style.display = 'none';
        contentEl.style.display = 'none';
        planMeta.style.display = 'none';
        emptyEl.style.display = 'block';
        createBtn.style.display = 'inline-flex';
        regenerateBtn.style.display = 'none';
        footerEl.style.display = 'flex';
    }

    function showLoading() {
        loadingEl.style.display = 'block';
        contentEl.style.display = 'none';
        errorEl.style.display = 'none';
        emptyEl.style.display = 'none';
        createBtn.style.display = 'none';
        regenerateBtn.style.display = 'none';
        footerEl.style.display = 'none';
        planMeta.style.display = 'none';
    }

    function showError(msg) {
        loadingEl.style.display = 'none';
        contentEl.style.display = 'none';
        emptyEl.style.display = 'none';
        createBtn.style.display = 'none';
        regenerateBtn.style.display = 'none';
        errorText.textContent = msg || 'حدث خطأ غير متوقع';
        errorEl.style.display = 'block';
        footerEl.style.display = 'flex';
    }

    function doGenerate(caseType, caseId) {
        showLoading();
        fetch('/dashboard/treatment-plans/generate/' + caseType + '/' + caseId + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success && data.plan_data) {
                    showPlanView(data.plan_data, {
                        created_by: '',
                        created_at: new Date().toISOString(),
                    });
                } else {
                    showError(data.errors ? data.errors.join('\n') : 'فشل في إنشاء الخطة العلاجية');
                }
            })
            .catch(function() {
                showError('حدث خطأ في الاتصال بالخادم');
            });
    }

    function openPlan(caseType, caseId) {
        currentCaseType = caseType;
        currentCaseId = caseId;
        showLoading();
        modal.show();

        fetch('/dashboard/treatment-plans/get/' + caseType + '/' + caseId + '/')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success && data.plan_data) {
                    showPlanView(data.plan_data, data);
                } else {
                    showEmptyView();
                }
            })
            .catch(function() {
                showEmptyView();
            });
    }

    // Event listeners
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('.btn-treatment-plan');
        if (btn) {
            openPlan(btn.dataset.caseType, btn.dataset.caseId);
        }
    });

    createBtn.addEventListener('click', function() {
        if (currentCaseType && currentCaseId) {
            doGenerate(currentCaseType, currentCaseId);
        }
    });

    regenerateBtn.addEventListener('click', function() {
        if (currentCaseType && currentCaseId) {
            doGenerate(currentCaseType, currentCaseId);
        }
    });

    retryBtn.addEventListener('click', function() {
        if (currentCaseType && currentCaseId) {
            doGenerate(currentCaseType, currentCaseId);
        }
    });
})();
