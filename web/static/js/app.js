const logInput = document.getElementById("logInput");
const analyzeButton = document.getElementById("analyzeButton");
const clearAnalyzeButton = document.getElementById("clearAnalyzeButton");
const maxGroupsInput = document.getElementById("maxGroups");
const analysisStatus = document.getElementById("analysisStatus");
const analysisResults = document.getElementById("analysisResults");
const sanitizeInput = document.getElementById("sanitizeInput");
const sanitizeButton = document.getElementById("sanitizeButton");
const clearSanitizeButton = document.getElementById("clearSanitizeButton");
const sanitizeMode = document.getElementById("sanitizeMode");
const preserveCorrelation = document.getElementById("preserveCorrelation");
const sanitizeStatus = document.getElementById("sanitizeStatus");
const sanitizeResults = document.getElementById("sanitizeResults");
const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");
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

function switchTab(targetId) {
  tabButtons.forEach((button) => button.classList.toggle("active", button.dataset.tab === targetId));
  tabPanels.forEach((panel) => panel.classList.toggle("active", panel.id === targetId));
}

tabButtons.forEach((button) => {
  button.addEventListener("click", () => switchTab(button.dataset.tab));
});

analyzeButton.addEventListener("click", analyzeLogs);
clearAnalyzeButton.addEventListener("click", () => {
  logInput.value = "";
  setStatus(analysisStatus, "Waiting for logs.", false);
  renderEmptyState(
    analysisResults,
    "No analysis yet",
    "Paste production-like logs and run analysis. The result will show source breakdown, dominant issue, grouped patterns, examples, and recommended L2 actions.",
  );
});

sanitizeButton.addEventListener("click", sanitizeLogs);
clearSanitizeButton.addEventListener("click", () => {
  sanitizeInput.value = "";
  setStatus(sanitizeStatus, "Waiting for logs.", false);
  renderEmptyState(
    sanitizeResults,
    "No sanitization yet",
    "Paste logs with possible secrets or PII. The result will show detections, replacements, and a share-safe version of the logs.",
  );
});

logInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    analyzeLogs();
  }
});

sanitizeInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    sanitizeLogs();
  }
});

async function analyzeLogs() {
  const text = logInput.value.trim();
  if (!text) {
    setStatus(analysisStatus, "Paste logs before running analysis.", true);
    return;
  }

  setStatus(analysisStatus, "Analyzing logs...", false);
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
    setStatus(analysisStatus, "Analysis complete.", false);
  } catch (error) {
    setStatus(analysisStatus, error.message || "Analysis failed.", true);
    renderEmptyState(
      analysisResults,
      "Analysis failed",
      "Check that the FastAPI backend is running and the pasted payload is valid text.",
    );
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Analyze logs";
  }
}

