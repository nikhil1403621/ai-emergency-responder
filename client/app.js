// AI-Based Emergency Response System - Interactive Frontend Logic

const API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

// State Store
const state = {
  activeRole: 'citizen',
  trackedIncidentId: null,
  selectedQueueIncidentId: null,
  activeResponderUnitId: null,
  incidents: [],
  units: [],
  auditLogs: [],
  pendingDispatch: {
    unitId: null,
    unitName: null,
    incidentId: null
  }
};

// DOM References
const el = {
  roleTabs: document.querySelectorAll('.role-tab'),
  roleViews: document.querySelectorAll('.role-view'),
  disclaimerBanner: document.getElementById('disclaimerBanner'),
  btnDismissBanner: document.getElementById('btnDismissBanner'),
  wsStatusDot: document.getElementById('wsStatusDot'),
  wsStatusText: document.getElementById('wsStatusText'),
  queueBadge: document.getElementById('queueBadge'),
  queueSubBadge: document.getElementById('queueSubBadge'),
  toastContainer: document.getElementById('toastContainer'),

  // Citizen
  subtabCitizenForm: document.getElementById('subtabCitizenForm'),
  subtabCitizenTicket: document.getElementById('subtabCitizenTicket'),
  citizenFormCard: document.getElementById('citizenFormCard'),
  citizenTicketCard: document.getElementById('citizenTicketCard'),
  incidentForm: document.getElementById('incidentForm'),
  incidentDescription: document.getElementById('incidentDescription'),
  charCount: document.getElementById('charCount'),
  descError: document.getElementById('descError'),
  inputLat: document.getElementById('inputLat'),
  inputLon: document.getElementById('inputLon'),
  addressHint: document.getElementById('addressHint'),
  reporterName: document.getElementById('reporterName'),
  reporterContact: document.getElementById('reporterContact'),
  btnSubmitReport: document.getElementById('btnSubmitReport'),
  noTicketState: document.getElementById('noTicketState'),
  activeTicketDetails: document.getElementById('activeTicketDetails'),
  ticketLiveTag: document.getElementById('ticketLiveTag'),
  ticketId: document.getElementById('ticketId'),
  ticketStatusPill: document.getElementById('ticketStatusPill'),
  ticketCategory: document.getElementById('ticketCategory'),
  ticketUrgency: document.getElementById('ticketUrgency'),
  ticketUnitType: document.getElementById('ticketUnitType'),
  ticketConfidencePct: document.getElementById('ticketConfidencePct'),
  ticketConfidenceBar: document.getElementById('ticketConfidenceBar'),
  uncertaintyBadge: document.getElementById('uncertaintyBadge'),
  ticketReasoning: document.getElementById('ticketReasoning'),
  assignedUnitName: document.getElementById('assignedUnitName'),
  assignedUnitEta: document.getElementById('assignedUnitEta'),
  ticketEventsList: document.getElementById('ticketEventsList'),
  presetButtons: document.querySelectorAll('.preset-btn'),
  pinButtons: document.querySelectorAll('.pin-btn'),

  // Dispatcher
  subtabQueue: document.getElementById('subtabQueue'),
  subtabDossier: document.getElementById('subtabDossier'),
  dispatcherQueuePane: document.getElementById('dispatcherQueuePane'),
  dispatcherDossierPane: document.getElementById('dispatcherDossierPane'),
  btnBackToQueue: document.getElementById('btnBackToQueue'),
  btnRefreshIncidents: document.getElementById('btnRefreshIncidents'),
  filterStatus: document.getElementById('filterStatus'),
  filterUrgency: document.getElementById('filterUrgency'),
  incidentQueueList: document.getElementById('incidentQueueList'),
  dossierPlaceholder: document.getElementById('dossierPlaceholder'),
  dossierContent: document.getElementById('dossierContent'),
  dossierUrgencyBadge: document.getElementById('dossierUrgencyBadge'),
  dossierStatusBadge: document.getElementById('dossierStatusBadge'),
  dossierId: document.getElementById('dossierId'),
  btnReassessAI: document.getElementById('btnReassessAI'),
  selectNextStatus: document.getElementById('selectNextStatus'),
  duplicateAlertBox: document.getElementById('duplicateAlertBox'),
  duplicateCandidatesList: document.getElementById('duplicateCandidatesList'),
  dossierDescription: document.getElementById('dossierDescription'),
  dossierAddress: document.getElementById('dossierAddress'),
  dossierCoords: document.getElementById('dossierCoords'),
  dossierReporter: document.getElementById('dossierReporter'),
  dossierTimestamp: document.getElementById('dossierTimestamp'),
  dossierCategory: document.getElementById('dossierCategory'),
  dossierUrgency: document.getElementById('dossierUrgency'),
  dossierConfidenceScore: document.getElementById('dossierConfidenceScore'),
  dossierUncertaintyScore: document.getElementById('dossierUncertaintyScore'),
  dossierRecommendedUnit: document.getElementById('dossierRecommendedUnit'),
  dossierReasoningText: document.getElementById('dossierReasoningText'),
  unitsProximityList: document.getElementById('unitsProximityList'),
  dossierEventsList: document.getElementById('dossierEventsList'),

  // Responder
  selectActiveUnit: document.getElementById('selectActiveUnit'),
  activeUnitStatusTag: document.getElementById('activeUnitStatusTag'),
  noMissionBox: document.getElementById('noMissionBox'),
  activeMissionBox: document.getElementById('activeMissionBox'),
  missionUrgencyTag: document.getElementById('missionUrgencyTag'),
  missionIncidentId: document.getElementById('missionIncidentId'),
  missionIncidentStatus: document.getElementById('missionIncidentStatus'),
  missionDescription: document.getElementById('missionDescription'),
  missionLocation: document.getElementById('missionLocation'),
  btnMarkEnRoute: document.getElementById('btnMarkEnRoute'),
  btnMarkArrived: document.getElementById('btnMarkArrived'),
  btnMarkInProgress: document.getElementById('btnMarkInProgress'),
  btnMarkResolved: document.getElementById('btnMarkResolved'),
  telemetryLat: document.getElementById('telemetryLat'),
  telemetryLon: document.getElementById('telemetryLon'),
  telemetrySpeed: document.getElementById('telemetrySpeed'),
  btnSimulateDrive: document.getElementById('btnSimulateDrive'),
  btnSimulateHome: document.getElementById('btnSimulateHome'),

  // Radar & Audit
  radarIncidentsGroup: document.getElementById('radarIncidentsGroup'),
  radarUnitsGroup: document.getElementById('radarUnitsGroup'),
  radarTooltip: document.getElementById('radarTooltip'),
  auditStreamContainer: document.getElementById('auditStreamContainer'),
  btnClearAudit: document.getElementById('btnClearAudit'),

  // Dialog
  dispatchModal: document.getElementById('dispatchModal'),
  dispatchModalTitle: document.getElementById('dispatchModalTitle'),
  btnCloseModal: document.getElementById('btnCloseModal'),
  modalUnitName: document.getElementById('modalUnitName'),
  modalUnitEta: document.getElementById('modalUnitEta'),
  modalIncidentId: document.getElementById('modalIncidentId'),
  modalIncidentCategory: document.getElementById('modalIncidentCategory'),
  dispatcherIdInput: document.getElementById('dispatcherIdInput'),
  dispatcherNotes: document.getElementById('dispatcherNotes'),
  btnCancelDispatch: document.getElementById('btnCancelDispatch'),
  dispatchForm: document.getElementById('dispatchForm')
};

