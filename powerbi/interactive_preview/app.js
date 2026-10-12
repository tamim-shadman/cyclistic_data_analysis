/**
 * Cyclistic Bike-Share Analytics — Lead BI Architect Application Engine
 * Supports 6-page navigation, Leaflet Chicago map, Chart.js visualizations,
 * 2D sensitivity matrix, and dynamic What-If parameter modeling.
 */

const state = {
  activePage: 'page1',
  darkMode: false,
  sidebarCollapsed: false,
  filters: {
    userType: 'all',
    dayType: 'all',
    bikeType: 'all',
    season: 'all'
  },
  whatIf: {
    conversionRate: 0.07,
    membershipFee: 119
  },
  selectedStation: null
};

// Registered chart instances
const charts = {};
let leafletMap = null;
let stationMarkers = [];

// Color constants
const THEME = {
  member: '#1d4ed8',
  memberHover: '#1e40af',
  memberLight: '#93c5fd',
  casual: '#ea580c',
  casualHover: '#c2410c',
  casualLight: '#fed7aa',
  teal: '#0d9488',
  indigo: '#4f46e5',
  gold: '#d97706',
  green: '#059669',
  red: '#dc2626',
  grid: '#e2e8f0',
  text: '#64748b'
};

// Station Catalog
const STATIONS = [
  { id: 101, name: "Streeter Dr & Grand Ave (Navy Pier)", lat: 41.892278, lng: -87.612043, volume: 4740, casual: 82.0, net: "+420 (Surplus)", type: "orange" },
  { id: 102, name: "DuSable Lake Shore & Monroe", lat: 41.880958, lng: -87.616743, volume: 4300, casual: 78.0, net: "+290 (Surplus)", type: "orange" },
  { id: 103, name: "Michigan Ave & Oak St (Beach)", lat: 41.900960, lng: -87.623777, volume: 3830, casual: 72.0, net: "+180 (Surplus)", type: "orange" },
  { id: 104, name: "Millennium Park", lat: 41.881032, lng: -87.624084, volume: 3800, casual: 75.0, net: "+210 (Surplus)", type: "orange" },
  { id: 105, name: "Theater on the Lake", lat: 41.926277, lng: -87.630831, volume: 3130, casual: 76.0, net: "+110 (Surplus)", type: "orange" },
  { id: 201, name: "Clinton & Washington (Ogilvie Station)", lat: 41.883380, lng: -87.641170, volume: 4370, casual: 14.0, net: "-440 (Deficit)", type: "blue" },
  { id: 202, name: "Clinton & Madison (Union Station)", lat: 41.882242, lng: -87.641066, volume: 4230, casual: 16.0, net: "-380 (Deficit)", type: "blue" },
  { id: 203, name: "Canal St & Adams St", lat: 41.879255, lng: -87.639904, volume: 3410, casual: 18.0, net: "-260 (Deficit)", type: "blue" },
  { id: 204, name: "Kingsbury St & Kinzie St", lat: 41.889177, lng: -87.638506, volume: 3090, casual: 22.0, net: "-140 (Deficit)", type: "blue" },
  { id: 205, name: "Clark St & Elm St", lat: 41.902973, lng: -87.631280, volume: 3280, casual: 32.0, net: "+40 (Balanced)", type: "blue" },
  { id: 206, name: "Wells St & Concord Ln", lat: 41.912133, lng: -87.634656, volume: 3000, casual: 34.0, net: "+60 (Balanced)", type: "blue" },
  { id: 207, name: "Dearborn St & Adams St (Loop)", lat: 41.879356, lng: -87.629791, volume: 2950, casual: 21.0, net: "-180 (Deficit)", type: "blue" }
];

document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupSidebarToggle();
  setupThemeToggle();
  setupFilters();
  setupWhatIfControls();
  initAllCharts();
  renderHeatmap();
  renderODRoutes();
  renderSensitivityMatrix();

  // Lazy init leaflet when user switches to page 4
  state.selectedStation = STATIONS[0];
});