async function sanitizeLogs() {
  const text = sanitizeInput.value.trim();
  if (!text) {
    setStatus(sanitizeStatus, "Paste logs before running sanitization.", true);
    return;
  }

  setStatus(sanitizeStatus, "Sanitizing logs...", false);
  sanitizeButton.disabled = true;
  sanitizeButton.textContent = "Sanitizing...";
  clear(sanitizeResults);

  try {
    const response = await fetch(`${apiBaseUrl}/api/sanitize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        mode: sanitizeMode.value,
        preserve_correlation: preserveCorrelation.checked,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(readApiError(payload));
    }
    renderSanitized(payload);
    setStatus(sanitizeStatus, "Sanitization complete.", false);
  } catch (error) {
    setStatus(sanitizeStatus, error.message || "Sanitization failed.", true);
    renderEmptyState(
      sanitizeResults,
      "Sanitization failed",
      "Check that the FastAPI backend is running and the pasted payload is valid text.",
    );
  } finally {
    sanitizeButton.disabled = false;
    sanitizeButton.textContent = "Sanitize logs";
  }
}

function renderAnalysis(payload) {
  clear(analysisResults);
  analysisResults.appendChild(renderAnalysisSummary(payload.summary));
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

function renderAnalysisSummary(summary) {
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

function renderSanitized(payload) {
  clear(sanitizeResults);
  sanitizeResults.appendChild(renderSanitizationSummary(payload.summary));
  sanitizeResults.appendChild(renderCategoryBreakdown(payload.summary.categories || {}));
  sanitizeResults.appendChild(renderExamples(payload.examples || []));
  sanitizeResults.appendChild(renderSanitizedOutput(payload.sanitized_text));
}

function renderSanitizationSummary(summary) {
  const grid = createElement("section", "summary-grid");
  [
    ["Total lines", summary.total_lines],
    ["Changed lines", summary.transformed_lines],
    ["Matches", summary.total_matches],
  ].forEach(([label, value]) => {
    const card = createElement("div", "metric-card");
    card.appendChild(createElement("span", "metric-value", String(value)));
    card.appendChild(createElement("span", "metric-label", label));
    grid.appendChild(card);
  });
  return grid;
}

function renderCategoryBreakdown(categories) {
  const panel = createElement("section", "source-panel");
  const header = createElement("div", "panel-header");
  header.appendChild(createElement("h3", null, "Detected categories"));
  panel.appendChild(header);

  const row = createElement("div", "source-row");
  const entries = Object.entries(categories).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    row.appendChild(createElement("span", "badge", "none"));
  } else {
    entries.forEach(([category, count]) => row.appendChild(createElement("span", "badge", `${category}: ${count}`)));
  }
  panel.appendChild(row);
  return panel;
}

function renderExamples(examples) {
  const panel = createElement("section", "insight-panel");
  panel.appendChild(createElement("h3", "section-title", "Replacement examples"));
  if (!examples.length) {
    panel.appendChild(createElement("p", "muted", "No sensitive values were detected."));
    return panel;
  }

  const list = createElement("div", "example-grid");
  examples.forEach((example) => {
    const card = createElement("article", "example-panel");
    const header = createElement("div", "panel-header");
    header.appendChild(createElement("span", "badge success", example.category));
    card.appendChild(header);
    card.appendChild(createElement("div", "mini-label", "Original preview"));
    card.appendChild(createElement("code", "example-code", example.original_preview));
    card.appendChild(createElement("div", "mini-label", "Replacement"));
    card.appendChild(createElement("code", "example-code", example.replacement_preview));
    list.appendChild(card);
  });
  panel.appendChild(list);
  return panel;
}

function renderSanitizedOutput(sanitizedText) {
  const panel = createElement("section", "output-block");
  const header = createElement("div", "panel-header");
  header.appendChild(createElement("h3", null, "Sanitized logs"));

  const buttonRow = createElement("div", "inline-actions");
  const copyButton = createElement("button", "secondary-button compact-button", "Copy");
  copyButton.type = "button";
  copyButton.addEventListener("click", () => copyText(sanitizedText, copyButton));

  const moveButton = createElement("button", "primary-button compact-button", "Use in analyzer");
  moveButton.type = "button";
  moveButton.addEventListener("click", () => {
    logInput.value = sanitizedText;
    switchTab("analyzerTab");
    setStatus(analysisStatus, "Sanitized logs copied into RCA Analyzer input.", false);
  });

  buttonRow.appendChild(copyButton);
  buttonRow.appendChild(moveButton);
  header.appendChild(buttonRow);
  panel.appendChild(header);

  const output = createElement("textarea", "text-output");
  output.value = sanitizedText;
  output.readOnly = true;
  panel.appendChild(output);
  return panel;
}

function renderList(items) {
  const list = createElement("ul");
  items.forEach((item) => list.appendChild(createElement("li", null, item)));
  return list;
}

function renderEmptyState(node, title, message) {
  clear(node);
  const empty = createElement("div", "empty-state");
  empty.appendChild(createElement("h3", null, title));
  empty.appendChild(createElement("p", null, message));
  node.appendChild(empty);
}

async function copyText(text, button) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      fallbackCopy(text);
    }
    const previous = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => {
      button.textContent = previous;
    }, 1400);
  } catch {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

function setStatus(node, message, isError) {
  node.textContent = message;
  node.classList.toggle("error", Boolean(isError));
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
