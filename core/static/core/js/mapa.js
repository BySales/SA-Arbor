// Arquivo: static/core/js/mapa.js (VERSÃO FINAL COMPLETA V4.2)

document.addEventListener('DOMContentLoaded', function() {

    // ======================================================
    // 1. FUNÇÕES AUXILIARES (Toast, Cookie, JSON)
    // ======================================================
    function showToast(title, message, isError = false) {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return;
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${isError ? 'danger' : 'success'} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong>: ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    const getJsonData = (id) => {
        const element = document.getElementById(id);
        try { return element ? JSON.parse(element.textContent) : null; } 
        catch (e) { console.error(`Erro JSON #${id}:`, e); return null; }
    };

    // ======================================================
    // 2. INICIALIZAÇÃO DO MAPA E VARIÁVEIS GLOBAIS
    // ======================================================
    const mapContainer = document.getElementById('map');
    if (!mapContainer) return;

    const analisarAreaUrl = mapContainer.dataset.analisarUrl;
    const solicitacaoFocoId_antigo = getJsonData('solicitacao-foco-id');
    const focoSolicitacao = getJsonData('foco-solicitacao-data');
    const areaFocoId = getJsonData('area-foco-id');

    const map = L.map('map', { zoomControl: false }).setView([-24.0965, -46.6212], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    const gpsControl = L.Control.extend({
        options: { position: 'bottomright' },
        onAdd: function(map) {
            const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            container.innerHTML = '<a href="#" title="Minha Localização" role="button" style="width: 30px; height: 30px; line-height: 30px; text-align: center; font-size: 18px; background: white; color: #333;"><i class="bi bi-crosshair"></i></a>';
            container.onclick = function(e) {
                e.preventDefault();
                if (navigator.geolocation) map.locate({setView: true, maxZoom: 16});
                else alert("Geolocalização não suportada.");
                return false;
            }
            return container;
        }
    });
    map.addControl(new gpsControl());
    map.on('locationfound', e => { if (marker) marker.setLatLng(e.latlng); else marker = L.marker(e.latlng).addTo(map); });

    // ======================================================
    // 3. REFERÊNCIAS AOS MODAIS E ELEMENTOS DA UI
    // ======================================================
    const areaModalEl = document.getElementById('areaFormModal');
    const areaModal = areaModalEl ? new bootstrap.Modal(areaModalEl) : null;
    const modalTitle = document.getElementById('modalTitle');
    const deleteAreaButton = document.getElementById('deleteAreaButton');
    
    const addTreeModalEl = document.getElementById('addTreeModal');
    const addTreeModal = addTreeModalEl ? new bootstrap.Modal(addTreeModalEl) : null;
    
    const deleteConfirmModalEl = document.getElementById('deleteConfirmModal');
    const deleteConfirmModal = deleteConfirmModalEl ? new bootstrap.Modal(deleteConfirmModalEl) : null;
    
    const deleteAreaConfirmModalEl = document.getElementById('deleteAreaConfirmModal');
    const deleteAreaConfirmModal = deleteAreaConfirmModalEl ? new bootstrap.Modal(deleteAreaConfirmModalEl) : null;
    const confirmDeleteAreaBtn = document.getElementById('confirm-delete-area-btn');

    const detailsPanel = document.getElementById('details-panel');
    const detailsTitle = document.getElementById('details-title');
    const detailsContent = document.getElementById('details-content');
    document.getElementById('close-details-btn')?.addEventListener('click', () => detailsPanel.classList.remove('show'));
    
    // Fecha painel ao clicar no mapa vazio
    map.on('click', () => detailsPanel.classList.remove('show'));

    const coordsDisplay = document.getElementById('coords-display');
    if (coordsDisplay) {
        map.on('mousemove', e => { coordsDisplay.innerHTML = `<i class="bi bi-crosshair me-1"></i> Lat: ${e.latlng.lat.toFixed(4)} | Lon: ${e.latlng.lng.toFixed(4)}`; });
        map.on('mouseout', () => { coordsDisplay.innerHTML = '<i class="bi bi-crosshair me-1"></i> Lat: -- | Lon: --'; });
    }

    if (areaModalEl) {
        areaModalEl.addEventListener('shown.bs.modal', function () {
            if (window.jQuery && window.jQuery.fn.select2) {
                window.jQuery('#id_especies').select2({ placeholder: "Selecione as espécies", allowClear: true, width: '100%', dropdownParent: window.jQuery('#areaFormModal') });
            }
        });
    }

    // ======================================================
    // 4. ÍCONES E CAMADAS
    // ======================================================
    const createCustomIcon = (className, htmlContent) => L.divIcon({ className: `custom-marker-icon ${className}`, html: htmlContent, iconSize: [24, 24], iconAnchor: [12, 24], popupAnchor: [0, -24] });
    const treeIcon = createCustomIcon('marker-arvore', '<i class="bi bi-tree-fill"></i>');
    const alertIcon = createCustomIcon('marker-denuncia', '<i class="bi bi-exclamation-triangle-fill"></i>');
    const suggestionIcon = createCustomIcon('marker-sugestao', '<i class="bi bi-lightbulb-fill"></i>');
    const ghostIcon = createCustomIcon('marker-fantasma', '<i class="bi bi-pin-fill"></i>');

    const camadaArvores = L.markerClusterGroup();
    const camadaSolicitacoes = L.layerGroup();
    const camadaAreas = L.layerGroup();
    let camadaHeatmap = null;

    const arvoresData = getJsonData('arvores-data-json') || [];
    const solicitacoesData = getJsonData('solicitacoes-data-json') || [];
    const areasData = getJsonData('areas-data-json') || [];

    arvoresData.forEach(arvore => {
        if (arvore.lat && arvore.lon) {
            const marker = L.marker([arvore.lat, arvore.lon], { icon: treeIcon, treeId: arvore.id });
            marker.on('click', () => {
                L.DomEvent.stop(event);
                detailsTitle.innerHTML = `<i class="bi bi-tree-fill text-success me-2"></i> ${arvore.nome}`;
                detailsContent.innerHTML = `<p class="mb-1 small"><strong>Científico:</strong> ${arvore.nome_cientifico || '-'}</p><p class="mb-1 small"><strong>Saúde:</strong> ${arvore.saude || '-'}</p><p class="mb-1 small"><strong>Plantio:</strong> ${arvore.plantio || '-'}</p><div class="mt-3 pt-3 border-top d-flex justify-content-end"><button class="btn btn-danger-outline btn-sm px-3" onclick="deleteTree(${arvore.id})"><i class="bi bi-trash-fill me-1"></i> Apagar</button></div>`;
                detailsPanel.classList.add('show');
            });
            camadaArvores.addLayer(marker);
        }
    });

    solicitacoesData.forEach(sol => {
        if (sol.lat && sol.lon) {
            const icon = (sol.tipo_codigo === 'DENUNCIA') ? alertIcon : suggestionIcon;
            const marker = L.marker([sol.lat, sol.lon], { icon: icon });
            marker.on('click', (event) => {
                L.DomEvent.stop(event);
                detailsTitle.innerHTML = `<i class="bi bi-file-earmark-text-fill text-warning me-2"></i> Solicitação #${sol.id}`;
                detailsContent.innerHTML = `<span class="badge bg-secondary mb-2">${sol.status}</span><p class="small">${sol.descricao || '-'}</p><a href="/solicitacoes/${sol.id}/" class="btn btn-secondary-custom btn-sm w-100 mt-2">Ver Detalhes</a>`;
                detailsPanel.classList.add('show');
            });
            camadaSolicitacoes.addLayer(marker);
        }
    });

    areasData.forEach(area => {
        if (area.geom) {
            try {
                const layer = L.geoJSON(area.geom, { style: { color: "#6f42c1", weight: 2, fillOpacity: 0.2 } });
                layer.on('click', (e) => {
                    L.DomEvent.stop(e);
                    detailsTitle.innerHTML = `<i class="bi bi-bounding-box text-primary me-2"></i> ${area.nome}`;
                    detailsContent.innerHTML = `<p class="mb-1 small"><strong>Tipo:</strong> ${area.tipo || '-'}</p><p class="mb-1 small"><strong>Status:</strong> ${area.status || '-'}</p><button class="btn btn-secondary-custom btn-sm w-100 mt-3" onclick="openEditModal(${area.id})">Editar Área</button>`;
                    detailsPanel.classList.add('show');
                });
                camadaAreas.addLayer(layer);
            } catch (e) { console.error(e); }
        }
    });

    if (arvoresData.length > 0 && L.heatLayer) {
        camadaHeatmap = L.heatLayer(arvoresData.map(a => [a.lat, a.lon, 0.8]), { radius: 30, blur: 20 });
    }

    map.addLayer(camadaArvores);
    map.addLayer(camadaSolicitacoes);
    map.addLayer(camadaAreas);

    // ======================================================
    // 5. CONTROLES EXTERNOS
    // ======================================================
    document.querySelectorAll('.layer-option input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', function() {
            const layer = { 'arvores': camadaArvores, 'solicitacoes': camadaSolicitacoes, 'areas': camadaAreas, 'calor': camadaHeatmap }[this.dataset.layer];
            if (layer) this.checked ? map.addLayer(layer) : map.removeLayer(layer);
        });
    });

    const canvasRenderer = L.canvas({ padding: 1 });
    let mascaraCinza = null, cidadesGlobais = [];
    const citySelect = document.getElementById('city-select');

    async function iniciarCidades() {
        if (!citySelect) return;
        try {
            const res = await fetch("/api/cidades-geo/", { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (!res.ok) throw new Error();
            cidadesGlobais = (await res.json()).cidades || [];
            citySelect.innerHTML = cidadesGlobais.length ? '' : '<option disabled selected>Nenhuma cidade</option>';
            cidadesGlobais.forEach(c => citySelect.add(new Option(c.nome, c.nome)));
            desenharMascara(cidadesGlobais);
            if (!focoSolicitacao && !areaFocoId && cidadesGlobais.length) focarCidade(cidadesGlobais[0].nome);
            citySelect.addEventListener('change', function() { focarCidade(this.value); });
        } catch (e) { citySelect.innerHTML = '<option disabled selected>Erro ao carregar</option>'; }
    }

    function desenharMascara(cidades) {
        if (mascaraCinza) map.removeLayer(mascaraCinza);
        const holes = [];
        cidades.forEach(c => L.geoJSON(c.geom, { onEachFeature: (f, l) => {
            const coords = l.toGeoJSON().geometry.coordinates;
            if (l.toGeoJSON().geometry.type === 'Polygon') holes.push(coords[0].map(p => [p[1], p[0]]));
            else if (l.toGeoJSON().geometry.type === 'MultiPolygon') coords.forEach(poly => holes.push(poly[0].map(p => [p[1], p[0]])));
        }}));
        if (!map.getPane('mask')) { map.createPane('mask'); map.getPane('mask').style.zIndex = 350; }
        mascaraCinza = L.polygon([ [[-90, -180], [-90, 180], [90, 180], [90, -180]], ...holes], { pane: 'mask', color: '#000', weight: 1, fillColor: '#0a0a0aa2', fillOpacity: 0.85, interactive: false, renderer: canvasRenderer }).addTo(map);
    }

    function focarCidade(nome) {
        const c = cidadesGlobais.find(x => x.nome === nome);
        if (c) map.fitBounds(L.geoJSON(c.geom).getBounds(), { padding: [50, 50], duration: 1 });
    }

    // ======================================================
    // 6. FERRAMENTAS DE DESENHO
    // ======================================================
    const drawnItems = new L.FeatureGroup().addTo(map);
    L.drawLocal.draw.toolbar.buttons.polygon = 'Desenhar área';
    L.drawLocal.draw.toolbar.buttons.marker = 'Nova árvore';
    L.drawLocal.draw.toolbar.buttons.rectangle = 'Desenhar retângulo';
    const drawControl = new L.Control.Draw({
        position: 'topleft',
        edit: false, // <--- 🔥 DESLIGA A BARRA DE EDIÇÃO/EXCLUSÃO 🔥
        draw: {
            polygon: { allowIntersection: false, showArea: true },
            rectangle: { shapeOptions: { clickable: false } },
            marker: { icon: treeIcon },
            circle: false, polyline: false, circlemarker: false
        }
    });
    map.addControl(drawControl);

    let temporaryLayer = null, editingAreaId = null;

    map.on(L.Draw.Event.CREATED, function(e) {
        const layer = e.layer;
        drawnItems.addLayer(layer);
        if (e.layerType === 'marker') {
            const c = layer.getLatLng();
            document.getElementById('tree-lat').value = c.lat.toFixed(6);
            document.getElementById('tree-lon').value = c.lng.toFixed(6);
            const form = document.getElementById('add-tree-form'); if (form) form.reset();
            if (typeof $ !== 'undefined' && $.fn.select2) $('#tree-especie').val(null).trigger('change');
            new bootstrap.Modal(document.getElementById('addTreeModal')).show();
            document.getElementById('addTreeModal').addEventListener('hidden.bs.modal', () => { if (drawnItems.hasLayer(layer)) drawnItems.removeLayer(layer); }, { once: true });
        } else {
            temporaryLayer = layer;
            const popup = document.createElement('div');
            popup.innerHTML = `<div class="text-center p-2"><h6 class="mb-2">Área Desenhada</h6><div class="d-flex gap-2 justify-content-center"><button id="btn-save-draw" class="btn btn-sm btn-success px-3">Salvar</button><button id="btn-cancel-draw" class="btn btn-sm btn-outline-danger px-3">Cancelar</button></div></div>`;
            popup.querySelector('#btn-save-draw').onclick = () => {
                editingAreaId = null; document.getElementById('area-form').reset();
                document.getElementById('modalTitle').textContent = 'Nova Área';
                document.getElementById('deleteAreaButton').classList.add('d-none');
                if (typeof $ !== 'undefined' && $.fn.select2) $('#id_especies').val(null).trigger('change');
                new bootstrap.Modal(document.getElementById('areaFormModal')).show(); map.closePopup();
            };
            popup.querySelector('#btn-cancel-draw').onclick = () => { drawnItems.removeLayer(layer); map.closePopup(); };
            layer.bindPopup(popup).openPopup();
        }
    });

    // ======================================================
    // 7. INICIALIZAÇÃO E GLOBAIS
    // ======================================================
    iniciarCidades().then(() => {
        if (focoSolicitacao) {
            const ghostMarker = L.marker([focoSolicitacao.lat, focoSolicitacao.lon], { icon: ghostIcon, zIndexOffset: 1000 }).addTo(map)
                .bindPopup(`<b>${focoSolicitacao.tipo_display}</b><br>${focoSolicitacao.status}`).openPopup();
            map.setView([focoSolicitacao.lat, focoSolicitacao.lon], 18);
        }
    });

    window.deleteTree = function(id) {
        document.getElementById('tree-id-placeholder').textContent = id;
        document.getElementById('confirm-delete-btn').dataset.treeId = id;
        new bootstrap.Modal(document.getElementById('deleteConfirmModal')).show();
    }

    window.openEditModal = function(id) {
        editingAreaId = id; temporaryLayer = null;
        document.getElementById('modalTitle').textContent = 'Editar Área';
        document.getElementById('deleteAreaButton').classList.remove('d-none');
        fetch(`/api/areas/${id}/`).then(r => r.json()).then(d => {
            const f = document.getElementById('area-form');
            f.elements['nome'].value = d.nome; f.elements['tipo'].value = d.tipo; f.elements['status'].value = d.status;
            if (typeof $ !== 'undefined' && $.fn.select2) $('#id_especies').val(d.especies).trigger('change');
            new bootstrap.Modal(document.getElementById('areaFormModal')).show();
        }).catch(() => showToast('Erro', 'Falha ao carregar área.', true));
    }

    // --- LISTENERS GLOBAIS (BOTÕES DE MODAL) ---
    document.getElementById('submitNewTree')?.addEventListener('click', function() {
        const fd = new FormData(document.getElementById('add-tree-form'));
        if (!fd.get('especie')) return showToast('Erro', 'Selecione uma espécie.', true);
        fetch('/api/instancias/nova/', { method: 'POST', headers: {'X-CSRFToken': csrftoken}, body: fd }).then(r=>r.json()).then(d=>{
            if(d.status==='ok') { bootstrap.Modal.getInstance(document.getElementById('addTreeModal')).hide(); showToast('Sucesso', d.message); window.location.reload(); }
            else showToast('Erro', d.message||'Falha.', true);
        });
    });

    document.getElementById('confirm-delete-btn')?.addEventListener('click', function() {
        fetch(`/api/arvores/${this.dataset.treeId}/delete/`, { method: 'DELETE', headers: {'X-CSRFToken': csrftoken} }).then(r=>r.json()).then(d=>{
            if(d.status==='ok') { showToast('Sucesso', d.message); window.location.reload(); } else showToast('Erro', d.message, true);
        });
    });

    document.getElementById('saveAreaButton')?.addEventListener('click', function() {
        const fd = new FormData(document.getElementById('area-form')), obj = {}; fd.forEach((v,k)=>obj[k]=v);
        if(typeof $ !== 'undefined') obj['especies'] = $('#id_especies').val()||[];
        const url = editingAreaId ? `/api/areas/${editingAreaId}/` : "/api/salvar_area/", method = editingAreaId ? 'PUT' : 'POST';
        const body = { form_data: obj }; if(!editingAreaId && temporaryLayer) body.geometry = temporaryLayer.toGeoJSON().geometry;
        fetch(url, { method: method, headers: {'Content-Type':'application/json', 'X-CSRFToken':csrftoken}, body: JSON.stringify(body) }).then(r=>r.json()).then(d=>{
             if(d.status==='ok') { showToast('Sucesso', d.message); window.location.reload(); } else showToast('Erro', d.message||'Falha.', true);
        });
    });

    // 🔥 NOVO LISTENER DE DELETAR ÁREA (SEM ALERT) 🔥
    if (confirmDeleteAreaBtn) {
        confirmDeleteAreaBtn.addEventListener('click', function() {
            if (editingAreaId) {
                 fetch(`/api/areas/${editingAreaId}/`, { method: 'DELETE', headers: { 'X-CSRFToken': csrftoken } })
                 .then(r => r.json())
                 .then(data => {
                     if (data.status === 'ok') {
                         showToast('Sucesso', 'Área removida.');
                         if (deleteAreaConfirmModal) deleteAreaConfirmModal.hide();
                         if (areaModal) areaModal.hide();
                         window.location.reload();
                     } else {
                         showToast('Erro', 'Falha ao remover.', true);
                     }
                 })
                 .catch(() => showToast('Erro', 'Erro de conexão.', true));
            }
        });
    }

    // Botão "Excluir" no modal de edição -> abre o de confirmação
    if (deleteAreaButton) {
        deleteAreaButton.addEventListener('click', function() {
             if (deleteAreaConfirmModal) {
                 // Opcional: esconder o modal de edição pra focar na confirmação
                 // if (areaModal) areaModal.hide(); 
                 deleteAreaConfirmModal.show();
             }
        });
    }

});