// --------------------------------------------------------------------------
// 1. PAGE NAVIGATION & HEADERS
// --------------------------------------------------------------------------
const PAGE_TITLES = {
  page1: { title: "Executive Ridership Cockpit", desc: "High-level KPI performance, member-versus-casual distribution, and ridership trajectory." },
  page2: { title: "Rider Personas & Behavioral Segmentation", desc: "Intraday usage patterns, commute spikes, trip duration categories, and machine learning clusters." },
  page3: { title: "Temporal Trends & Seasonality Dynamics", desc: "Monthly seasonality cycles, temperature impact, and 24x7 ridership density heatmap." },
  page4: { title: "Geospatial Station Intelligence & Network Flow", desc: "Interactive Chicago station map, origin-destination corridors, and fleet rebalancing balance." },
  page5: { title: "Strategic Conversion & Financial What-If Simulator", desc: "Interactive scenario modeling to simulate recurring ARR gained from converting prime casual commuters." },
  page6: { title: "Executive Boardroom Briefing & Strategic Storytelling", desc: "C-suite strategic summary, key analytical discoveries, and 4-point commercial action plan." }
};

function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      const targetPage = item.getAttribute('data-page');
      state.activePage = targetPage;

      // Update Header Text
      if (PAGE_TITLES[targetPage]) {
        document.getElementById('pageHeaderTitle').innerText = PAGE_TITLES[targetPage].title;
        document.getElementById('pageHeaderDesc').innerText = PAGE_TITLES[targetPage].desc;
      }

      // Switch Page View
      document.querySelectorAll('.report-page').forEach(p => p.classList.remove('active'));
      const activeEl = document.getElementById(targetPage);
      if (activeEl) {
        activeEl.classList.add('active');
        window.dispatchEvent(new Event('resize'));
      }

      // If page 4, initialize or invalidate leaflet map size
      if (targetPage === 'page4') {
        setTimeout(initLeafletMap, 150);
      }
    });
  });
}

function setupSidebarToggle() {
  const btn = document.getElementById('toggleSidebarBtn');
  const sidebar = document.getElementById('appSidebar');
  btn.addEventListener('click', () => {
    state.sidebarCollapsed = !state.sidebarCollapsed;
    sidebar.classList.toggle('collapsed', state.sidebarCollapsed);
    setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 250);
  });
}

// --------------------------------------------------------------------------
// 2. THEME TOGGLE
// --------------------------------------------------------------------------
function setupThemeToggle() {
  const btn = document.getElementById('themeToggleBtn');
  btn.addEventListener('click', () => {
    state.darkMode = !state.darkMode;
    document.body.classList.toggle('dark-mode', state.darkMode);
    document.body.classList.toggle('light-mode', !state.darkMode);

    THEME.grid = state.darkMode ? '#1f2937' : '#e2e8f0';
    THEME.text = state.darkMode ? '#94a3b8' : '#64748b';

    updateAllCharts();
    if (leafletMap) {
      updateMapTileLayer();
    }
  });
}

// --------------------------------------------------------------------------
// 3. SLICERS, CROSS-FILTERING & CHIPS
// --------------------------------------------------------------------------
function setupFilters() {
  const userSelect = document.getElementById('filterUserType');
  const daySelect = document.getElementById('filterDayType');
  const bikeSelect = document.getElementById('filterBikeType');
  const seasonSelect = document.getElementById('filterSeason');
  const resetBtn = document.getElementById('resetFiltersBtn');

  const onFilterChange = () => {
    state.filters.userType = userSelect.value;
    state.filters.dayType = daySelect.value;
    state.filters.bikeType = bikeSelect.value;
    state.filters.season = seasonSelect.value;

    updateFilterChips();
    recalculateMetrics();
    updateAllCharts();
  };

  userSelect.addEventListener('change', onFilterChange);
  daySelect.addEventListener('change', onFilterChange);
  bikeSelect.addEventListener('change', onFilterChange);
  seasonSelect.addEventListener('change', onFilterChange);

  resetBtn.addEventListener('click', () => {
    userSelect.value = 'all';
    daySelect.value = 'all';
    bikeSelect.value = 'all';
    seasonSelect.value = 'all';
    onFilterChange();
  });
}

function updateFilterChips() {
  const userText = state.filters.userType === 'all' ? 'All' : state.filters.userType === 'member' ? 'Members' : 'Casuals';
  const dayText = state.filters.dayType === 'all' ? 'All Days' : state.filters.dayType === 'weekday' ? 'Weekdays' : 'Weekends';
  const bikeText = state.filters.bikeType === 'all' ? 'All Fleet' : state.filters.bikeType.toUpperCase();
  const seasonText = state.filters.season === 'all' ? '2025' : state.filters.season.toUpperCase();

  document.getElementById('chipUser').innerText = `Rider: ${userText}`;
  document.getElementById('chipDay').innerText = `Day: ${dayText}`;
  document.getElementById('chipBike').innerText = `Fleet: ${bikeText}`;
  document.getElementById('chipSeason').innerText = `Period: ${seasonText}`;
}

