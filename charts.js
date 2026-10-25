/**
 * FinWise AI - Chart.js Visualizations
 * Category Doughnut Chart & 6-Month Income vs Expense Trend Bar Chart
 */

let categoryChartInstance = null;
let trendChartInstance = null;

const FINTECH_COLORS = [
  '#f59e0b', '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899',
  '#f43f5e', '#a855f7', '#eab308', '#10b981', '#06b6d4',
  '#14b8a6', '#f97316', '#64748b'
];

function getThemeFontColor() {
  const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
  return isDark ? '#94a3b8' : '#64748b';
}

function getThemeGridColor() {
  const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
  return isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
}

function initCategoryChart(labels, values, currencySymbol = '₹') {
  const ctx = document.getElementById('categoryChart');
  if (!ctx) return;

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  if (!values || values.length === 0 || values.every(v => v === 0)) {
    // Show empty chart state
    ctx.parentElement.innerHTML = `
      <div class="text-center py-5 text-muted">
        <i class="bi bi-pie-chart fs-1 opacity-50 mb-2 d-block"></i>
        <p class="mb-0">No expenses recorded for this month.</p>
      </div>`;
    return;
  }

  categoryChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: FINTECH_COLORS.slice(0, labels.length),
        borderWidth: 2,
        borderColor: document.documentElement.getAttribute('data-bs-theme') === 'dark' ? '#151c2c' : '#ffffff',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: getThemeFontColor(),
            font: { family: 'Inter', size: 12 },
            boxWidth: 12,
            padding: 14
          }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const val = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
              return ` ${context.label}: ${currencySymbol}${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })} (${pct}%)`;
            }
          }
        }
      },
      cutout: '68%'
    }
  });
}

function initTrendChart(labels, incomeData, expenseData, currencySymbol = '₹') {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Income',
          data: incomeData,
          backgroundColor: '#10b981',
          borderRadius: 6,
          barPercentage: 0.65,
          categoryPercentage: 0.7
        },
        {
          label: 'Expenses',
          data: expenseData,
          backgroundColor: '#ef4444',
          borderRadius: 6,
          barPercentage: 0.65,
          categoryPercentage: 0.7
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: getThemeFontColor(), font: { family: 'Inter', size: 11 } }
        },
        y: {
          grid: { color: getThemeGridColor() },
          ticks: {
            color: getThemeFontColor(),
            font: { family: 'Inter', size: 11 },
            callback: function (val) {
              return currencySymbol + (val >= 1000 ? (val / 1000).toFixed(0) + 'k' : val);
            }
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            color: getThemeFontColor(),
            font: { family: 'Inter', size: 12 },
            usePointStyle: true,
            boxWidth: 8
          }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return ` ${context.dataset.label}: ${currencySymbol}${context.raw.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            }
          }
        }
      }
    }
  });
}

// React to theme changes
window.onFinWiseThemeChange = function () {
  if (categoryChartInstance) {
    categoryChartInstance.options.plugins.legend.labels.color = getThemeFontColor();
    categoryChartInstance.update();
  }
  if (trendChartInstance) {
    trendChartInstance.options.scales.x.ticks.color = getThemeFontColor();
    trendChartInstance.options.scales.y.ticks.color = getThemeFontColor();
    trendChartInstance.options.scales.y.grid.color = getThemeGridColor();
    trendChartInstance.options.plugins.legend.labels.color = getThemeFontColor();
    trendChartInstance.update();
  }
};