// Preset Scenarios
const PRESETS = {
  crash: {
    desc: "Multi-vehicle collision on highway near exit 4 with three cars involved. Visible flames coming from truck engine, driver trapped and bleeding.",
    lat: 12.9900,
    lon: 77.5700,
    address: "North Expressway Exit 4"
  },
  fire: {
    desc: "Commercial chemical warehouse fire with heavy black smoke and exploding containers. Fire spreading rapidly to adjacent office block.",
    lat: 12.9650,
    lon: 77.5850,
    address: "Downtown Industrial Park, Block 7"
  },
  cardiac: {
    desc: "Elderly commuter collapsed at metro platform, unconscious and not breathing. CPR initiated by bystanders, urgent medical emergency.",
    lat: 12.9850,
    lon: 77.6050,
    address: "East Metro Station Platform 2"
  },
  robbery: {
    desc: "Armed robbery in progress at jewelry retailer by two masked suspects carrying handguns. Store alarm sounding, occupants sheltering.",
    lat: 12.9716,
    lon: 77.5946,
    address: "Central Market Square, Shop 14"
  }
};

// -------------------------------------------------------------
// BANNER DISMISSAL
// -------------------------------------------------------------
if (el.btnDismissBanner) {
  el.btnDismissBanner.addEventListener('click', () => {
    el.disclaimerBanner.classList.add('dismissed');
  });
}

// -------------------------------------------------------------
// WEBSOCKET REAL-TIME SYNC
// -------------------------------------------------------------
let ws = null;
let wsReconnectTimer = null;

function initWebSocket() {
  const wsUrl = `${WS_BASE}/ws/incidents`;
  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      el.wsStatusDot.className = 'status-dot connected';
      el.wsStatusText.textContent = 'Live Feed Connected';
      logAudit({
        type: 'system',
        actor: 'WebSocket',
        text: 'Connected to live dispatch stream.'
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleLiveEvent(data);
      } catch (e) {
        console.error('Failed to parse WS payload:', e);
      }
    };

    ws.onclose = () => {
      el.wsStatusDot.className = 'status-dot disconnected';
      el.wsStatusText.textContent = 'Reconnecting...';
      if (!wsReconnectTimer) {
        wsReconnectTimer = setTimeout(() => {
          wsReconnectTimer = null;
          initWebSocket();
        }, 3000);
      }
    };

    ws.onerror = (err) => {
      console.warn('WebSocket encountered error:', err);
    };
  } catch (err) {
    console.error('WS Connection error:', err);
  }
}

function handleLiveEvent(data) {
  // Add to real-time audit log
  logAudit({
    type: data.type,
    actor: data.actor_role || 'System',
    text: getEventSummaryText(data)
  });

  // Toast notification for high-priority incidents
  if (data.type === 'incident_created') {
    showToast(`🚨 New ${data.urgency.toUpperCase()} Incident: ${data.category}`, data.urgency === 'critical' ? 'critical' : 'info');
  } else if (data.type === 'unit_assigned') {
    showToast(`🛡️ Unit ${data.unit_call_sign} Dispatched to ${data.incident_id.slice(0, 8)}`, 'info');
  }

  // Refresh data
  loadIncidents();
  loadUnits();

  // If active tracked citizen ticket matches
  if (state.trackedIncidentId && (data.incident_id === state.trackedIncidentId)) {
    fetchIncidentDetails(state.trackedIncidentId, true);
  }

  // If dossier incident matches
  if (state.selectedQueueIncidentId && (data.incident_id === state.selectedQueueIncidentId)) {
    loadDossier(state.selectedQueueIncidentId);
  }

  // If responder view active unit matches
  if (state.activeResponderUnitId) {
    updateResponderMissionView();
  }
}