function recalculateMetrics() {
  let multiplier = 1.0;
  if (state.filters.season === 'q1') multiplier *= 0.35;
  if (state.filters.season === 'q2') multiplier *= 0.95;
  if (state.filters.season === 'q3') multiplier *= 1.45;
  if (state.filters.season === 'q4') multiplier *= 0.70;

  if (state.filters.dayType === 'weekday') multiplier *= 0.71;
  if (state.filters.dayType === 'weekend') multiplier *= 0.29;

  let memberShare = 0.552;
  let casualShare = 0.448;
  if (state.filters.userType === 'member') {
    memberShare = 1.0;
    casualShare = 0.0;
  } else if (state.filters.userType === 'casual') {
    memberShare = 0.0;
    casualShare = 1.0;
  } else if (state.filters.dayType === 'weekend') {
    memberShare = 0.38;
    casualShare = 0.62;
  } else if (state.filters.dayType === 'weekday') {
    memberShare = 0.68;
    casualShare = 0.32;
  }

  const baseTotal = 61973;
  const filteredTotal = Math.round(baseTotal * multiplier * (state.filters.userType === 'member' ? 0.552 : state.filters.userType === 'casual' ? 0.448 : 1.0));
  const memberCount = Math.round(filteredTotal * memberShare);
  const casualCount = Math.round(filteredTotal * casualShare);
  const primePool = Math.round(11480 * multiplier);

  document.getElementById('valTotalRides').innerText = filteredTotal.toLocaleString();
  document.getElementById('valMemberShare').innerText = memberCount.toLocaleString();
  document.getElementById('valCasualShare').innerText = casualCount.toLocaleString();
  document.getElementById('valPrimeConversion').innerText = primePool.toLocaleString();

  updateWhatIfCalculation();
}

// --------------------------------------------------------------------------
// 4. WHAT-IF PARAMETER SIMULATION & SENSITIVITY MATRIX
// --------------------------------------------------------------------------
function setupWhatIfControls() {
  const rateSlider = document.getElementById('sliderConversionRate');
  const feeSlider = document.getElementById('sliderAnnualFee');

  rateSlider.addEventListener('input', (e) => {
    state.whatIf.conversionRate = parseFloat(e.target.value) / 100;
    document.getElementById('valSliderRate').innerText = `${e.target.value}%`;
    updateWhatIfCalculation();
    renderSensitivityMatrix();
  });

  feeSlider.addEventListener('input', (e) => {
    state.whatIf.membershipFee = parseInt(e.target.value, 10);
    document.getElementById('valSliderFee').innerText = `$${e.target.value} / yr`;
    updateWhatIfCalculation();
    renderSensitivityMatrix();
  });

  updateWhatIfCalculation();
}

function updateWhatIfCalculation() {
  const pool = parseInt(document.getElementById('valPrimeConversion').innerText.replace(/,/g, ''), 10) || 11480;
  const converted = Math.round(pool * state.whatIf.conversionRate);
  const arr = converted * state.whatIf.membershipFee;
  const cannibalization = Math.round(converted * 65); // $65 single-pass casual spend lost
  const netUplift = arr - cannibalization;

  document.getElementById('valSimConverted').innerText = converted.toLocaleString();
  document.getElementById('valSimRevenue').innerText = `$${arr.toLocaleString()}`;
  document.getElementById('valSimCannibal').innerText = `-$${cannibalization.toLocaleString()}`;
  document.getElementById('valSimNetUplift').innerText = `+$${netUplift.toLocaleString()}`;
  document.getElementById('funnelConvertedNum').innerText = `${converted.toLocaleString()} (${(state.whatIf.conversionRate * 100).toFixed(1)}%)`;
}

