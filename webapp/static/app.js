/* global go */

const $ = go.GraphObject.make;

const state = {
  graph: null,
  nodeByKey: new Map(),
  lastContextOpenTs: 0,
};

const colorByLabel = {
  User: "#5dade2",
  PolicyGroup: "#a4b0be",
  Policy: "#f7dc6f",
  Schema: "#b388eb",
  Table: "#f1948a",
  Column: "#58d68d",
  Node: "#ced6e0",
};

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function linkColorByType(type) {
  if (type === "hasRowRule") return "#1f77b4";
  if (type === "hasColumnRule") return "#e67e22";
  return "#52606d";
}

function setStatus(text, isError = false) {
  const el = document.getElementById("statusMsg");
  el.textContent = text;
  el.style.color = isError ? "#d64545" : "#334e68";
}

function debugLog(message) {
  const el = document.getElementById("debugLog");
  if (!el) return;
  const stamp = new Date().toLocaleTimeString();
  const next = `[${stamp}] ${message}`;
  const existing = el.textContent === "No events yet." ? "" : el.textContent;
  const lines = [next, ...existing.split("\n").filter(Boolean)].slice(0, 18);
  el.textContent = lines.join("\n");
}

function hideUserContextMenu() {
  const menu = document.getElementById("userContextMenu");
  menu.classList.add("hidden");
  menu.innerHTML = "";
}

function handleContextForData(data, viewPoint) {
  if (!data) {
    hideUserContextMenu();
    return;
  }
  if (data.label === "User") {
    showUserContextMenu(data, viewPoint);
    return;
  }
  if (data.label === "PolicyGroup") {
    showGroupContextMenu(data, viewPoint);
    return;
  }
  hideUserContextMenu();
}

function openContextMenuFromDomEvent(evt) {
  if (!state.graph || !state.graph.div) return;
  evt.preventDefault();
  evt.stopPropagation();

  const rect = state.graph.div.getBoundingClientRect();
  const viewPoint = new go.Point(evt.clientX, evt.clientY);
  const localViewPoint = new go.Point(evt.clientX - rect.left, evt.clientY - rect.top);
  const docPoint = state.graph.transformViewToDoc(localViewPoint);
  const part =
    state.graph.findPartAt(docPoint, false) ||
    state.graph.findPartAt(docPoint, true) ||
    state.graph.findPartAt(state.graph.lastInput.documentPoint, false) ||
    state.graph.findPartAt(state.graph.lastInput.documentPoint, true);
  const data = part && part.data ? part.data : null;
  debugLog(
    [
      `openContextMenuFromDomEvent type=${evt.type}`,
      `button=${evt.button ?? "na"}`,
      `buttons=${evt.buttons ?? "na"}`,
      `ctrl=${Boolean(evt.ctrlKey)}`,
      `meta=${Boolean(evt.metaKey)}`,
      `pointer=${evt.pointerType || "na"}`,
      `client=(${evt.clientX},${evt.clientY})`,
      `part=${data ? `${data.label}:${(data.properties && (data.properties.userId || data.properties.policyGroupId || data.properties.policyName || data.properties.tableName || data.properties.columnName || data.properties.schemaName)) || "unknown"}` : "none"}`,
    ].join(" | ")
  );
  state.lastContextOpenTs = Date.now();
  handleContextForData(data, viewPoint);
}

async function submitMembership(action, userId, groupId) {
  const endpoint = action === "entitle" ? "/api/entitlements/assign" : "/api/entitlements/revoke";
  await fetchJSON(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, group_id: groupId }),
  });
}

async function submitGroupPolicy(action, groupId, policyId) {
  const endpoint =
    action === "include" ? "/api/groups/includes-policy" : "/api/groups/excludes-policy";
  await fetchJSON(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_id: groupId, policy_id: policyId }),
  });
}

function ctxSection(title, items, onClick, labelBuilder) {
  const section = document.createElement("div");
  const heading = document.createElement("div");
  heading.className = "ctx-section-title";
  heading.textContent = title;
  section.appendChild(heading);

  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "ctx-empty";
    empty.textContent = "None";
    section.appendChild(empty);
    return section;
  }

  for (const item of items) {
    const btn = document.createElement("button");
    btn.className = "ctx-item";
    btn.textContent = labelBuilder(item);
    btn.addEventListener("click", async () => {
      await onClick(item);
    });
    section.appendChild(btn);
  }
  return section;
}