function getEventSummaryText(data) {
  switch (data.type) {
    case 'incident_created':
      return `New report created [${data.incident_id.slice(0, 8)}] categorized as '${data.category}' (${data.urgency}).`;
    case 'status_changed':
      return `Incident [${data.incident_id.slice(0, 8)}] status changed from '${data.from_status}' to '${data.to_status}' by ${data.actor_role}.`;
    case 'unit_assigned':
      return `Unit ${data.unit_call_sign} assigned by dispatcher ${data.dispatcher_id}.`;
    case 'unit_location_updated':
      return `Unit ${data.call_sign} GPS location updated: (${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}).`;
    case 'incident_assessed':
      return `Triage refreshed for [${data.incident_id.slice(0, 8)}]: ${data.category} (conf: ${(data.confidence * 100).toFixed(0)}%).`;
    default:
      return JSON.stringify(data);
  }
}

// -------------------------------------------------------------
// NAVIGATION & TABS
// -------------------------------------------------------------
el.roleTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const targetRole = tab.dataset.role;
    switchView(targetRole);
  });
});

function switchView(role) {
  state.activeRole = role;
  el.roleTabs.forEach(t => t.classList.toggle('active', t.dataset.role === role));
  el.roleViews.forEach(v => {
    if (v.id === `view${capitalize(role)}`) {
      v.classList.add('active');
    } else {
      v.classList.remove('active');
    }
  });

  // Handle responsive view adaptation
  if (role === 'dispatcher') {
    loadIncidents();
    if (window.innerWidth <= 900) {
      if (!state.selectedQueueIncidentId) {
        showDispatcherMobilePane('queue');
      } else {
        showDispatcherMobilePane('dossier');
      }
    }
  } else if (role === 'citizen') {
    if (window.innerWidth <= 900) {
      if (!state.trackedIncidentId) {
        showCitizenMobilePane('form');
      } else {
        showCitizenMobilePane('ticket');
      }
    }
  } else if (role === 'responder') {
    loadUnits().then(() => updateResponderMissionView());
  } else if (role === 'radar') {
    renderTacticalRadar();
  }
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// -------------------------------------------------------------
// MOBILE SUB-NAVIGATION HANDLERS
// -------------------------------------------------------------
function showCitizenMobilePane(pane) {
  if (pane === 'form') {
    el.subtabCitizenForm.classList.add('active');
    el.subtabCitizenTicket.classList.remove('active');
    el.citizenFormCard.classList.remove('mobile-pane-hidden');
    el.citizenTicketCard.classList.add('mobile-pane-hidden');
  } else {
    el.subtabCitizenTicket.classList.add('active');
    el.subtabCitizenForm.classList.remove('active');
    el.citizenTicketCard.classList.remove('mobile-pane-hidden');
    el.citizenFormCard.classList.add('mobile-pane-hidden');
  }
}

if (el.subtabCitizenForm && el.subtabCitizenTicket) {
  el.subtabCitizenForm.addEventListener('click', () => showCitizenMobilePane('form'));
  el.subtabCitizenTicket.addEventListener('click', () => showCitizenMobilePane('ticket'));
}

function showDispatcherMobilePane(pane) {
  if (pane === 'queue') {
    if (el.subtabQueue) el.subtabQueue.classList.add('active');
    if (el.subtabDossier) el.subtabDossier.classList.remove('active');
    el.dispatcherQueuePane.classList.remove('mobile-pane-hidden');
    el.dispatcherDossierPane.classList.add('mobile-pane-hidden');
  } else {
    if (el.subtabDossier) el.subtabDossier.classList.add('active');
    if (el.subtabQueue) el.subtabQueue.classList.remove('active');
    el.dispatcherDossierPane.classList.remove('mobile-pane-hidden');
    el.dispatcherQueuePane.classList.add('mobile-pane-hidden');
  }
}

if (el.subtabQueue && el.subtabDossier) {
  el.subtabQueue.addEventListener('click', () => showDispatcherMobilePane('queue'));
  el.subtabDossier.addEventListener('click', () => showDispatcherMobilePane('dossier'));
}

if (el.btnBackToQueue) {
  el.btnBackToQueue.addEventListener('click', () => {
    showDispatcherMobilePane('queue');
  });
}

// Window resize listener to clear mobile hiding on larger screens
window.addEventListener('resize', () => {
  if (window.innerWidth > 900) {
    if (el.citizenFormCard) el.citizenFormCard.classList.remove('mobile-pane-hidden');
    if (el.citizenTicketCard) el.citizenTicketCard.classList.remove('mobile-pane-hidden');
    if (el.dispatcherQueuePane) el.dispatcherQueuePane.classList.remove('mobile-pane-hidden');
    if (el.dispatcherDossierPane) el.dispatcherDossierPane.classList.remove('mobile-pane-hidden');
  } else {
    if (state.activeRole === 'dispatcher') {
      showDispatcherMobilePane(state.selectedQueueIncidentId ? 'dossier' : 'queue');
    } else if (state.activeRole === 'citizen') {
      showCitizenMobilePane(state.trackedIncidentId ? 'ticket' : 'form');
    }
  }
});

// -------------------------------------------------------------
// CITIZEN VIEW: REPORTING & ACTIVE TICKET
// -------------------------------------------------------------
el.incidentDescription.addEventListener('input', () => {
  const len = el.incidentDescription.value.length;
  el.charCount.textContent = len;
  if (len >= 10) {
    el.descError.textContent = '';
  }
});

// Preset Buttons
el.presetButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const key = btn.dataset.preset;
    const preset = PRESETS[key];
    if (preset) {
      el.incidentDescription.value = preset.desc;
      el.inputLat.value = preset.lat;
      el.inputLon.value = preset.lon;
      el.addressHint.value = preset.address;
      el.charCount.textContent = preset.desc.length;
      el.descError.textContent = '';
    }
  });
});

