let currentData = null;
let currentFilter = 'all';

// ── Format Indian Rupees ─────────────────────────────────────
function formatINR(amount) {
  return '₹' + Math.round(amount).toLocaleString('en-IN');
}

// ── Animate number counting up ───────────────────────────────
function animateCount(elementId, targetValue, prefix = '₹') {
  const el = document.getElementById(elementId);
  const duration = 1000;
  const steps = 40;
  const increment = targetValue / steps;
  let current = 0;
  let step = 0;

  const timer = setInterval(() => {
    step++;
    current += increment;
    if (step >= steps) {
      current = targetValue;
      clearInterval(timer);
    }
    el.textContent = prefix + Math.round(current).toLocaleString('en-IN');
  }, duration / steps);
}

// ── Slab toggle ──────────────────────────────────────────────
function showSlab(type, btn) {
  document.getElementById('slab-new').classList.add('hidden');
  document.getElementById('slab-old').classList.add('hidden');
  document.getElementById('slab-' + type).classList.remove('hidden');
  document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

// ── Range filter ─────────────────────────────────────────────
function filterRange(type, btn) {
  currentFilter = type;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (currentData) renderRangeTable(currentData.range_data, currentData.income);
}

// ── Render breakdown bars ────────────────────────────────────
function renderBreakdownBars(data) {
  const container = document.getElementById('breakdown-bars');

  const newTakeHomePct = ((data.take_home_new / data.income) * 100).toFixed(1);
  const newTaxPct      = ((data.new_tax / data.income) * 100).toFixed(1);
  const oldTakeHomePct = ((data.take_home_old / data.income) * 100).toFixed(1);
  const oldTaxPct      = ((data.old_tax / data.income) * 100).toFixed(1);

  container.innerHTML = `
    <div class="bar-row">
      <div class="bar-label">
        <span>New Regime</span>
        <span>${formatINR(data.take_home_new)} take home · ${formatINR(data.new_tax)} tax</span>
      </div>
      <div class="bar-track">
        <div class="bar-take" style="width:${newTakeHomePct}%"></div>
        <div class="bar-tax"  style="width:${newTaxPct}%"></div>
      </div>
    </div>
    <div class="bar-row">
      <div class="bar-label">
        <span>Old Regime</span>
        <span>${formatINR(data.take_home_old)} take home · ${formatINR(data.old_tax)} tax</span>
      </div>
      <div class="bar-track">
        <div class="bar-take" style="width:${oldTakeHomePct}%"></div>
        <div class="bar-tax"  style="width:${oldTaxPct}%"></div>
      </div>
    </div>
  `;
}

// ── Render range table ───────────────────────────────────────
function renderRangeTable(rangeData, currentIncome) {
  const showNew = currentFilter !== 'old';
  const showOld = currentFilter !== 'new';

  let headers = '<th>Annual Income</th>';
  if (showNew) headers += '<th>New Regime Tax</th>';
  if (showOld) headers += '<th>Old Regime Tax</th>';

  let rows = rangeData.map(r => {
    const isCurrent = r.income === Math.round(currentIncome);
    let row = `<tr class="${isCurrent ? 'current-row' : ''}">
      <td>${formatINR(r.income)} ${isCurrent ? '← You' : ''}</td>`;
    if (showNew) row += `<td>${formatINR(r.new_tax)}</td>`;
    if (showOld) row += `<td>${formatINR(r.old_tax)}</td>`;
    row += '</tr>';
    return row;
  }).join('');

  document.getElementById('range-table-container').innerHTML = `
    <table class="range-table">
      <tr>${headers}</tr>
      ${rows}
    </table>
  `;
}

// ── Main calculate function ──────────────────────────────────
async function calculate() {
  const income = document.getElementById('income').value;

  if (!income || parseFloat(income) <= 0) {
    alert('Please enter a valid income!');
    return;
  }

  const btn = document.querySelector('.btn-primary');
  btn.textContent = 'Calculating...';
  btn.disabled = true;

  const payload = {
    income:  parseFloat(income),
    sec80c:  parseFloat(document.getElementById('sec80c').value) || 0,
    sec80d:  parseFloat(document.getElementById('sec80d').value) || 0,
    hra:     parseFloat(document.getElementById('hra').value)    || 0,
  };

  try {
    const response = await fetch('/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    currentData = data;
    displayResults(data);
  } catch (err) {
    alert('Something went wrong. Please try again.');
  } finally {
    btn.textContent = 'Calculate Tax →';
    btn.disabled = false;
  }
}

// ── Display results ──────────────────────────────────────────
function displayResults(data) {
  document.getElementById('empty-state').classList.add('hidden');
  document.getElementById('results').classList.remove('hidden');

  // Animated counters
  animateCount('new-tax',       data.new_tax);
  animateCount('old-tax',       data.old_tax);
  animateCount('take-home-new', data.take_home_new);
  animateCount('take-home-old', data.take_home_old);

  // Regime banner
  const banner = document.getElementById('regime-banner');
  if (data.better_regime === 'New Regime') {
    banner.className = 'regime-banner banner-new';
    banner.innerHTML = `✅ New Regime is better — saves you ${formatINR(data.savings)} vs Old Regime`;
  } else {
    banner.className = 'regime-banner banner-old';
    banner.innerHTML = `✅ Old Regime is better — saves you ${formatINR(data.savings)} vs New Regime`;
  }

  // Breakdown bars
  renderBreakdownBars(data);

  // Range table
  renderRangeTable(data.range_data, data.income);

  // Tips
  const tipsList = document.getElementById('tips-list');
  tipsList.innerHTML = '';
  data.tips.forEach(tip => {
    const li = document.createElement('li');
    li.textContent = '💡 ' + tip;
    tipsList.appendChild(li);
  });

  // Smooth scroll
  document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}