async function showUserContextMenu(userNodeData, viewPoint) {
  const userId = userNodeData?.properties?.userId;
  if (!userId) return;
  const menu = document.getElementById("userContextMenu");
  menu.classList.remove("hidden");
  menu.innerHTML = "<div class='ctx-title'>Loading group options...</div>";
  menu.style.left = `${Math.max(8, viewPoint.x)}px`;
  menu.style.top = `${Math.max(8, viewPoint.y)}px`;

  try {
    const options = await fetchJSON(`/api/users/${encodeURIComponent(userId)}/group-options`);
    menu.innerHTML = "";
    const title = document.createElement("div");
    title.className = "ctx-title";
    title.textContent = `User: ${userId}`;
    menu.appendChild(title);
    menu.appendChild(
      ctxSection(
        "Entitle to",
        options.entitle_to || [],
        async (g) => {
          try {
            await submitMembership("entitle", userId, g.group_id);
            setStatus(`Entitled ${userId} to ${g.group_id}`);
            hideUserContextMenu();
            await loadGraph();
            await loadSelectors();
          } catch (err) {
            setStatus(`Failed to entitle: ${err.message}`, true);
          }
        },
        (g) => `${g.group_name || g.group_id} (${g.group_id})`
      )
    );
    menu.appendChild(
      ctxSection(
        "Revoke from",
        options.revoke_from || [],
        async (g) => {
          try {
            await submitMembership("revoke", userId, g.group_id);
            setStatus(`Revoked ${userId} from ${g.group_id}`);
            hideUserContextMenu();
            await loadGraph();
            await loadSelectors();
          } catch (err) {
            setStatus(`Failed to revoke: ${err.message}`, true);
          }
        },
        (g) => `${g.group_name || g.group_id} (${g.group_id})`
      )
    );
  } catch (err) {
    menu.innerHTML = `<div class='ctx-title'>Failed to load options</div><div class='ctx-empty'>${escapeHtml(String(err.message))}</div>`;
  }
}

async function showGroupContextMenu(groupNodeData, viewPoint) {
  const groupId = groupNodeData?.properties?.policyGroupId;
  const groupName = groupNodeData?.properties?.policyGroupName || groupId;
  if (!groupId) return;
  const menu = document.getElementById("userContextMenu");
  menu.classList.remove("hidden");
  menu.innerHTML = "<div class='ctx-title'>Loading policy options...</div>";
  menu.style.left = `${Math.max(8, viewPoint.x)}px`;
  menu.style.top = `${Math.max(8, viewPoint.y)}px`;

  try {
    const options = await fetchJSON(`/api/groups/${encodeURIComponent(groupId)}/user-options`);
    menu.innerHTML = "";
    const title = document.createElement("div");
    title.className = "ctx-title";
    title.textContent = `Group: ${groupName} (${groupId})`;
    menu.appendChild(title);
    menu.appendChild(
      ctxSection(
        "Includes policy",
        options.including_policies || [],
        async (p) => {
          try {
            await submitGroupPolicy("include", groupId, p.policy_id);
            setStatus(`Included ${p.policy_id} in ${groupId}`);
            hideUserContextMenu();
            await loadGraph();
          } catch (err) {
            setStatus(`Failed to include policy: ${err.message}`, true);
          }
        },
        (p) => `${p.policy_name || p.policy_id} (${p.policy_id})`
      )
    );
    menu.appendChild(
      ctxSection(
        "Excludes policy",
        options.excluding_policies || [],
        async (p) => {
          try {
            await submitGroupPolicy("exclude", groupId, p.policy_id);
            setStatus(`Excluded ${p.policy_id} from ${groupId}`);
            hideUserContextMenu();
            await loadGraph();
          } catch (err) {
            setStatus(`Failed to exclude policy: ${err.message}`, true);
          }
        },
        (p) => `${p.policy_name || p.policy_id} (${p.policy_id})`
      )
    );
  } catch (err) {
    menu.innerHTML = `<div class='ctx-title'>Failed to load options</div><div class='ctx-empty'>${escapeHtml(String(err.message))}</div>`;
  }
}