function renderSensitivityMatrix() {
  const body = document.getElementById('sensitivityMatrixBody');
  if (!body) return;

  const rates = [0.03, 0.05, 0.07, 0.10, 0.15];
  const fees = [89, 109, 119, 139, 159];
  const pool = 11480;

  let html = '';
  rates.forEach(r => {
    const isCurrentRate = Math.abs(r - state.whatIf.conversionRate) < 0.015;
    html += `<tr><td><strong>${(r * 100).toFixed(0)}%</strong></td>`;

    fees.forEach(f => {
      const isCurrentFee = (f === state.whatIf.membershipFee);
      const isSelected = isCurrentRate && isCurrentFee;

      const converted = Math.round(pool * r);
      const net = (converted * f) - (converted * 65);
      const formatted = `+$${Math.round(net / 1000)}k`;

      html += `<td class="${isSelected ? 'selected-cell' : ''}">${formatted}</td>`;
    });

    html += '</tr>';
  });

  body.innerHTML = html;
}

// --------------------------------------------------------------------------
// 5. CHART INITIALIZATION
// --------------------------------------------------------------------------
function initAllCharts() {
  initChartTrendDaily();
  initChartUserSplit();
  initChartTopStations();
  initChartBikeFleet();
  initChartHourlyProfile();
  initChartTripDurationBuckets();
  initChartDayOfWeek();
  initChartMonthlySeasonality();
  initChartNetStationFlow();
}

function updateAllCharts() {
  Object.values(charts).forEach(c => {
    if (c && typeof c.update === 'function') {
      if (c.options.scales) {
        if (c.options.scales.x && c.options.scales.x.ticks) c.options.scales.x.ticks.color = THEME.text;
        if (c.options.scales.y && c.options.scales.y.ticks) c.options.scales.y.ticks.color = THEME.text;
        if (c.options.scales.y && c.options.scales.y.grid) c.options.scales.y.grid.color = THEME.grid;
      }
      c.update();
    }
  });
}

// 5.1 Page 1: Daily Trend with 7-Day MA & Target Line
function initChartTrendDaily() {
  const ctx = document.getElementById('chartTrendDaily').getContext('2d');
  const days = [];
  const observed = [];
  const ma = [];
  const target = [];

  let rolling = 135;
  for (let i = 1; i <= 60; i++) {
    days.push(`Day ${i}`);
    const noise = Math.sin(i / 3.2) * 50 + (Math.random() * 34 - 17);
    const dayVal = Math.round(168 + noise);
    observed.push(dayVal);
    rolling = rolling * 0.75 + dayVal * 0.25;
    ma.push(Math.round(rolling));
    target.push(170);
  }

  charts.trendDaily = new Chart(ctx, {
    type: 'line',
    data: {
      labels: days,
      datasets: [
        {
          label: 'Observed Daily Rides',
          data: observed,
          borderColor: THEME.memberLight,
          backgroundColor: 'rgba(29, 78, 216, 0.04)',
          borderWidth: 1.5,
          pointRadius: 0,
          fill: true,
          tension: 0.2
        },
        {
          label: '7-Day Moving Average',
          data: ma,
          borderColor: THEME.red,
          borderWidth: 2.6,
          pointRadius: 0,
          tension: 0.35
        },
        {
          label: 'Target Baseline (170/day)',
          data: target,
          borderColor: '#94a3b8',
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 10, color: THEME.text } },
        y: { grid: { color: THEME.grid }, ticks: { color: THEME.text } }
      }
    }
  });
}

// 5.2 Page 1: User Split Donut
function initChartUserSplit() {
  const ctx = document.getElementById('chartUserSplit').getContext('2d');
  charts.userSplit = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Annual Member', 'Casual Rider'],
      datasets: [{
        data: [34210, 27763],
        backgroundColor: [THEME.member, THEME.casual],
        borderWidth: 3,
        borderColor: '#ffffff',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '74%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 12, padding: 18, font: { weight: 600 } }
        }
      }
    }
  });
}

// 5.3 Page 1: Top 10 Departure Stations
function initChartTopStations() {
  const ctx = document.getElementById('chartTopStations').getContext('2d');
  const stations = [
    'Streeter Dr & Grand',
    'DuSable Lake Shore',
    'Michigan & Oak',
    'Millennium Park',
    'Clinton & Washington',
    'Clinton & Madison',
    'Canal & Adams',
    'Kingsbury & Kinzie',
    'Clark & Elm',
    'Theater on Lake'
  ];

  charts.topStations = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: stations,
      datasets: [
        {
          label: 'Member',
          data: [620, 850, 940, 1020, 3850, 3620, 2790, 2410, 2140, 710],
          backgroundColor: THEME.member,
          borderRadius: 4
        },
        {
          label: 'Casual',
          data: [4120, 3450, 2890, 2780, 520, 610, 620, 680, 1140, 2420],
          backgroundColor: THEME.casual,
          borderRadius: 4
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12 } }
      },
      scales: {
        x: { stacked: true, grid: { color: THEME.grid }, ticks: { color: THEME.text } },
        y: { stacked: true, grid: { display: false }, ticks: { color: THEME.text } }
      }
    }
  });
}