// Landmark Shortcuts
el.pinButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    el.inputLat.value = btn.dataset.lat;
    el.inputLon.value = btn.dataset.lon;
    el.addressHint.value = btn.dataset.name;
  });
});

// Submit Emergency Report
el.incidentForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const desc = el.incidentDescription.value.trim();
  if (desc.length < 10) {
    el.descError.textContent = 'Description must be at least 10 characters.';
    el.incidentDescription.focus();
    return;
  }

  const payload = {
    description: desc,
    latitude: parseFloat(el.inputLat.value) || null,
    longitude: parseFloat(el.inputLon.value) || null,
    address_hint: el.addressHint.value.trim() || null,
    reporter_name: el.reporterName.value.trim() || null,
    reporter_contact: el.reporterContact.value.trim() || null
  };

  el.btnSubmitReport.disabled = true;
  el.btnSubmitReport.querySelector('.btn-text').textContent = 'Transmitting...';

  try {
    const response = await fetch(`${API_BASE}/incidents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to submit incident');
    }

    const data = await response.json();
    state.trackedIncidentId = data.id;

    // Display Active Ticket Card
    renderActiveTicket(data);
    showToast(`Report Transmitted. Assigned ID: ${data.id.slice(0, 8)}`, 'success');

    // On mobile screens, automatically navigate to Ticket tracking view
    if (window.innerWidth <= 900) {
      showCitizenMobilePane('ticket');
    }

    // Reset Form
    el.incidentDescription.value = '';
    el.charCount.textContent = '0';
    loadIncidents();
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    el.btnSubmitReport.disabled = false;
    el.btnSubmitReport.querySelector('.btn-text').textContent = 'Transmit Emergency Report';
  }
});

function renderActiveTicket(incident) {
  el.noTicketState.classList.add('hidden');
  el.activeTicketDetails.classList.remove('hidden');

  el.ticketId.textContent = incident.id;
  el.ticketLiveTag.textContent = incident.status.replace(/_/g, ' ').toUpperCase();
  el.ticketLiveTag.className = `status-badge status-${incident.status}`;
  el.ticketStatusPill.textContent = incident.status.replace(/_/g, ' ').toUpperCase();
  el.ticketStatusPill.className = `status-badge status-${incident.status}`;

  el.ticketCategory.textContent = incident.category.replace(/_/g, ' ').toUpperCase();
  el.ticketUrgency.textContent = incident.urgency.toUpperCase();
  el.ticketUrgency.className = `m-value text-${incident.urgency}`;

  if (incident.assessment) {
    const ass = incident.assessment;
    el.ticketUnitType.textContent = ass.recommended_unit_type.replace(/_/g, ' ').toUpperCase();
    const confPct = Math.round(ass.confidence * 100);
    const uncertPct = Math.round(ass.uncertainty * 100);
    el.ticketConfidencePct.textContent = `${confPct}%`;
    el.ticketConfidenceBar.style.width = `${confPct}%`;
    el.uncertaintyBadge.textContent = `Uncertainty: ${uncertPct}%`;
    el.ticketReasoning.textContent = ass.reasoning;
  }

  // Assigned unit
  if (incident.assigned_unit_id) {
    const unit = state.units.find(u => u.id === incident.assigned_unit_id);
    el.assignedUnitName.textContent = unit ? `Unit: ${unit.call_sign}` : `Unit: ${incident.assigned_unit_id}`;
    el.assignedUnitEta.textContent = 'Dispatched • In Transit';
  } else {
    el.assignedUnitName.textContent = 'Awaiting Dispatcher Assignment';
    el.assignedUnitEta.textContent = 'Pending Authorization';
  }

  // Load events
  loadTicketEvents(incident.id);
}

async function loadTicketEvents(incidentId) {
  try {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/events`);
    if (res.ok) {
      const events = await res.json();
      el.ticketEventsList.innerHTML = events.map(ev => `
        <li class="event-item">
          <span class="event-meta">${formatTimestamp(ev.timestamp)} • ${ev.actor_role}</span>
          <span class="event-desc">${escapeHtml(ev.details)}</span>
        </li>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading events:', err);
  }
}

// -------------------------------------------------------------
// DISPATCHER VIEW: QUEUE & DOSSIER
// -------------------------------------------------------------
async function loadIncidents() {
  try {
    let url = `${API_BASE}/incidents?limit=100`;
    if (el.filterStatus.value) url += `&status=${el.filterStatus.value}`;
    if (el.filterUrgency.value) url += `&urgency=${el.filterUrgency.value}`;

    const res = await fetch(url);
    if (!res.ok) return;

    state.incidents = await res.json();
    renderIncidentQueue(state.incidents);
    const unassignedCount = state.incidents.filter(i => !['resolved', 'closed', 'cancelled'].includes(i.status)).length;
    el.queueBadge.textContent = unassignedCount;
    if (el.queueSubBadge) el.queueSubBadge.textContent = unassignedCount;

    renderTacticalRadar();
  } catch (err) {
    console.error('Failed to load incidents:', err);
  }
}

el.btnRefreshIncidents.addEventListener('click', loadIncidents);
el.filterStatus.addEventListener('change', loadIncidents);
el.filterUrgency.addEventListener('change', loadIncidents);

function renderIncidentQueue(incidents) {
  if (incidents.length === 0) {
    el.incidentQueueList.innerHTML = `<div class="empty-state" style="padding: 24px;"><p>No incidents match the selected filter.</p></div>`;
    return;
  }

  el.incidentQueueList.innerHTML = incidents.map(inc => {
    const isSelected = inc.id === state.selectedQueueIncidentId;
    return `
      <div class="queue-card ${isSelected ? 'active' : ''}" data-id="${inc.id}">
        <div class="queue-card-header">
          <span class="urgency-badge badge-${inc.urgency}">${inc.urgency.toUpperCase()}</span>
          <span class="status-badge status-${inc.status}">${inc.status.replace(/_/g, ' ')}</span>
        </div>
        <div class="queue-card-desc">${escapeHtml(inc.description)}</div>
        <div class="queue-card-meta">
          <span>📍 ${inc.address_hint || 'Coordinates provided'}</span>
          <span>${formatRelativeTime(inc.created_at)}</span>
        </div>
      </div>
    `;
  }).join('');

  // Attach click listeners to cards
  el.incidentQueueList.querySelectorAll('.queue-card').forEach(card => {
    card.addEventListener('click', () => {
      loadDossier(card.dataset.id);
      // On mobile screens, automatically show the Dossier pane
      if (window.innerWidth <= 900) {
        showDispatcherMobilePane('dossier');
      }
    });
  });
}

async function loadDossier(incidentId) {
  state.selectedQueueIncidentId = incidentId;
  renderIncidentQueue(state.incidents); // update active highlight

  try {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}`);
    if (!res.ok) return;
    const inc = await res.json();

    el.dossierPlaceholder.classList.add('hidden');
    el.dossierContent.classList.remove('hidden');

    el.dossierId.textContent = inc.id;
    el.dossierUrgencyBadge.textContent = inc.urgency.toUpperCase();
    el.dossierUrgencyBadge.className = `urgency-badge badge-${inc.urgency}`;
    el.dossierStatusBadge.textContent = inc.status.replace(/_/g, ' ').toUpperCase();
    el.dossierStatusBadge.className = `status-badge status-${inc.status}`;

    el.dossierDescription.textContent = inc.description;
    el.dossierAddress.textContent = inc.address_hint || 'N/A';
    el.dossierCoords.textContent = (inc.latitude && inc.longitude) ? `${inc.latitude.toFixed(4)}, ${inc.longitude.toFixed(4)}` : 'Not provided';
    el.dossierReporter.textContent = inc.reporter_name ? `${inc.reporter_name} (${inc.reporter_contact || 'No contact'})` : 'Anonymous';
    el.dossierTimestamp.textContent = formatTimestamp(inc.created_at);

    // AI Box
    el.dossierCategory.textContent = inc.category.replace(/_/g, ' ').toUpperCase();
    el.dossierUrgency.textContent = inc.urgency.toUpperCase();
    el.dossierUrgency.className = `col-value text-${inc.urgency}`;

    if (inc.assessment) {
      const confPct = Math.round(inc.assessment.confidence * 100);
      const uncertPct = Math.round(inc.assessment.uncertainty * 100);
      el.dossierConfidenceScore.textContent = `${confPct}% Confidence`;
      el.dossierUncertaintyScore.textContent = `Uncertainty: ${uncertPct}%`;
      el.dossierRecommendedUnit.textContent = inc.assessment.recommended_unit_type.replace(/_/g, ' ').toUpperCase();
      el.dossierReasoningText.textContent = inc.assessment.reasoning;
    }

    // Duplicate Check Banner
    if (inc.duplicate_candidates && inc.duplicate_candidates.length > 0) {
      el.duplicateAlertBox.classList.remove('hidden');
      el.duplicateCandidatesList.innerHTML = inc.duplicate_candidates.map(dup => `
        <div class="candidate-item">
          <span><strong>Incident ${dup.incident_id.slice(0, 8)}</strong>: "${escapeHtml(dup.description.slice(0, 50))}..."</span>
          <span>Similarity: ${(dup.similarity_score * 100).toFixed(0)}% • ${dup.distance_km ? dup.distance_km.toFixed(1) + ' km' : 'Nearby'}</span>
        </div>
      `).join('');
    } else {
      el.duplicateAlertBox.classList.add('hidden');
    }

    // Load Proximity Units
    loadProximityUnits(inc);

    // Load Events Log
    loadDossierEvents(incidentId);

  } catch (err) {
    console.error('Error loading dossier:', err);
  }
}