function setSelection(title, obj) {
  document.getElementById("selectionTitle").textContent = title;
  const tbody = document.querySelector("#propertiesTable tbody");
  const src = obj || {};
  const entries = [];
  const hiddenKeys = new Set(["key", "label", "labels", "group", "category"]);
  const isTable = src.label === "Table";
  const isColumn = src.label === "Column";

  if (isTable) {
    const tableProps = src.properties || {};
    Object.entries(tableProps).forEach(([k, v]) => {
      if (hiddenKeys.has(k)) return;
      entries.push([k, v]);
    });
  } else if (isColumn) {
    const columnProps = src.properties || {};
    Object.entries(columnProps).forEach(([k, v]) => {
      if (hiddenKeys.has(k)) return;
      entries.push([`column.${k}`, v]);
    });

    const tableNode = src.group && state.nodeByKey.has(src.group) ? state.nodeByKey.get(src.group) : null;
    const tableProps = (tableNode && tableNode.properties) || {};
    Object.entries(tableProps).forEach(([k, v]) => {
      if (hiddenKeys.has(k)) return;
      entries.push([`table.${k}`, v]);
    });
  } else {
    Object.entries(src).forEach(([k, v]) => {
      if (k === "properties" && v && typeof v === "object" && !Array.isArray(v)) {
        Object.entries(v).forEach(([pk, pv]) => {
          if (hiddenKeys.has(pk)) return;
          entries.push([pk, pv]);
        });
        return;
      }
      if (k !== "properties" && !hiddenKeys.has(k)) {
        entries.push([k, v]);
      }
    });
  }

  if (!entries.length) {
    tbody.innerHTML = "<tr><td colspan='2'>No properties</td></tr>";
    return;
  }
  const rows = entries
    .map(([k, v]) => {
      const value = typeof v === "object" ? JSON.stringify(v) : String(v);
      return `<tr><td>${escapeHtml(String(k))}</td><td>${escapeHtml(value)}</td></tr>`;
    })
    .join("");
  tbody.innerHTML = rows;
}

function labelText(node) {
  const p = node.properties || {};
  if (node.label === "User") return p.userId || "User";
  if (node.label === "PolicyGroup") return p.policyGroupName || p.policyGroupId || "PolicyGroup";
  if (node.label === "Policy") return p.policyName || p.policyId || "Policy";
  if (node.label === "Schema") return p.schemaName || "Schema";
  if (node.label === "Table") return p.tableName || "Table";
  if (node.label === "Column") return p.columnName || "Column";
  return node.label || "Node";
}

function iconByLabel(label) {
  if (label === "User") return "/static/icons/user.svg";
  if (label === "PolicyGroup") return "/static/icons/group.svg";
  if (label === "Policy") return "/static/icons/policy.svg";
  if (label === "Schema" || label === "RelationalDatabase") return "/static/icons/database.svg";
  if (label === "Table") return "/static/icons/table.svg";
  return "";
}

