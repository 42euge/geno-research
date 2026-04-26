// Reward Monitoring Dashboard frontend.
// Single-file vanilla JS module with three render entrypoints, one per page.
// Uses Chart.js loaded from CDN.

const RewardDashboard = (() => {
  const api = (path) => fetch(path).then(r => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  });

  const fmt = (v, digits = 3) =>
    v === null || v === undefined || Number.isNaN(v) ? "—" : Number(v).toFixed(digits);

  function getRunId() {
    const m = window.location.pathname.match(/\/run\/(.+)$/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  // ---- runs list page ------------------------------------------------------

  async function renderRunsList() {
    const runs = await api("/api/runs");
    const tbody = document.querySelector("#runs-table tbody");
    if (!runs.length) {
      document.getElementById("empty-state").hidden = false;
      return;
    }
    tbody.innerHTML = runs.map(r => {
      const s = r.summary || {};
      return `
        <tr class="clickable" onclick="window.location='/run/${encodeURIComponent(r.run_id)}'">
          <td><strong>${escape(r.name)}</strong><br><code>${escape(r.run_id)}</code></td>
          <td>${escape(r.created_at)}</td>
          <td>${s.count ?? 0}</td>
          <td>${fmt(s.mean)}</td>
          <td>${fmt(s.std)}</td>
          <td>${fmt(s.min)} / ${fmt(s.max)}</td>
          <td>${runAlertsBadge(r.run_id)}</td>
        </tr>`;
    }).join("");
    // Asynchronously fill in alert badges
    runs.forEach(async r => {
      try {
        const alerts = await api(`/api/runs/${encodeURIComponent(r.run_id)}/alerts`);
        const slot = document.getElementById(`alerts-${r.run_id}`);
        if (!slot) return;
        if (!alerts.length) {
          slot.innerHTML = `<span class="badge good">OK</span>`;
        } else {
          slot.innerHTML = alerts
            .map(a => `<span class="badge ${a.severity === 'critical' ? 'danger' : 'warn'}">${escape(a.name)}</span>`)
            .join(" ");
        }
      } catch (e) { /* ignore */ }
    });
  }

  function runAlertsBadge(runId) {
    return `<span id="alerts-${runId}"><span class="badge">…</span></span>`;
  }

  // ---- run detail page -----------------------------------------------------

  async function renderRunDetail() {
    const runId = getRunId();
    if (!runId) return;
    const [run, series, dist, byTask, lengthCorr, anomalies] = await Promise.all([
      api(`/api/runs/${encodeURIComponent(runId)}`),
      api(`/api/runs/${encodeURIComponent(runId)}/series`),
      api(`/api/runs/${encodeURIComponent(runId)}/distribution`),
      api(`/api/runs/${encodeURIComponent(runId)}/by_task`),
      api(`/api/runs/${encodeURIComponent(runId)}/length_corr`),
      api(`/api/runs/${encodeURIComponent(runId)}/anomalies`),
    ]);

    document.getElementById("run-title").textContent = `${run.name} · ${run.run_id}`;
    renderAlerts(run.alerts || []);
    renderSummary(run);
    renderSeriesChart(series, anomalies);
    renderDistChart(dist);
    renderLengthChart(lengthCorr);
    renderTaskTable(byTask);
    renderAnomaliesTable(anomalies, runId);

    setupSamplesPager(runId);
  }

  function renderAlerts(alerts) {
    const sec = document.getElementById("alerts-section");
    if (!alerts.length) { sec.hidden = true; return; }
    sec.hidden = false;
    document.getElementById("alerts-list").innerHTML = alerts.map(a => `
      <li class="${a.severity}">
        <strong>${escape(a.name)}</strong> — ${escape(a.message)}
      </li>
    `).join("");
  }

  function renderSummary(run) {
    const s = run.summary || {};
    const d = run.drift || {};
    const cells = [
      ["Samples", s.count],
      ["Mean reward", fmt(s.mean)],
      ["Std", fmt(s.std)],
      ["Median", fmt(s.median)],
      ["Min", fmt(s.min)],
      ["Max", fmt(s.max)],
      ["P10 / P90", `${fmt(s.p10)} / ${fmt(s.p90)}`],
      ["Mean output length", fmt(s.mean_length, 1)],
      ["Drift Δ (late−early)", fmt(d.delta)],
      ["Drift / σ", fmt(d.normalized)],
      ["Anomalies", run.anomaly_count ?? 0],
    ];
    document.getElementById("summary-grid").innerHTML = cells
      .map(([k, v]) => `<div class="metric"><div class="label">${k}</div><div class="value">${v ?? '—'}</div></div>`)
      .join("");
  }

  function renderSeriesChart(series, anomalies) {
    const ctx = document.getElementById("series-chart").getContext("2d");
    const anomalyMap = new Map(anomalies.map(a => [a.step, a.reward]));
    const anomalyData = series.steps.map(step =>
      anomalyMap.has(step) ? anomalyMap.get(step) : null);
    new Chart(ctx, {
      type: "line",
      data: {
        labels: series.steps,
        datasets: [
          {
            label: "Reward",
            data: series.rewards,
            borderColor: "rgba(88,166,255,0.4)",
            borderWidth: 1,
            pointRadius: 0,
            tension: 0,
          },
          {
            label: `Rolling mean (w=${series.window})`,
            data: series.rolling_mean,
            borderColor: "#58a6ff",
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.2,
          },
          {
            label: "Anomalies",
            data: anomalyData,
            type: "scatter",
            backgroundColor: "#f85149",
            pointRadius: 4,
            showLine: false,
          },
        ],
      },
      options: chartOpts({ x: "step" }),
    });
  }

  function renderDistChart(dist) {
    const ctx = document.getElementById("dist-chart").getContext("2d");
    const labels = dist.bin_edges.slice(0, -1).map((e, i) =>
      `${e.toFixed(2)}–${dist.bin_edges[i+1].toFixed(2)}`);
    new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [{ label: "count", data: dist.counts, backgroundColor: "#58a6ff" }] },
      options: chartOpts({ x: "reward bin" }),
    });
  }

  function renderLengthChart(lc) {
    document.getElementById("length-corr-label").textContent =
      `Pearson r = ${fmt(lc.pearson)} (n=${lc.n})`;
    const ctx = document.getElementById("length-chart").getContext("2d");
    new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [{
          label: "samples",
          data: lc.points.map(p => ({ x: p.length, y: p.reward })),
          backgroundColor: "rgba(88,166,255,0.5)",
          pointRadius: 3,
        }],
      },
      options: chartOpts({ x: "output length", y: "reward" }),
    });
  }

  function renderTaskTable(rows) {
    const tbody = document.querySelector("#task-table tbody");
    if (!rows.length) { tbody.innerHTML = `<tr><td colspan="7" class="hint">No data</td></tr>`; return; }
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${escape(r.task_type)}</td>
        <td>${r.count}</td>
        <td>${fmt(r.mean)}</td>
        <td>${fmt(r.std)}</td>
        <td>${fmt(r.min)}</td>
        <td>${fmt(r.median)}</td>
        <td>${fmt(r.max)}</td>
      </tr>`).join("");
  }

  function renderAnomaliesTable(anomalies, runId) {
    const tbody = document.querySelector("#anomalies-table tbody");
    if (!anomalies.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="hint">No anomalies detected</td></tr>`;
      return;
    }
    tbody.innerHTML = anomalies.map(a => `
      <tr class="clickable" data-sample-id="${a.id}">
        <td>${a.step}</td>
        <td>${fmt(a.reward)}</td>
        <td>${fmt(a.z_score)}</td>
        <td><span class="badge ${a.direction === 'low' ? 'danger' : 'warn'}">${a.direction}</span></td>
        <td>${escape(a.task_type)}</td>
        <td><button>view</button></td>
      </tr>`).join("");
    tbody.querySelectorAll("tr").forEach(tr => {
      tr.onclick = () => loadSampleDetail(tr.dataset.sampleId);
    });
  }

  // ---- samples pager -------------------------------------------------------

  function setupSamplesPager(runId) {
    const state = { offset: 0, limit: 25, order_by: "step", descending: false };

    async function refresh() {
      const params = new URLSearchParams(state);
      const data = await api(`/api/runs/${encodeURIComponent(runId)}/samples?${params}`);
      const tbody = document.querySelector("#samples-table tbody");
      tbody.innerHTML = data.items.map(s => `
        <tr class="clickable" data-sample-id="${s.id}">
          <td>${s.step}</td>
          <td>${fmt(s.reward)}</td>
          <td>${s.output_length}</td>
          <td>${escape(s.task_type)}</td>
          <td>${escape(truncate(s.prompt, 80))}</td>
        </tr>`).join("");
      tbody.querySelectorAll("tr").forEach(tr => {
        tr.onclick = () => loadSampleDetail(tr.dataset.sampleId);
      });
      const start = data.total === 0 ? 0 : state.offset + 1;
      const end = Math.min(state.offset + state.limit, data.total);
      document.getElementById("page-info").textContent = `${start}–${end} of ${data.total}`;
      document.getElementById("prev-page").disabled = state.offset === 0;
      document.getElementById("next-page").disabled = end >= data.total;
    }

    document.getElementById("sort-by").onchange = e => { state.order_by = e.target.value; state.offset = 0; refresh(); };
    document.getElementById("sort-desc").onchange = e => { state.descending = e.target.checked; state.offset = 0; refresh(); };
    document.getElementById("prev-page").onclick = () => { state.offset = Math.max(0, state.offset - state.limit); refresh(); };
    document.getElementById("next-page").onclick = () => { state.offset += state.limit; refresh(); };
    refresh();
  }

  async function loadSampleDetail(sampleId) {
    const s = await api(`/api/samples/${sampleId}`);
    document.getElementById("sample-detail").hidden = false;
    document.getElementById("sample-fields").innerHTML = `
      <dt>Step</dt><dd>${s.step}</dd>
      <dt>Timestamp</dt><dd>${escape(s.timestamp)}</dd>
      <dt>Reward</dt><dd>${fmt(s.reward)}</dd>
      <dt>Task type</dt><dd>${escape(s.task_type)}</dd>
      <dt>Output length</dt><dd>${s.output_length}</dd>`;
    document.getElementById("sample-prompt").textContent = s.prompt;
    document.getElementById("sample-output").textContent = s.output;
    document.getElementById("sample-detail").scrollIntoView({ behavior: "smooth" });
  }

  // ---- compare page --------------------------------------------------------

  async function renderComparePage() {
    const runs = await api("/api/runs");
    const container = document.getElementById("run-checkboxes");
    container.innerHTML = runs.map(r => `
      <label><input type="checkbox" value="${escape(r.run_id)}" /> ${escape(r.name)} <code>${escape(r.run_id)}</code></label>
    `).join("");
    document.getElementById("compare-form").onsubmit = async (e) => {
      e.preventDefault();
      const ids = Array.from(container.querySelectorAll("input:checked")).map(i => i.value);
      if (!ids.length) return;
      const data = await api(`/api/compare?runs=${ids.map(encodeURIComponent).join(",")}`);
      renderCompareResults(data);
    };
  }

  function renderCompareResults(data) {
    document.getElementById("compare-results").hidden = false;
    const palette = ["#58a6ff", "#f0b441", "#56d364", "#f85149", "#bc8cff", "#39c5cf"];
    const datasets = data.runs.map((r, i) => ({
      label: r.name,
      data: r.series.steps.map((step, j) => ({ x: step, y: r.series.rolling_mean[j] })),
      borderColor: palette[i % palette.length],
      backgroundColor: palette[i % palette.length],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.2,
    }));
    const ctx = document.getElementById("compare-chart").getContext("2d");
    if (window._compareChart) window._compareChart.destroy();
    window._compareChart = new Chart(ctx, {
      type: "line",
      data: { datasets },
      options: chartOpts({ x: "step", y: "rolling mean reward", parsing: false }),
    });

    const tbody = document.querySelector("#compare-table tbody");
    tbody.innerHTML = data.runs.map(r => `
      <tr>
        <td><strong>${escape(r.name)}</strong><br><code>${escape(r.run_id)}</code></td>
        <td>${r.summary.count}</td>
        <td>${fmt(r.summary.mean)}</td>
        <td>${fmt(r.summary.std)}</td>
        <td>${fmt(r.drift.delta)}</td>
        <td>${fmt(r.drift.normalized)}</td>
      </tr>`).join("");
  }

  // ---- helpers -------------------------------------------------------------

  function chartOpts({ x = "", y = "", parsing = true } = {}) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      parsing,
      animation: false,
      scales: {
        x: { title: { display: !!x, text: x, color: "#8b949e" }, ticks: { color: "#8b949e" }, grid: { color: "#2a313c" } },
        y: { title: { display: !!y, text: y, color: "#8b949e" }, ticks: { color: "#8b949e" }, grid: { color: "#2a313c" } },
      },
      plugins: { legend: { labels: { color: "#d6dde6" } } },
    };
  }

  function escape(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function truncate(s, n) {
    s = String(s ?? "");
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  return { renderRunsList, renderRunDetail, renderComparePage };
})();