async function loadProximityUnits(incident) {
  const lat = incident.latitude || 12.9716;
  const lon = incident.longitude || 77.5946;

  try {
    const res = await fetch(`${API_BASE}/units/nearby?latitude=${lat}&longitude=${lon}&max_distance_km=50`);
    if (!res.ok) return;
    const nearbyUnits = await res.json();

    if (nearbyUnits.length === 0) {
      el.unitsProximityList.innerHTML = `<p class="subtext">No response units currently within reach.</p>`;
      return;
    }

    el.unitsProximityList.innerHTML = nearbyUnits.map(unit => {
      const isAssignedToThis = incident.assigned_unit_id === unit.id;
      const isAvailable = unit.status === 'available';
      return `
        <div class="unit-card">
          <div class="unit-card-top">
            <span class="unit-card-title">${unit.call_sign}</span>
            <span class="status-badge status-${unit.status}">${unit.status}</span>
          </div>
          <div class="unit-card-details">
            <span>Type: <strong>${unit.unit_type.replace(/_/g, ' ')}</strong></span>
            <span>Dist: <strong>${unit.distance_km} km</strong> (~${unit.estimated_eta_minutes}m)</span>
          </div>
          <button 
            type="button" 
            class="btn btn-sm ${isAssignedToThis ? 'btn-success' : (isAvailable ? 'btn-primary' : 'btn-secondary')}"
            onclick="openDispatchModal('${unit.id}', '${escapeHtml(unit.call_sign)}', '${unit.estimated_eta_minutes}', '${incident.id}', '${incident.category}')"
            ${isAssignedToThis ? 'disabled' : ''}
          >
            ${isAssignedToThis ? '✅ Currently Assigned' : '⚡ Approve & Dispatch'}
          </button>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Error querying nearby units:', err);
  }
}

async function loadDossierEvents(incidentId) {
  try {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/events`);
    if (!res.ok) return;
    const events = await res.json();
    el.dossierEventsList.innerHTML = events.map(ev => `
      <li class="event-item">
        <span class="event-meta">${formatTimestamp(ev.timestamp)} • ${ev.actor_role} (${ev.actor_id})</span>
        <span class="event-desc">${escapeHtml(ev.details)}</span>
      </li>
    `).join('');
  } catch (err) {
    console.error('Error loading events:', err);
  }
}

// Re-Assess AI Button
el.btnReassessAI.addEventListener('click', async () => {
  if (!state.selectedQueueIncidentId) return;
  try {
    const res = await fetch(`${API_BASE}/incidents/${state.selectedQueueIncidentId}/assess`, {
      method: 'POST'
    });
    if (res.ok) {
      showToast('AI Triage Re-assessed successfully', 'info');
      loadDossier(state.selectedQueueIncidentId);
    }
  } catch (err) {
    alert(`Re-assessment failed: ${err.message}`);
  }
});

// Status Advance Dropdown
el.selectNextStatus.addEventListener('change', async () => {
  const targetStatus = el.selectNextStatus.value;
  if (!targetStatus || !state.selectedQueueIncidentId) return;

  try {
    const res = await fetch(`${API_BASE}/incidents/${state.selectedQueueIncidentId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: targetStatus,
        actor_role: 'dispatcher',
        actor_id: 'COMMANDER_DISPATCH_1',
        notes: `Dispatcher marked status as '${targetStatus}'.`
      })
    });

    if (!res.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Status transition rejected');
    }

    showToast(`Status updated to ${targetStatus}`, 'success');
    el.selectNextStatus.value = '';
    loadDossier(state.selectedQueueIncidentId);
    loadIncidents();
  } catch (err) {
    alert(`Status Update Rejected: ${err.message}`);
    el.selectNextStatus.value = '';
  }
});

// -------------------------------------------------------------
// DISPATCH MODAL & ASSIGNMENT (Modern Native Dialog + Fallback)
// -------------------------------------------------------------
window.openDispatchModal = function(unitId, unitName, etaMinutes, incidentId, category) {
  state.pendingDispatch = { unitId, unitName, incidentId };
  el.modalUnitName.textContent = unitName;
  el.modalUnitEta.textContent = `ETA ~ ${etaMinutes} mins`;
  el.modalIncidentId.textContent = incidentId;
  el.modalIncidentCategory.textContent = category.replace(/_/g, ' ').toUpperCase();
  el.dispatcherNotes.value = '';

  el.dispatchModal.showModal();
};

el.btnCloseModal.addEventListener('click', () => el.dispatchModal.close());
el.btnCancelDispatch.addEventListener('click', () => el.dispatchModal.close());

// Light-dismiss click outside fallback according to modern-web-guidance
if (!('closedBy' in HTMLDialogElement.prototype)) {
  el.dispatchModal.addEventListener('click', (event) => {
    if (event.target !== el.dispatchModal) return;
    const rect = el.dispatchModal.getBoundingClientRect();
    const isInside = (
      rect.top <= event.clientY &&
      event.clientY <= rect.top + rect.height &&
      rect.left <= event.clientX &&
      event.clientX <= rect.left + rect.width
    );
    if (!isInside) {
      el.dispatchModal.close();
    }
  });
}

// Confirm Dispatch
el.dispatchForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const { unitId, incidentId } = state.pendingDispatch;
  const dispatcherId = el.dispatcherIdInput.value.trim() || 'DISPATCH_OFFICER_01';
  const notes = el.dispatcherNotes.value.trim();

  try {
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        unit_id: unitId,
        dispatcher_id: dispatcherId,
        notes: notes || 'Authorized emergency rollout'
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Dispatch assignment failed');
    }

    el.dispatchModal.close();
    showToast(`Dispatch Authorized for Unit ${unitId}!`, 'success');
    loadDossier(incidentId);
    loadIncidents();
    loadUnits();
  } catch (err) {
    alert(`Assignment error: ${err.message}`);
  }
});

// -------------------------------------------------------------
// RESPONDER VIEW: MDT TERMINAL & SIMULATOR
// -------------------------------------------------------------
async function loadUnits() {
  try {
    const res = await fetch(`${API_BASE}/units`);
    if (!res.ok) return;
    state.units = await res.json();

    // Populate responder unit dropdown if needed
    const currentVal = el.selectActiveUnit.value;
    el.selectActiveUnit.innerHTML = state.units.map(u => `
      <option value="${u.id}">${u.call_sign} (${u.unit_type.replace(/_/g, ' ')}) - ${u.status.toUpperCase()}</option>
    `).join('');

    if (currentVal && state.units.some(u => u.id === currentVal)) {
      el.selectActiveUnit.value = currentVal;
    } else if (state.units.length > 0 && !state.activeResponderUnitId) {
      state.activeResponderUnitId = state.units[0].id;
      el.selectActiveUnit.value = state.activeResponderUnitId;
    }

    renderTacticalRadar();
  } catch (err) {
    console.error('Error loading units:', err);
  }
}

el.selectActiveUnit.addEventListener('change', () => {
  state.activeResponderUnitId = el.selectActiveUnit.value;
  updateResponderMissionView();
});

function updateResponderMissionView() {
  const activeUnit = state.units.find(u => u.id === state.activeResponderUnitId);
  if (!activeUnit) return;

  el.activeUnitStatusTag.textContent = activeUnit.status.toUpperCase();
  el.activeUnitStatusTag.className = `status-badge status-${activeUnit.status}`;

  el.telemetryLat.textContent = activeUnit.latitude.toFixed(4);
  el.telemetryLon.textContent = activeUnit.longitude.toFixed(4);

  if (activeUnit.assigned_incident_id) {
    el.noMissionBox.classList.add('hidden');
    el.activeMissionBox.classList.remove('hidden');

    // Fetch assigned incident
    fetch(`${API_BASE}/incidents/${activeUnit.assigned_incident_id}`)
      .then(res => res.json())
      .then(inc => {
        el.missionIncidentId.textContent = inc.id;
        el.missionIncidentStatus.textContent = inc.status.replace(/_/g, ' ').toUpperCase();
        el.missionIncidentStatus.className = `status-badge status-${inc.status}`;
        el.missionUrgencyTag.textContent = inc.urgency.toUpperCase();
        el.missionUrgencyTag.className = `urgency-badge badge-${inc.urgency}`;
        el.missionDescription.textContent = inc.description;
        el.missionLocation.textContent = inc.address_hint || `${inc.latitude}, ${inc.longitude}`;
      });
  } else {
    el.noMissionBox.classList.remove('hidden');
    el.activeMissionBox.classList.add('hidden');
  }
}

// Responder Stepper Actions
async function setMissionStatus(targetStatus) {
  const activeUnit = state.units.find(u => u.id === state.activeResponderUnitId);
  if (!activeUnit || !activeUnit.assigned_incident_id) {
    alert('No incident currently assigned to this unit.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/incidents/${activeUnit.assigned_incident_id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: targetStatus,
        actor_role: 'responder',
        actor_id: activeUnit.id,
        notes: `Responder updated status to ${targetStatus}`
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Status change rejected');
    }

    showToast(`Status updated to ${targetStatus}`, 'success');
    loadIncidents();
    loadUnits().then(() => updateResponderMissionView());
  } catch (err) {
    alert(`Could not advance status: ${err.message}`);
  }
}

el.btnMarkEnRoute.addEventListener('click', () => setMissionStatus('en_route'));
el.btnMarkArrived.addEventListener('click', () => setMissionStatus('arrived'));
el.btnMarkInProgress.addEventListener('click', () => setMissionStatus('assistance_in_progress'));
el.btnMarkResolved.addEventListener('click', () => setMissionStatus('resolved'));

// Simulated Telemetry Drive Step
el.btnSimulateDrive.addEventListener('click', async () => {
  const activeUnit = state.units.find(u => u.id === state.activeResponderUnitId);
  if (!activeUnit) return;

  let targetLat = 12.9716;
  let targetLon = 77.5946;

  if (activeUnit.assigned_incident_id) {
    const inc = state.incidents.find(i => i.id === activeUnit.assigned_incident_id);
    if (inc && inc.latitude && inc.longitude) {
      targetLat = inc.latitude;
      targetLon = inc.longitude;
    }
  }

  // Interpolate 25% toward destination
  const newLat = activeUnit.latitude + (targetLat - activeUnit.latitude) * 0.25;
  const newLon = activeUnit.longitude + (targetLon - activeUnit.longitude) * 0.25;

  try {
    const res = await fetch(`${API_BASE}/units/${activeUnit.id}/location`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: parseFloat(newLat.toFixed(5)),
        longitude: parseFloat(newLon.toFixed(5)),
        heading: 45.0,
        speed_kmh: 58.0,
        is_simulated: true
      })
    });

    if (res.ok) {
      const updated = await res.json();
      el.telemetryLat.textContent = updated.latitude.toFixed(4);
      el.telemetryLon.textContent = updated.longitude.toFixed(4);
      showToast(`GPS Telemetry Ping Sent for ${activeUnit.call_sign}`, 'info');
      loadUnits();
    }
  } catch (err) {
    console.error('Error updating location:', err);
  }
});

// Simulated Return to Base
el.btnSimulateHome.addEventListener('click', async () => {
  const activeUnit = state.units.find(u => u.id === state.activeResponderUnitId);
  if (!activeUnit) return;

  const defaultCoords = {
    'UNIT-AMB-101': { lat: 12.9716, lon: 77.5946 },
    'UNIT-AMB-102': { lat: 12.9850, lon: 77.6050 },
    'UNIT-FIRE-201': { lat: 12.9650, lon: 77.5850 },
    'UNIT-FIRE-202': { lat: 12.9900, lon: 77.5700 },
    'UNIT-POL-301': { lat: 12.9750, lon: 77.6100 },
    'UNIT-POL-302': { lat: 12.9550, lon: 77.5950 },
    'UNIT-RESC-401': { lat: 12.9600, lon: 77.6200 },
    'UNIT-UTIL-501': { lat: 12.9800, lon: 77.5600 }
  };

  const coords = defaultCoords[activeUnit.id] || { lat: 12.9716, lon: 77.5946 };

  try {
    const res = await fetch(`${API_BASE}/units/${activeUnit.id}/location`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: coords.lat,
        longitude: coords.lon,
        speed_kmh: 0.0,
        is_simulated: true
      })
    });

    if (res.ok) {
      showToast(`${activeUnit.call_sign} returned to Base`, 'info');
      loadUnits().then(() => updateResponderMissionView());
    }
  } catch (err) {
    console.error('Error returning home:', err);
  }
});

// -------------------------------------------------------------
// TACTICAL RADAR MAP RENDERING
// -------------------------------------------------------------
function geoToRadar(lat, lon) {
  // Center: (12.975, 77.595), Scale to SVG 600x400
  const centerLat = 12.975;
  const centerLon = 77.595;
  const scale = 4000; // pixels per degree

  const x = 300 + (lon - centerLon) * scale;
  const y = 200 - (lat - centerLat) * scale;
  return {
    x: Math.max(20, Math.min(580, x)),
    y: Math.max(20, Math.min(380, y))
  };
}

function renderTacticalRadar() {
  if (!el.radarIncidentsGroup || !el.radarUnitsGroup) return;

  // Render Incidents
  el.radarIncidentsGroup.innerHTML = state.incidents
    .filter(i => i.latitude && i.longitude && !['resolved', 'closed'].includes(i.status))
    .map(inc => {
      const pt = geoToRadar(inc.latitude, inc.longitude);
      const isCritical = inc.urgency === 'critical';
      return `
        <g class="radar-blip-incident" transform="translate(${pt.x}, ${pt.y})" 
           data-info="Incident [${inc.id.slice(0, 8)}]: ${escapeHtml(inc.category)} (${inc.urgency})">
          <circle r="${isCritical ? 10 : 7}" fill="rgba(239, 68, 68, 0.4)">
            <animate attributeName="r" values="${isCritical ? '8;18;8' : '6;14;6'}" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite" />
          </circle>
          <circle r="${isCritical ? 6 : 4}" fill="#ef4444" stroke="#ffffff" stroke-width="1.5" />
        </g>
      `;
    }).join('');

  // Render Units
  el.radarUnitsGroup.innerHTML = state.units.map(unit => {
    const pt = geoToRadar(unit.latitude, unit.longitude);
    return `
      <g class="radar-blip-unit" transform="translate(${pt.x}, ${pt.y})" 
         data-info="Unit: ${escapeHtml(unit.call_sign)} [${unit.status}]">
        <rect x="-6" y="-6" width="12" height="12" rx="2" fill="#06b6d4" stroke="#ffffff" stroke-width="1.5" />
        <text x="8" y="4" font-size="9" fill="#7dd3fc" font-family="JetBrains Mono">${escapeHtml(unit.id.split('-')[1])}</text>
      </g>
    `;
  }).join('');

  // Attach hover/touch tooltips
  const blips = document.querySelectorAll('.radar-blip-incident, .radar-blip-unit');
  blips.forEach(blip => {
    const handleTooltip = (e) => {
      el.radarTooltip.textContent = blip.dataset.info;
      el.radarTooltip.classList.remove('hidden');
      const containerRect = document.querySelector('.radar-canvas-container').getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const left = Math.min(containerRect.width - 150, Math.max(10, clientX - containerRect.left + 15));
      const top = Math.min(containerRect.height - 40, Math.max(10, clientY - containerRect.top + 10));
      el.radarTooltip.style.left = `${left}px`;
      el.radarTooltip.style.top = `${top}px`;
    };

    blip.addEventListener('mouseenter', handleTooltip);
    blip.addEventListener('mousemove', handleTooltip);
    blip.addEventListener('touchstart', handleTooltip, { passive: true });
    blip.addEventListener('mouseleave', () => el.radarTooltip.classList.add('hidden'));
  });
}

// -------------------------------------------------------------
// AUDIT STREAM & TOASTS
// -------------------------------------------------------------
function logAudit(entry) {
  state.auditLogs.unshift({
    timestamp: new Date().toISOString(),
    ...entry
  });

  if (state.auditLogs.length > 50) state.auditLogs.pop();

  el.auditStreamContainer.innerHTML = state.auditLogs.map(log => `
    <div class="audit-row">
      <div class="audit-row-header">
        <span>[${log.actor.toUpperCase()}] • ${log.type.replace(/_/g, ' ')}</span>
        <span>${formatTimestamp(log.timestamp)}</span>
      </div>
      <div class="audit-row-text">${escapeHtml(log.text)}</div>
    </div>
  `).join('');
}

el.btnClearAudit.addEventListener('click', () => {
  state.auditLogs = [];
  el.auditStreamContainer.innerHTML = '';
});

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  el.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// -------------------------------------------------------------
// UTILITIES
// -------------------------------------------------------------
function formatTimestamp(isoStr) {
  if (!isoStr) return '--';
  const d = new Date(isoStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatRelativeTime(isoStr) {
  if (!isoStr) return '';
  const diffSec = Math.floor((new Date() - new Date(isoStr)) / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  return `${Math.floor(diffSec / 3600)}h ago`;
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// -------------------------------------------------------------
// APPLICATION INITIALIZATION
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initWebSocket();
  loadIncidents();
  loadUnits();

  // Initial check for mobile viewports
  if (window.innerWidth <= 900) {
    showCitizenMobilePane('form');
  }
});