function initDiagram() {
  const diagram = $(go.Diagram, "graphDiv", {
    "undoManager.isEnabled": false,
    "animationManager.isEnabled": true,
    // Keep a valid layout instance but disable automatic re-layout.
    layout: $(go.ForceDirectedLayout, { isInitial: false, isOngoing: false }),
  });
  diagram.addDiagramListener("BackgroundContextClicked", () => hideUserContextMenu());
  diagram.addDiagramListener("BackgroundSingleClicked", () => hideUserContextMenu());

  diagram.nodeTemplate = $(
    go.Node,
    "Auto",
    {
      selectionChanged: (part) => {
        if (!part.isSelected) return;
        const d = part.data;
        setSelection(`Node: ${d.label}`, d);
      },
      contextClick: (e, obj) => {
        const p = e.diagram.lastInput.viewPoint;
        handleContextForData(obj.part && obj.part.data, p);
      },
    },
    $(
      go.Shape,
      "RoundedRectangle",
      {
        strokeWidth: 1,
        stroke: "#1f2933",
      },
      new go.Binding("fill", "label", (label) => colorByLabel[label] || colorByLabel.Node)
    ),
    $(
      go.Panel,
      "Horizontal",
      { margin: 8, defaultAlignment: go.Spot.Center },
      $(
        go.Picture,
        { width: 14, height: 14, margin: new go.Margin(0, 5, 0, 0) },
        new go.Binding("source", "label", iconByLabel)
      ),
      $(
        go.TextBlock,
        {
          stroke: "#111111",
          font: "12px sans-serif",
          maxSize: new go.Size(165, NaN),
          wrap: go.Wrap.Fit,
        },
        new go.Binding("text", "", labelText)
      )
    )
  );

  diagram.groupTemplateMap.add(
    "TableGroup",
    $(
      go.Group,
      "Auto",
      {
        layout: $(go.GridLayout, {
          wrappingColumn: 1,
          spacing: new go.Size(2, 2),
          alignment: go.GridLayout.Position,
        }),
        computesBoundsAfterDrag: true,
        selectionChanged: (part) => {
          if (!part.isSelected) return;
          const d = part.data;
          setSelection(`Node: ${d.label}`, d);
        },
        contextClick: (e, obj) => {
          const p = e.diagram.lastInput.viewPoint;
          handleContextForData(obj.part && obj.part.data, p);
        },
      },
      $(go.Shape, "RoundedRectangle", { fill: "#fff5f5", stroke: "#7f1d1d", strokeWidth: 1.2 }),
      $(
        go.Panel,
        "Vertical",
        { margin: 6, defaultAlignment: go.Spot.Left },
        $(
          go.Panel,
          "Horizontal",
          { margin: new go.Margin(2, 4, 6, 4), defaultAlignment: go.Spot.Center },
          $(
            go.Picture,
            { width: 14, height: 14, margin: new go.Margin(0, 6, 0, 0) },
            new go.Binding("source", "label", iconByLabel)
          ),
          $(
            go.TextBlock,
            {
              font: "bold 12px sans-serif",
              stroke: "#7f1d1d",
            },
            new go.Binding("text", "", (d) => labelText(d))
          )
        ),
        $(go.Placeholder, { padding: 4 })
      )
    )
  );

  diagram.nodeTemplateMap.add(
    "ColumnNode",
    $(
      go.Node,
      "Auto",
      {
        selectionChanged: (part) => {
          if (!part.isSelected) return;
          const d = part.data;
          setSelection(`Node: ${d.label}`, d);
        },
        contextClick: (e, obj) => {
          const p = e.diagram.lastInput.viewPoint;
          handleContextForData(obj.part && obj.part.data, p);
        },
      },
      $(go.Shape, "RoundedRectangle", {
        fill: "#58d68d",
        stroke: "#065f46",
        strokeWidth: 1,
        portId: "",
        fromLinkable: true,
        toLinkable: true,
        fromSpot: go.Spot.AllSides,
        toSpot: go.Spot.AllSides,
      }),
      $(
        go.Panel,
        "Horizontal",
        { margin: 6, defaultAlignment: go.Spot.Center },
        $(
          go.Picture,
          { width: 13, height: 13, margin: new go.Margin(0, 5, 0, 0) },
          new go.Binding("source", "label", iconByLabel)
        ),
        $(
          go.TextBlock,
          {
            stroke: "#0b1f14",
            font: "11px sans-serif",
            maxSize: new go.Size(145, NaN),
            wrap: go.Wrap.Fit,
          },
          new go.Binding("text", "", labelText)
        )
      )
    )
  );

  diagram.linkTemplate = $(
    go.Link,
    {
      curve: go.Curve.Bezier,
      fromSpot: go.Spot.Right,
      toSpot: go.Spot.Left,
      selectionChanged: (part) => {
        if (!part.isSelected) return;
        setSelection(`Relationship: ${part.data.type}`, part.data);
      },
    },
    $(go.Shape, { strokeWidth: 1.8 }, new go.Binding("stroke", "type", linkColorByType)),
    $(go.Shape, { toArrow: "Standard", stroke: null }, new go.Binding("fill", "type", linkColorByType)),
    $(
      go.Panel,
      "Auto",
      {
        segmentIndex: NaN,
        segmentFraction: 0.5,
      },
      new go.Binding("visible", "type", (t) => t === "hasRowRule" || t === "hasColumnRule"),
      $(go.Shape, "RoundedRectangle", { fill: "#ffffff", stroke: "#d9e2ec" }),
      $(
        go.TextBlock,
        {
          margin: 4,
          font: "bold 11px sans-serif",
        },
        new go.Binding("stroke", "type", linkColorByType),
        new go.Binding("text", "type")
      )
    )
  );

  state.graph = diagram;
}