// 5.4 Page 1: Bike Fleet Share
function initChartBikeFleet() {
  const ctx = document.getElementById('chartBikeFleet').getContext('2d');
  charts.bikeFleet = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Classic Bike', 'Electric Bike', 'Docked Bike'],
      datasets: [
        {
          label: 'Member',
          data: [18400, 15810, 0],
          backgroundColor: THEME.member,
          borderRadius: 4
        },
        {
          label: 'Casual',
          data: [11200, 13120, 3443],
          backgroundColor: THEME.casual,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12 } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: THEME.text } },
        y: { grid: { color: THEME.grid }, ticks: { color: THEME.text } }
      }
    }
  });
}

// 5.5 Page 2: 24-Hour Profile
function initChartHourlyProfile() {
  const ctx = document.getElementById('chartHourlyProfile').getContext('2d');
  const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);

  const memberHourly = [
    120, 80, 50, 40, 90, 340, 1100, 2850, 4100, 2200, 1400, 1600, 
    1850, 1720, 1680, 2150, 3950, 4620, 2980, 1820, 1240, 820, 510, 250
  ];

  const casualHourly = [
    180, 110, 80, 60, 50, 90, 240, 580, 890, 1150, 1620, 2140, 
    2650, 2980, 3210, 3450, 3620, 3410, 2850, 2100, 1480, 990, 620, 320
  ];

  charts.hourlyProfile = new Chart(ctx, {
    type: 'line',
    data: {
      labels: hours,
      datasets: [
        {
          label: 'Member (Twin Commute Peaks: 8 AM & 5 PM)',
          data: memberHourly,
          borderColor: THEME.member,
          backgroundColor: 'rgba(29, 78, 216, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 2
        },
        {
          label: 'Casual (Leisure Afternoon Bell Curve)',
          data: casualHourly,
          borderColor: THEME.casual,
          backgroundColor: 'rgba(234, 88, 12, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12 } },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 12, color: THEME.text } },
        y: { grid: { color: THEME.grid }, ticks: { color: THEME.text } }
      }
    }
  });
}

// 5.6 Page 2: Trip Duration Buckets
function initChartTripDurationBuckets() {
  const ctx = document.getElementById('chartTripDurationBuckets').getContext('2d');
  charts.tripDuration = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Short (<15 min)', 'Medium (15-60 min)', 'Long (>60 min)'],
      datasets: [
        {
          label: 'Member',
          data: [61.2, 36.4, 2.4],
          backgroundColor: THEME.member,
          borderRadius: 4
        },
        {
          label: 'Casual',
          data: [26.8, 54.1, 19.1],
          backgroundColor: THEME.casual,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12 } },
        tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.raw}% of trips` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: THEME.text } },
        y: { grid: { color: THEME.grid }, ticks: { callback: v => `${v}%`, color: THEME.text } }
      }
    }
  });
}

// 5.7 Page 2: Day of Week
function initChartDayOfWeek() {
  const ctx = document.getElementById('chartDayOfWeek').getContext('2d');
  charts.dayOfWeek = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [
        {
          label: 'Member',
          data: [5420, 5840, 6110, 5920, 5100, 3120, 2700],
          backgroundColor: THEME.member,
          borderRadius: 4
        },
        {
          label: 'Casual',
          data: [2650, 2480, 2710, 2920, 3850, 6890, 6263],
          backgroundColor: THEME.casual,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12 } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: THEME.text } },
        y: { grid: { color: THEME.grid }, ticks: { color: THEME.text } }
      }
    }
  });
}

// 5.8 Page 3: Monthly Seasonality Area Chart
function initChartMonthlySeasonality() {
  const ctx = document.getElementById('chartMonthlySeasonality').getContext('2d');
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  charts.monthlySeason = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Member Rides',
          data: [1820, 2100, 2850, 3420, 3950, 4420, 4610, 4520, 4120, 3210, 1980, 1420],
          borderColor: THEME.member,
          backgroundColor: 'rgba(29, 78, 216, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        },
        {
          label: 'Casual Rides',
          data: [740, 910, 1450, 2410, 3620, 4850, 5232, 4980, 3510, 2120, 940, 560],
          borderColor: THEME.casual,
          backgroundColor: 'rgba(234, 88, 12, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12 } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: THEME.text } },
        y: { grid: { color: THEME.grid }, ticks: { color: THEME.text } }
      }
    }
  });
}

// 5.9 Page 4: Net Station Flow
function initChartNetStationFlow() {
  const ctx = document.getElementById('chartNetStationFlow').getContext('2d');
  const stations = ['Navy Pier', 'Millennium Pk', 'Oak St Beach', 'Union Station', 'Ogilvie Stn', 'Lincoln Park'];
  const netFlow = [420, 290, 180, -380, -440, 110];

  charts.netFlow = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: stations,
      datasets: [{
        label: 'Net Balance',
        data: netFlow,
        backgroundColor: netFlow.map(v => v >= 0 ? THEME.green : THEME.red),
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.raw >= 0 ? '+' : ''}${ctx.raw} rides net (${ctx.raw >= 0 ? 'Surplus' : 'Deficit'})`
          }
        }
      },
      scales: {
        x: { grid: { color: THEME.grid }, ticks: { color: THEME.text } },
        y: { grid: { display: false }, ticks: { color: THEME.text } }
      }
    }
  });
}

