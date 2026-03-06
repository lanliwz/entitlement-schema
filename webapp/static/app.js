/* global go */

const $ = go.GraphObject.make;

const state = {
  graph: null,
  nodeByKey: new Map(),
  lastContextOpenTs: 0,
  baseGraph: null,
  activeTab: "dashboard",
  resizeSession: null,
};

const laneMenuConfig = {
  left: {
    title: "User lane",
    actions: [
      { verb: "Add", entityType: "user", label: "Add user" },
      { verb: "Delete", entityType: "user", label: "Delete user" },
    ],
  },
  group: {
    title: "Group lane",
    actions: [
      { verb: "Add", entityType: "group", label: "Add group" },
      { verb: "Delete", entityType: "group", label: "Delete group" },
    ],
  },
  policy: {
    title: "Policy lane",
    actions: [
      { verb: "Add", entityType: "policy", label: "Add policy" },
      { verb: "Delete", entityType: "policy", label: "Delete policy" },
    ],
  },
  table: {
    title: "Table / Column lane",
    actions: [
      { verb: "Add", entityType: "table", label: "Add table" },
      { verb: "Delete", entityType: "table", label: "Delete table" },
      { verb: "Add", entityType: "column", label: "Add column" },
      { verb: "Delete", entityType: "column", label: "Delete column" },
    ],
  },
  database: {
    title: "Database lane",
    actions: [
      { verb: "Add", entityType: "database", label: "Add database" },
      { verb: "Delete", entityType: "database", label: "Delete database" },
    ],
  },
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

function isCompactLayout() {
  return window.innerWidth <= 1100;
}

function startPaneResize(side, evt) {
  if (isCompactLayout()) return;
  const layout = document.querySelector(".layout");
  if (!layout) return;
  const divider = evt.currentTarget;
  const rect = layout.getBoundingClientRect();
  state.resizeSession = {
    side,
    layoutLeft: rect.left,
    layoutWidth: rect.width,
    divider,
  };
  divider.classList.add("dragging");
  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";
}

function handlePaneResize(evt) {
  const session = state.resizeSession;
  if (!session || isCompactLayout()) return;
  const minLeft = 240;
  const minCenter = 320;
  const minRight = 280;
  const total = session.layoutWidth;
  const x = evt.clientX - session.layoutLeft;

  if (session.side === "left") {
    const nextLeft = Math.max(minLeft, Math.min(x, total - minCenter - minRight - 16));
    document.documentElement.style.setProperty("--left-panel-width", `${Math.round(nextLeft)}px`);
    return;
  }

  const nextRight = Math.max(minRight, Math.min(total - x, total - minCenter - minLeft - 16));
  document.documentElement.style.setProperty("--right-panel-width", `${Math.round(nextRight)}px`);
}

function stopPaneResize() {
  if (!state.resizeSession) return;
  state.resizeSession.divider.classList.remove("dragging");
  state.resizeSession = null;
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
}

function setResultTitle(text) {
  const el = document.getElementById("resultTitle");
  if (el) el.textContent = text;
}

function clearTableResult(message = "Run Chat Explorer to render tabular data here.") {
  const el = document.getElementById("tableResult");
  if (!el) return;
  el.className = "table-result-empty";
  el.textContent = message;
}

function renderTableResult(table, title = "Tabular result") {
  const el = document.getElementById("tableResult");
  if (!el) return;
  const columns = table.columns || [];
  const rows = table.rows || [];
  setResultTitle(title);
  if (!columns.length) {
    clearTableResult("No rows returned.");
    return;
  }
  const head = columns.map((column) => `<th>${escapeHtml(String(column))}</th>`).join("");
  const body = rows
    .map((row) => {
      const cells = columns
        .map((column) => {
          const value = row[column];
          const text = typeof value === "object" ? JSON.stringify(value) : String(value ?? "");
          return `<td>${escapeHtml(text)}</td>`;
        })
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");
  el.className = "";
  el.innerHTML = `<table class="kv-table"><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="${columns.length}">No rows</td></tr>`}</tbody></table>`;
}

function debugLog(message) {
  void message;
}

function hideUserContextMenu() {
  const menu = document.getElementById("userContextMenu");
  menu.classList.add("hidden");
  menu.innerHTML = "";
}

function hideLaneContextMenu() {
  const menu = document.getElementById("laneContextMenu");
  menu.classList.add("hidden");
  menu.innerHTML = "";
}

function handleContextForData(data, viewPoint) {
  if (!data) {
    hideUserContextMenu();
    return;
  }
  hideLaneContextMenu();
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

async function submitEntityMutation(action, entityType, entityId = "", properties = {}) {
  const endpoint = action === "create" ? "/api/entities/create" : "/api/entities/delete";
  await fetchJSON(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      entity_type: entityType,
      entity_id: entityId,
      properties,
    }),
  });
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

function openLaneContextMenu(lane, anchorEl) {
  const config = laneMenuConfig[lane];
  if (!config || !anchorEl) return;
  hideUserContextMenu();

  const rect = anchorEl.getBoundingClientRect();
  const menu = document.getElementById("laneContextMenu");
  menu.classList.remove("hidden");
  menu.innerHTML = "";
  menu.style.left = `${Math.max(8, rect.left)}px`;
  menu.style.top = `${Math.max(8, rect.bottom + 6)}px`;

  const title = document.createElement("div");
  title.className = "ctx-title";
  title.textContent = config.title;
  menu.appendChild(title);

  for (const action of config.actions) {
    const btn = document.createElement("button");
    btn.className = "ctx-item";
    btn.textContent = action.label;
    btn.addEventListener("click", async () => {
      await handleLaneEntityAction({ ...action, lane });
    });
    menu.appendChild(btn);
  }
}

function setLaneMenuPosition(menu, anchorEl) {
  const rect = anchorEl.getBoundingClientRect();
  menu.style.left = `${Math.max(8, rect.left)}px`;
  menu.style.top = `${Math.max(8, rect.bottom + 6)}px`;
}

function formatEntityChoice(entity) {
  const props = entity.properties || {};
  const primary =
    entity.display_name || props.policyName || props.policyGroupName || props.tableName || props.columnName || props.schemaName || entity.entity_id;
  return primary === entity.entity_id ? entity.entity_id : `${primary} (${entity.entity_id})`;
}

function laneMenuBackButton(onClick) {
  const btn = document.createElement("button");
  btn.className = "ctx-item ctx-back";
  btn.textContent = "Back";
  btn.addEventListener("click", onClick);
  return btn;
}

function laneMenuActionButton(label, onClick, className = "") {
  const btn = document.createElement("button");
  btn.className = className ? `ctx-item ${className}` : "ctx-item";
  btn.textContent = label;
  btn.addEventListener("click", onClick);
  return btn;
}

async function showAddEntityForm(action, anchorEl) {
  const menu = document.getElementById("laneContextMenu");
  const meta = await fetchJSON(`/api/entities/${encodeURIComponent(action.entityType)}/meta`);
  menu.innerHTML = "";
  setLaneMenuPosition(menu, anchorEl);

  const title = document.createElement("div");
  title.className = "ctx-title";
  title.textContent = action.label;
  menu.appendChild(title);
  menu.appendChild(laneMenuBackButton(() => openLaneContextMenu(anchorEl.dataset.lane, anchorEl)));

  const form = document.createElement("form");
  form.className = "ctx-form";
  const requiredFields = (meta.fields || []).filter((field) => field.required);
  const optionalFields = (meta.fields || []).filter((field) => !field.required);

  const appendFieldGroup = (titleText, fields) => {
    if (!fields.length) return;
    const titleEl = document.createElement("div");
    titleEl.className = "ctx-section-title";
    titleEl.textContent = titleText;
    form.appendChild(titleEl);
    for (const field of fields) {
      const label = document.createElement("label");
      label.className = "ctx-form-label";
      label.textContent = field.label;
      const input = document.createElement("input");
      input.className = "ctx-form-input";
      input.name = field.name;
      input.required = Boolean(field.required);
      input.placeholder = field.name;
      label.appendChild(input);
      form.appendChild(label);
    }
  };

  appendFieldGroup("Required properties", requiredFields);
  appendFieldGroup("Optional properties", optionalFields);

  const submit = laneMenuActionButton("Create", async (evt) => {
    evt.preventDefault();
    const data = new FormData(form);
    const properties = Object.fromEntries(
      [...data.entries()].map(([k, v]) => [k, String(v).trim()]).filter(([, v]) => v)
    );
    const missing = (meta.fields || []).filter((f) => f.required && !properties[f.name]);
    if (missing.length) {
      setStatus(`Missing required field: ${missing[0].label}`, true);
      return;
    }
    try {
      await submitEntityMutation("create", action.entityType, properties[meta.id_field], properties);
      setStatus(`Added ${action.entityType} ${properties[meta.id_field]}`);
      hideLaneContextMenu();
      await loadGraph();
      await loadSelectors();
    } catch (err) {
      setStatus(`Failed to add ${action.entityType}: ${err.message}`, true);
    }
  }, "ctx-primary");
  form.appendChild(submit);
  menu.appendChild(form);
}

async function showDeleteEntityChooser(action, anchorEl) {
  const menu = document.getElementById("laneContextMenu");
  const entities = await fetchJSON(`/api/entities/${encodeURIComponent(action.entityType)}`);
  menu.innerHTML = "";
  setLaneMenuPosition(menu, anchorEl);

  const title = document.createElement("div");
  title.className = "ctx-title";
  title.textContent = action.label;
  menu.appendChild(title);
  menu.appendChild(laneMenuBackButton(() => openLaneContextMenu(anchorEl.dataset.lane, anchorEl)));

  if (!entities.length) {
    const empty = document.createElement("div");
    empty.className = "ctx-empty";
    empty.textContent = "No entities found.";
    menu.appendChild(empty);
    return;
  }

  const select = document.createElement("select");
  select.className = "ctx-select";
  for (const entity of entities) {
    const opt = document.createElement("option");
    opt.value = entity.entity_id;
    opt.textContent = formatEntityChoice(entity);
    select.appendChild(opt);
  }
  menu.appendChild(select);

  const confirmWrap = document.createElement("div");
  confirmWrap.className = "ctx-confirm hidden";
  menu.appendChild(confirmWrap);

  const chooseBtn = laneMenuActionButton("Continue", () => {
    const entity = entities.find((item) => item.entity_id === select.value);
    if (!entity) return;
    confirmWrap.classList.remove("hidden");
    confirmWrap.innerHTML = "";
    const text = document.createElement("div");
    text.className = "ctx-empty";
    text.textContent = `Delete ${formatEntityChoice(entity)}?`;
    confirmWrap.appendChild(text);
    confirmWrap.appendChild(
      laneMenuActionButton("Confirm delete", async () => {
        try {
          await submitEntityMutation("delete", action.entityType, entity.entity_id);
          setStatus(`Deleted ${action.entityType} ${entity.entity_id}`);
          hideLaneContextMenu();
          await loadGraph();
          await loadSelectors();
        } catch (err) {
          setStatus(`Failed to delete ${action.entityType}: ${err.message}`, true);
        }
      }, "ctx-danger")
    );
  }, "ctx-primary");
  menu.appendChild(chooseBtn);
}

async function handleLaneEntityAction(action) {
  const anchorEl = document.querySelector(`.lane-header[data-lane="${action.lane}"]`);
  if (!anchorEl) return;
  try {
    if (action.verb === "Add") {
      await showAddEntityForm(action, anchorEl);
      return;
    }
    await showDeleteEntityChooser(action, anchorEl);
  } catch (err) {
    setStatus(`Failed to load ${action.entityType} action: ${err.message}`, true);
  }
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

function renderGraphPayload(graph, statusText) {
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
  setStatus(statusText || `Loaded ${nodes.length} nodes and ${renderedLinks.length} relationships.`);
}

async function loadGraph() {
  setStatus("Loading graph...");
  try {
    const graph = await fetchJSON("/api/graph");
    state.baseGraph = graph;
    renderGraphPayload(graph, `Loaded ${(graph.nodes || []).length} nodes and ${(graph.links || []).length} relationships.`);
  } catch (err) {
    setStatus(`Failed to load graph: ${err.message}`, true);
  }
}

function restoreBaseGraph() {
  if (!state.baseGraph) return;
  renderGraphPayload(state.baseGraph, "Restored base graph.");
}

async function loadDashboard() {
  try {
    const payload = await fetchJSON("/api/dashboard");
    const entityEl = document.getElementById("entityCounts");
    const relEl = document.getElementById("relationshipCounts");
    entityEl.innerHTML = (payload.entity_counts || [])
      .map((item) => `<div class="summary-item"><strong>${escapeHtml(item.entity_type)}</strong><span>${escapeHtml(String(item.count))}</span></div>`)
      .join("");
    relEl.innerHTML = (payload.relationship_counts || [])
      .map((item) => `<div class="summary-item"><strong>${escapeHtml(item.relationship_type)}</strong><span>${escapeHtml(String(item.count))}</span></div>`)
      .join("");
  } catch (err) {
    setStatus(`Failed to load dashboard: ${err.message}`, true);
  }
}

function activateTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.tabPanel === tab);
  });
}

async function runChatExplorer() {
  const question = document.getElementById("chatQuestion").value.trim();
  if (!question) {
    setStatus("Please enter a question for Chat Explorer.", true);
    return;
  }
  setStatus("Running Chat Explorer...");
  try {
    const result = await fetchJSON("/api/chat-explorer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    document.getElementById("chatCypher").textContent = result.cypher || "No query generated.";
    if (result.result_mode === "graph") {
      renderGraphPayload(result.graph || { nodes: [], links: [] }, `Chat Explorer returned ${result.row_count} graph rows.`);
      clearTableResult("Graph result rendered in the middle panel.");
      setResultTitle("No tabular result");
    } else {
      renderTableResult(result.table || { columns: [], rows: [] }, `Tabular result (${result.row_count} rows)`);
      restoreBaseGraph();
      setStatus(`Chat Explorer returned ${result.row_count} tabular rows.`);
    }
  } catch (err) {
    setStatus(`Chat Explorer failed: ${err.message}`, true);
  }
}

async function runSearch() {
  const term = document.getElementById("searchInput").value.trim();
  if (!term) {
    setStatus("Enter search text.", true);
    return;
  }
  setStatus("Searching...");
  try {
    const results = await fetchJSON(`/api/search?q=${encodeURIComponent(term)}`);
    const container = document.getElementById("searchResults");
    if (!results.length) {
      container.innerHTML = `<div class="table-result-empty">No matches found.</div>`;
      setStatus("No search matches found.");
      return;
    }
    container.innerHTML = "";
    for (const result of results) {
      const btn = document.createElement("button");
      btn.className = "search-item";
      const props = result.properties || {};
      const title =
        props.userId ||
        props.policyGroupName ||
        props.policyGroupId ||
        props.policyName ||
        props.policyId ||
        props.tableName ||
        props.tableId ||
        props.columnName ||
        props.columnId ||
        props.schemaName ||
        props.schemaId ||
        result.label;
      btn.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(result.label)}</span>`;
      btn.addEventListener("click", () => {
        setSelection(`Search: ${result.label}`, result);
        setStatus(`Loaded search result for ${title}`);
      });
      container.appendChild(btn);
    }
    setStatus(`Found ${results.length} search matches.`);
  } catch (err) {
    setStatus(`Search failed: ${err.message}`, true);
  }
}

