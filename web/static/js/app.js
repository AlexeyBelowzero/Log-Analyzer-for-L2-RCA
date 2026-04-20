const logInput = document.getElementById("logInput");
const analyzeButton = document.getElementById("analyzeButton");
const clearButton = document.getElementById("clearButton");
const maxGroupsInput = document.getElementById("maxGroups");
const analysisStatus = document.getElementById("analysisStatus");
const analysisResults = document.getElementById("analysisResults");
const apiBaseUrl = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

function createElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) {
    node.className = className;
  }
  if (text !== undefined && text !== null) {
    node.textContent = text;
  }
  return node;
}

function clear(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

analyzeButton.addEventListener("click", analyzeLogs);
clearButton.addEventListener("click", () => {
  logInput.value = "";
  setStatus("Waiting for logs.", false);
  renderEmptyState();
});

logInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    analyzeLogs();
  }
});

async function analyzeLogs() {
  const text = logInput.value.trim();
  if (!text) {
    setStatus("Paste logs before running analysis.", true);
    return;
  }

  setStatus("Analyzing logs...", false);
  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analyzing...";
  clear(analysisResults);

  try {
    const response = await fetch(`${apiBaseUrl}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        source_type: "auto",
        max_groups: Number(maxGroupsInput.value || 12),
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(readApiError(payload));
    }
    renderAnalysis(payload);
    setStatus("Analysis complete.", false);
  } catch (error) {
    setStatus(error.message || "Analysis failed.", true);
    renderEmptyState("Analysis failed", "Check that the FastAPI backend is running and the pasted payload is valid text.");
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Analyze logs";
  }
}

function renderAnalysis(payload) {
  clear(analysisResults);
  analysisResults.appendChild(renderSummary(payload.summary));
  analysisResults.appendChild(renderSourceBreakdown(payload.summary.source_types || {}));

  if (payload.summary.dominant_issue) {
    const dominant = createElement("section", "dominant-panel");
    const header = createElement("div", "panel-header");
    header.appendChild(createElement("h3", null, "Dominant issue"));
    header.appendChild(createElement("span", "badge warning", `${payload.summary.dominant_percentage.toFixed(1)}%`));
    dominant.appendChild(header);
    dominant.appendChild(createElement("code", "pattern-code", payload.summary.dominant_issue));
    analysisResults.appendChild(dominant);
  }

  const groupList = createElement("section", "group-list");
  groupList.appendChild(createElement("h3", "section-title", "Grouped failure patterns"));
  if (payload.groups.length) {
    payload.groups.forEach((group) => groupList.appendChild(renderGroup(group)));
  } else {
    groupList.appendChild(createElement("p", "muted", "No warning, error, fatal, or critical events were found."));
  }
  analysisResults.appendChild(groupList);

  if (payload.insights.length) {
    const insightList = createElement("section", "insight-list");
    insightList.appendChild(createElement("h3", "section-title", "RCA insights"));
    payload.insights.forEach((insight) => insightList.appendChild(renderInsight(insight)));
    analysisResults.appendChild(insightList);
  }
}

function renderSummary(summary) {
  const grid = createElement("section", "summary-grid");
  [
    ["Total lines", summary.total_lines],
    ["Parsed records", summary.parsed_lines],
    ["Error events", summary.error_events],
    ["Unique patterns", summary.unique_patterns],
    ["Dominant share", `${summary.dominant_percentage.toFixed(1)}%`],
  ].forEach(([label, value]) => {
    const card = createElement("div", "metric-card");
    card.appendChild(createElement("span", "metric-value", String(value)));
    card.appendChild(createElement("span", "metric-label", label));
    grid.appendChild(card);
  });
  return grid;
}

function renderSourceBreakdown(sourceTypes) {
  const panel = createElement("section", "source-panel");
  const header = createElement("div", "panel-header");
  header.appendChild(createElement("h3", null, "Detected sources"));
  panel.appendChild(header);

  const row = createElement("div", "source-row");
  const entries = Object.entries(sourceTypes).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    row.appendChild(createElement("span", "badge", "none"));
  } else {
    entries.forEach(([source, count]) => row.appendChild(createElement("span", "badge", `${source}: ${count}`)));
  }
  panel.appendChild(row);
  return panel;
}

function renderGroup(group) {
  const panel = createElement("article", "group-panel");
  const badges = createElement("div", "badge-row");
  badges.appendChild(createElement("span", "badge danger", group.classification));
  badges.appendChild(createElement("span", "badge", `Count: ${group.count}`));
  badges.appendChild(createElement("span", "badge", `Level: ${group.level}`));
  if (group.service) {
    badges.appendChild(createElement("span", "badge", `Service: ${group.service}`));
  }
  if (group.source_type) {
    badges.appendChild(createElement("span", "badge", `Source: ${group.source_type}`));
  }
  panel.appendChild(badges);
  panel.appendChild(createElement("code", "pattern-code", group.pattern));

  if (group.examples && group.examples.length) {
    const details = createElement("details", "examples");
    details.appendChild(createElement("summary", null, "Examples"));
    group.examples.forEach((example) => details.appendChild(createElement("code", "example-code", example)));
    panel.appendChild(details);
  }
  return panel;
}

function renderInsight(insight) {
  const panel = createElement("article", "insight-panel");
  const header = createElement("div", "panel-header");
  header.appendChild(createElement("h3", null, insight.title));
  header.appendChild(createElement("span", "badge success", insight.classification));
  panel.appendChild(header);

  if (insight.possible_causes.length) {
    panel.appendChild(createElement("h4", null, "Possible causes"));
    panel.appendChild(renderList(insight.possible_causes));
  }
  if (insight.recommended_actions.length) {
    panel.appendChild(createElement("h4", null, "Recommended actions"));
    panel.appendChild(renderList(insight.recommended_actions));
  }
  return panel;
}

function renderList(items) {
  const list = createElement("ul");
  items.forEach((item) => list.appendChild(createElement("li", null, item)));
  return list;
}

function renderEmptyState(title = "No analysis yet", message = "Paste production-like logs and run analysis. The result will show source breakdown, dominant issue, grouped patterns, examples, and recommended L2 actions.") {
  clear(analysisResults);
  const empty = createElement("div", "empty-state");
  empty.appendChild(createElement("h3", null, title));
  empty.appendChild(createElement("p", null, message));
  analysisResults.appendChild(empty);
}

function setStatus(message, isError) {
  analysisStatus.textContent = message;
  analysisStatus.classList.toggle("error", Boolean(isError));
}

function readApiError(payload) {
  if (payload && Array.isArray(payload.detail) && payload.detail.length) {
    return payload.detail.map((item) => item.msg).join("; ");
  }
  if (payload && typeof payload.detail === "string") {
    return payload.detail;
  }
  return "Request failed.";
}