// --------------------------------------------------------------------------
// 6. 24x7 HEATMAP MATRIX
// --------------------------------------------------------------------------
function renderHeatmap() {
  const container = document.getElementById('heatmapMatrixContainer');
  if (!container) return;

  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  let html = '<div class="heatmap-grid-layout">';

  html += '<div class="hm-cell header">Day \\ Hr</div>';
  for (let h = 0; h < 24; h++) {
    html += `<div class="hm-cell header">${h}h</div>`;
  }

  days.forEach((day, dIdx) => {
    html += `<div class="hm-cell header">${day}</div>`;
    const isWeekend = dIdx >= 5;

    for (let h = 0; h < 24; h++) {
      let intensity = 0.08;
      if (!isWeekend) {
        if (h >= 7 && h <= 9) intensity = 0.88 + (Math.random() * 0.12);
        else if (h >= 16 && h <= 19) intensity = 0.96 + (Math.random() * 0.04);
        else if (h >= 11 && h <= 15) intensity = 0.44;
        else if (h <= 5 || h >= 22) intensity = 0.05;
        else intensity = 0.26;
      } else {
        if (h >= 12 && h <= 17) intensity = 0.92 + (Math.random() * 0.08);
        else if (h >= 10 && h <= 20) intensity = 0.62;
        else if (h <= 6 || h >= 23) intensity = 0.07;
        else intensity = 0.32;
      }

      const bg = `rgba(29, 78, 216, ${intensity.toFixed(2)})`;
      const textColor = intensity > 0.5 ? '#ffffff' : '#0f172a';
      const rideCount = Math.round(intensity * 480);

      html += `<div class="hm-cell" style="background: ${bg}; color: ${textColor};" title="${day} at ${h}:00 - Volume: ${rideCount} rides">${rideCount}</div>`;
    }
  });

  html += '</div>';
  container.innerHTML = html;
}

// --------------------------------------------------------------------------
// 7. REAL LEAFLET CHICAGO MAP
// --------------------------------------------------------------------------
let mapTileLayer = null;