function laneForLabel(label) {
  if (label === "User") return "left";
  if (label === "PolicyGroup") return "group";
  if (label === "Policy") return "policy";
  if (label === "Table" || label === "Column") return "table";
  return "database";
}

function laneRankForLabel(label) {
  const lane = laneForLabel(label);
  if (lane === "left") return 1;
  if (lane === "group") return 2;
  if (lane === "policy") return 3;
  if (lane === "table") return 4;
  return 5;
}

function applyLaneLayout(diagram) {
  const viewWidth = diagram.viewportBounds.width > 0 ? diagram.viewportBounds.width : 1200;
  const viewHeight =
    diagram.viewportBounds.height > 0
      ? diagram.viewportBounds.height
      : (diagram.div ? diagram.div.clientHeight : 800);
  const laneWidth = Math.max(190, Math.floor(viewWidth / 5));
  const laneX = {
    left: 20,
    group: laneWidth + 20,
    policy: laneWidth * 2 + 20,
    table: laneWidth * 3 + 20,
    database: laneWidth * 4 + 20,
  };
  const laneBuckets = {
    left: [],
    group: [],
    policy: [],
    table: [],
    database: [],
  };
  const laneY = {};

  diagram.commit((d) => {
    d.nodes.each((node) => {
      if (node.containingGroup) return;
      const label = node.data.label || "Node";
      const lane = laneForLabel(label);
      laneBuckets[lane].push(node);
    });

    Object.keys(laneBuckets).forEach((lane) => {
      const spacing = 20;
      const heights = laneBuckets[lane].map((n) => Math.max(80, (n.actualBounds.height || 52) + 28));
      const totalHeight =
        heights.reduce((sum, h) => sum + h, 0) + Math.max(0, laneBuckets[lane].length - 1) * spacing;
      laneY[lane] = Math.max(56, (viewHeight - totalHeight) / 2);
    });

    Object.keys(laneBuckets).forEach((lane) => {
      for (const node of laneBuckets[lane]) {
        node.move(new go.Point(laneX[lane], laneY[lane]));
        laneY[lane] += Math.max(80, (node.actualBounds.height || 52) + 28) + 20;
      }
    });
  }, "lane-layout");
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText} ${body}`);
  }
  return res.json();
}

async function loadGraph() {
  setStatus("Loading graph...");
  try {
    const graph = await fetchJSON("/api/graph");
    const links = graph.links || [];
    const belongsToTable = links.filter((l) => l.type === "belongsToTable");
    let renderedLinks = links.filter((l) => l.type !== "belongsToTable");
    const tableByColumn = new Map();
    for (const rel of belongsToTable) {
      tableByColumn.set(rel.from, rel.to);
    }

    const nodes = (graph.nodes || []).map((n) => {
      const next = { ...n };
      if (next.label === "Table") {
        next.isGroup = true;
        next.category = "TableGroup";
      }
      if (next.label === "Column") {
        next.category = "ColumnNode";
        const parentTable = tableByColumn.get(next.key);
        if (parentTable) next.group = parentTable;
      }
      return next;
    });
    state.nodeByKey = new Map(nodes.map((n) => [n.key, n]));

    const nodeByKey = new Map(nodes.map((n) => [n.key, n]));
    renderedLinks = renderedLinks.map((l) => {
      const fromNode = nodeByKey.get(l.from);
      const toNode = nodeByKey.get(l.to);
      if (!fromNode || !toNode) return l;
      const fromRank = laneRankForLabel(fromNode.label);
      const toRank = laneRankForLabel(toNode.label);
      if (fromRank > toRank) {
        return { ...l, from: l.to, to: l.from };
      }
      return l;
    });

    state.graph.model = new go.GraphLinksModel(nodes, renderedLinks);
    setTimeout(() => applyLaneLayout(state.graph), 0);
    setStatus(`Loaded ${nodes.length} nodes and ${renderedLinks.length} relationships.`);
  } catch (err) {
    setStatus(`Failed to load graph: ${err.message}`, true);
  }
}

function fillSelect(selectEl, items, valueKey, labelFn) {
  selectEl.innerHTML = "";
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item[valueKey];
    opt.textContent = labelFn(item);
    selectEl.appendChild(opt);
  }
}

async function loadSelectors() {
  try {
    const [users, groups] = await Promise.all([fetchJSON("/api/users"), fetchJSON("/api/groups")]);
    fillSelect(document.getElementById("userSelect"), users, "user_id", (u) => u.user_id);
    fillSelect(
      document.getElementById("groupSelect"),
      groups,
      "group_id",
      (g) => `${g.group_name || g.group_id} (${g.group_id})`
    );
  } catch (err) {
    setStatus(`Failed to load users/groups: ${err.message}`, true);
  }
}

async function applyMembership(action) {
  const userId = document.getElementById("userSelect").value;
  const groupId = document.getElementById("groupSelect").value;
  if (!userId || !groupId) {
    setStatus("Please select both user and group.", true);
    return;
  }
  setStatus(`${action} in progress...`);
  try {
    await submitMembership(action === "Entitle" ? "entitle" : "revoke", userId, groupId);
    setStatus(`${action} succeeded for ${userId} -> ${groupId}`);
    await loadGraph();
    await loadSelectors();
  } catch (err) {
    setStatus(`${action} failed: ${err.message}`, true);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  initDiagram();
  // Safari compatibility: normalize native contextmenu to our custom menu.
  const graphDiv = document.getElementById("graphDiv");
  const traceEvent = (name) => (evt) => {
    debugLog(
      [
        `event=${name}`,
        `button=${evt.button ?? "na"}`,
        `buttons=${evt.buttons ?? "na"}`,
        `ctrl=${Boolean(evt.ctrlKey)}`,
        `meta=${Boolean(evt.metaKey)}`,
        `pointer=${evt.pointerType || "na"}`,
        `client=(${evt.clientX ?? "na"},${evt.clientY ?? "na"})`,
      ].join(" | ")
    );
  };
  graphDiv.addEventListener("pointerdown", traceEvent("pointerdown"), { capture: true });
  graphDiv.addEventListener("pointerup", traceEvent("pointerup"), { capture: true });
  graphDiv.addEventListener("mousedown", traceEvent("mousedown"), { capture: true });
  graphDiv.addEventListener("mouseup", traceEvent("mouseup"), { capture: true });
  graphDiv.addEventListener("click", traceEvent("click"), { capture: true });
  graphDiv.addEventListener("auxclick", traceEvent("auxclick"), { capture: true });
  graphDiv.addEventListener("contextmenu", openContextMenuFromDomEvent, { passive: false, capture: true });
  document.addEventListener(
    "contextmenu",
    (evt) => {
      if (graphDiv.contains(evt.target)) {
        openContextMenuFromDomEvent(evt);
      }
    },
    { passive: false, capture: true }
  );
  // Safari fallback: Ctrl+Click is often treated as a regular click.
  graphDiv.addEventListener("click", (evt) => {
    if (evt.ctrlKey) openContextMenuFromDomEvent(evt);
  });
  // Some Safari setups dispatch auxclick for secondary click.
  graphDiv.addEventListener("auxclick", (evt) => {
    if (evt.button === 2) openContextMenuFromDomEvent(evt);
  });
  graphDiv.addEventListener("mousedown", (evt) => {
    if (evt.button === 2 || evt.ctrlKey) {
      openContextMenuFromDomEvent(evt);
    }
  });
  document.addEventListener("click", (evt) => {
    if (Date.now() - state.lastContextOpenTs < 250) return;
    const menu = document.getElementById("userContextMenu");
    if (!menu.contains(evt.target)) hideUserContextMenu();
  });
  document.getElementById("assignBtn").addEventListener("click", () => applyMembership("Entitle"));
  document.getElementById("revokeBtn").addEventListener("click", () => applyMembership("Revoke"));
  document.getElementById("refreshBtn").addEventListener("click", loadGraph);
  await loadSelectors();
  await loadGraph();
});