function relationshipEndpointLabel(node) {
  const props = node.properties || {};
  return (
    props.userId ||
    props.policyGroupName ||
    props.policyGroupId ||
    props.policyName ||
    props.policyId ||
    props.tableName ||
    props.tableId ||
    props.columnName ||
    props.columnId ||
    props.schemaName ||
    props.schemaId ||
    node.label ||
    "Node"
  );
}

async function runRelationshipSearch() {
  const term = document.getElementById("relationshipSearchInput").value.trim();
  if (!term) {
    setStatus("Enter relationship search text.", true);
    return;
  }
  setStatus("Searching relationships...");
  try {
    const results = await fetchJSON(`/api/search/relationships?q=${encodeURIComponent(term)}`);
    const container = document.getElementById("relationshipSearchResults");
    if (!results.length) {
      container.innerHTML = `<div class="table-result-empty">No relationship matches found.</div>`;
      setStatus("No relationship matches found.");
      return;
    }
    container.innerHTML = "";
    for (const result of results) {
      const btn = document.createElement("button");
      btn.className = "search-item";
      const fromLabel = relationshipEndpointLabel(result.from || {});
      const toLabel = relationshipEndpointLabel(result.to || {});
      btn.innerHTML = `<strong>${escapeHtml(result.type)}</strong><span>${escapeHtml(`${fromLabel} -> ${toLabel}`)}</span>`;
      btn.addEventListener("click", () => {
        setSelection(`Relationship Search: ${result.type}`, {
          type: result.type,
          from: fromLabel,
          to: toLabel,
          properties: result.properties || {},
        });
        setStatus(`Loaded relationship result for ${result.type}`);
      });
      container.appendChild(btn);
    }
    setStatus(`Found ${results.length} relationship matches.`);
  } catch (err) {
    setStatus(`Relationship search failed: ${err.message}`, true);
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
    const laneMenu = document.getElementById("laneContextMenu");
    if (!laneMenu.contains(evt.target)) hideLaneContextMenu();
  });
  document.querySelectorAll(".lane-header").forEach((el) => {
    el.addEventListener("click", (evt) => {
      evt.preventDefault();
      evt.stopPropagation();
      openLaneContextMenu(el.dataset.lane, el);
    });
  });
  document.querySelectorAll(".pane-divider").forEach((divider) => {
    divider.addEventListener("pointerdown", (evt) => {
      evt.preventDefault();
      startPaneResize(divider.dataset.divider, evt);
    });
  });
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => activateTab(btn.dataset.tab));
  });
  document.getElementById("assignBtn").addEventListener("click", () => applyMembership("Entitle"));
  document.getElementById("revokeBtn").addEventListener("click", () => applyMembership("Revoke"));
  document.getElementById("refreshBtn").addEventListener("click", loadGraph);
  document.getElementById("runChatBtn").addEventListener("click", runChatExplorer);
  document.getElementById("searchBtn").addEventListener("click", runSearch);
  document.getElementById("relationshipSearchBtn").addEventListener("click", runRelationshipSearch);
  document.getElementById("searchInput").addEventListener("keydown", (evt) => {
    if (evt.key === "Enter") {
      evt.preventDefault();
      runSearch();
    }
  });
  document.getElementById("relationshipSearchInput").addEventListener("keydown", (evt) => {
    if (evt.key === "Enter") {
      evt.preventDefault();
      runRelationshipSearch();
    }
  });
  window.addEventListener("pointermove", handlePaneResize);
  window.addEventListener("pointerup", () => {
    const wasResizing = Boolean(state.resizeSession);
    stopPaneResize();
    if (wasResizing && state.graph) {
      setTimeout(() => applyLaneLayout(state.graph), 0);
    }
  });
  clearTableResult();
  activateTab("dashboard");
  await loadSelectors();
  await loadDashboard();
  await loadGraph();
});