function initLeafletMap() {
  const mapEl = document.getElementById('leafletMap');
  if (!mapEl) return;

  if (leafletMap) {
    leafletMap.invalidateSize();
    return;
  }

  // Chicago Downtown Coordinates
  leafletMap = L.map('leafletMap', {
    center: [41.884, -87.628],
    zoom: 13,
    zoomControl: true
  });

  updateMapTileLayer();

  // Add circle markers for all authentic Chicago stations
  STATIONS.forEach(s => {
    const isCasualHeavy = s.casual > 50;
    const color = isCasualHeavy ? '#ea580c' : '#1d4ed8';
    const radius = Math.max(9, Math.round(s.volume / 280));

    const marker = L.circleMarker([s.lat, s.lng], {
      radius: radius,
      fillColor: color,
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(leafletMap);

    marker.bindPopup(`
      <div style="font-family: var(--font-sans); padding: 4px;">
        <strong style="font-size: 13px;">${s.name}</strong><br/>
        <span style="font-size: 11px; color: #64748b;">Annual Volume: <strong>${s.volume.toLocaleString()}</strong></span><br/>
        <span style="font-size: 11px; color: ${isCasualHeavy ? '#ea580c' : '#1d4ed8'};">Casual Ratio: <strong>${s.casual}%</strong></span><br/>
        <span style="font-size: 11px; color: #059669;">Net Flow: <strong>${s.net}</strong></span>
      </div>
    `);

    marker.on('click', () => {
      selectStation(s);
    });

    stationMarkers.push(marker);
  });
}

function updateMapTileLayer() {
  if (!leafletMap) return;

  if (mapTileLayer) {
    leafletMap.removeLayer(mapTileLayer);
  }

  // Clean OpenStreetMap tiles without watermarks
  const tileUrl = state.darkMode
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  mapTileLayer = L.tileLayer(tileUrl, {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap &copy; CARTO'
  }).addTo(leafletMap);
}

function selectStation(s) {
  state.selectedStation = s;
  document.getElementById('selectedStationName').innerText = s.name;
  document.getElementById('selectedStationVolume').innerText = `${s.volume.toLocaleString()} rides`;
  document.getElementById('selectedStationCasual').innerText = `${s.casual.toFixed(1)}%`;
  document.getElementById('selectedStationNet').innerText = s.net;
}

// --------------------------------------------------------------------------
// 8. ORIGIN-DESTINATION CORRIDORS
// --------------------------------------------------------------------------
function renderODRoutes() {
  const body = document.getElementById('odRoutesTableBody');
  if (!body) return;

  const routes = [
    { key: "101-101", origin: "Streeter Dr & Grand Ave", dest: "Streeter Dr & Grand Ave (Loop)", rides: 1420, persona: "Casual Cruiser", duration: "38.2 min", dist: "8.4 km", round: "Yes (Loop)" },
    { key: "101-104", origin: "Streeter Dr & Grand Ave", dest: "Millennium Park", rides: 1180, persona: "Casual Tourist", duration: "24.6 min", dist: "2.1 km", round: "No" },
    { key: "201-207", origin: "Clinton St & Washington Blvd", dest: "Dearborn St & Adams St", rides: 960, persona: "Member Commuter", duration: "10.4 min", dist: "1.2 km", round: "No" },
    { key: "202-208", origin: "Clinton St & Madison St", dest: "Franklin St & Monroe St", rides: 910, persona: "Member Commuter", duration: "9.2 min", dist: "0.9 km", round: "No" },
    { key: "102-103", origin: "DuSable Lake Shore & Monroe", dest: "Michigan Ave & Oak St", rides: 840, persona: "Casual Cruiser", duration: "22.8 min", dist: "3.2 km", round: "No" },
    { key: "204-201", origin: "Kingsbury St & Kinzie St", dest: "Clinton St & Washington Blvd", rides: 780, persona: "Member Commuter", duration: "11.1 min", dist: "1.4 km", round: "No" },
    { key: "105-101", origin: "Theater on the Lake", dest: "Streeter Dr & Grand Ave", rides: 720, persona: "Casual Cruiser", duration: "28.5 min", dist: "4.8 km", round: "No" },
    { key: "205-207", origin: "Clark St & Elm St", dest: "Dearborn St & Adams St", rides: 690, persona: "Member Commuter", duration: "13.6 min", dist: "2.8 km", round: "No" }
  ];

  let html = '';
  routes.forEach(r => {
    const isMember = r.persona.includes('Member');
    html += `
      <tr>
        <td><code>${r.key}</code></td>
        <td><strong>${r.origin}</strong></td>
        <td>${r.dest}</td>
        <td><strong>${r.rides.toLocaleString()}</strong></td>
        <td><span class="status-tag ${isMember ? 'success' : 'warning'}">${r.persona}</span></td>
        <td>${r.duration}</td>
        <td>${r.dist}</td>
        <td><span class="cluster-tag ${r.round.includes('Yes') ? 'c2' : 'c1'}">${r.round}</span></td>
      </tr>
    `;
  });

  body.innerHTML = html;
}
