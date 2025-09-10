// Arquivo: static/core/js/mapa.js (VERSÃO FINAL COM REDIRECIONAMENTO DE DELEÇÃO)

document.addEventListener('DOMContentLoaded', function() {

    // --- FUNÇÕES AUXILIARES ---
    function showToast(title, message, isError = false) {
        const toastContainer = document.querySelector('.toast-container');
        const toastEl = document.createElement('div');
        toastEl.classList.add('toast');
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto ${isError ? 'text-danger' : ''}">${title}</strong>
                <small>Agora</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', function () {
            toastEl.remove();
        });
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

    // --- INICIALIZAÇÃO DO MAPA ---
    const mapContainer = document.getElementById('map');
    const analisarAreaUrl = mapContainer.dataset.analisarUrl;

    const map = L.map('map').setView([-24.0965, -46.6212], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
    
    // --- INICIALIZAÇÃO DO MODAL ---
    const areaModalEl = document.getElementById('areaFormModal');
    const areaModal = new bootstrap.Modal(areaModalEl);
    const areaForm = document.getElementById('area-form');
    const saveAreaButton = document.getElementById('saveAreaButton');
    const deleteAreaButton = document.getElementById('deleteAreaButton');
    const modalTitle = document.getElementById('modalTitle');

    areaModalEl.addEventListener('shown.bs.modal', function () {
        $('.select2-multiple').select2({
            placeholder: "Selecione as espécies",
            allowClear: true,
            dropdownParent: $('#areaFormModal') 
        });
    });

    // --- ÍCONES, CAMADAS, DADOS, PAINÉIS ---
    const treeIcon = L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] });
    const alertIcon = L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] });
    const suggestionIcon = L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] });

    const camadaArvores = L.markerClusterGroup();
    const camadaSolicitacoes = L.layerGroup();
    const camadaAreas = L.layerGroup();
    const areaLayers = {};

    const arvoresData = JSON.parse(document.getElementById('arvores-data-json').textContent);
    const solicitacoesData = JSON.parse(document.getElementById('solicitacoes-data-json').textContent);
    const areasData = JSON.parse(document.getElementById('areas-data-json').textContent);
    const solicitacaoFocoId = JSON.parse(document.getElementById('solicitacao-foco-id').textContent);
    const areaFocoId = JSON.parse(document.getElementById('area-foco-id').textContent);

    const detailsPanel = document.getElementById('details-panel');
    const detailsTitle = document.getElementById('details-title');
    const detailsContent = document.getElementById('details-content');
    const closeDetailsBtn = document.getElementById('close-details-btn');
    closeDetailsBtn.addEventListener('click', () => detailsPanel.classList.add('d-none'));
    
    // --- PROCESSAMENTO DAS CAMADAS ---
    arvoresData.forEach(arvore => {
        if (arvore.lat && arvore.lon) {
            const marker = L.marker([arvore.lat, arvore.lon], { icon: treeIcon });
            marker.on('click', () => {
                const content = `<p class="mb-1 small"><strong>Científico:</strong> ${arvore.nome_cientifico || 'N/A'}</p><p class="mb-1 small"><strong>Saúde:</strong> ${arvore.saude || 'N/A'}</p><p class="mb-1 small"><strong>Plantio:</strong> ${arvore.plantio || 'N/A'}</p>`;
                detailsTitle.innerHTML = `<i class="bi bi-tree-fill text-success me-2"></i> ${arvore.nome}`;
                detailsContent.innerHTML = content;
                detailsPanel.classList.remove('d-none');
            });
            camadaArvores.addLayer(marker);
        }
    });

    const solicitacaoMarkers = {};
    solicitacoesData.forEach(solicitacao => {
        if (solicitacao.lat && solicitacao.lon) {
            const iconeEscolhido = (solicitacao.tipo_codigo === 'DENUNCIA') ? alertIcon : suggestionIcon;
            const marker = L.marker([solicitacao.lat, solicitacao.lon], { icon: iconeEscolhido });
            marker.on('click', () => {
                const content = `<p class="mb-1 small"><strong>Status:</strong> ${solicitacao.status || 'N/A'}</p><p class="mb-1 small">${solicitacao.descricao || 'N/A'}</p><a href="/solicitacoes/${solicitacao.id}/" class="btn btn-secondary-custom btn-sm mt-2">Ver Detalhes</a>`;
                detailsTitle.innerHTML = `<i class="bi bi-file-earmark-text-fill text-warning me-2"></i> ${solicitacao.tipo_display}`;
                detailsContent.innerHTML = content;
                detailsPanel.classList.remove('d-none');
            });
            camadaSolicitacoes.addLayer(marker);
            solicitacaoMarkers[solicitacao.id] = marker;
        }
    });

    areasData.forEach(area => {
        if (area.geom) {
            const areaLayer = L.geoJSON(area.geom, { style: { color: "#6f42c1", weight: 2 } });
            areaLayer.on('click', () => {
                const content = `
                    <p class="mb-1 small"><strong>Tipo:</strong> ${area.tipo || 'N/A'}</p>
                    <p class="mb-1 small"><strong>Status:</strong> ${area.status || 'N/A'}</p>
                    <button class="btn btn-secondary-custom btn-sm mt-2" onclick="openEditModal(${area.id})">Editar Detalhes</button>
                `;
                detailsTitle.innerHTML = `<i class="bi bi-bounding-box text-primary me-2"></i> ${area.nome}`;
                detailsContent.innerHTML = content;
                detailsPanel.classList.remove('d-none');
            });
            camadaAreas.addLayer(areaLayer);
            areaLayers[area.id] = areaLayer;
        }
    });
    
    // --- CONTROLE DE CAMADAS ---
    const heatPoints = arvoresData.map(arvore => [arvore.lat, arvore.lon, 1]);
    const camadaHeatmap = L.heatLayer(heatPoints, { radius: 25 });
    
    const baseLayers = {};
    const overlayLayers = {
        "<span class='layer-name'>Árvores</span>": camadaArvores,
        "<span class='layer-name'>Solicitações</span>": camadaSolicitacoes,
        "<span class='layer-name'>Áreas Planejadas</span>": camadaAreas,
        "<span class='layer-name'>Mapa de Calor</span>": camadaHeatmap
    };
    L.control.layers(baseLayers, overlayLayers, { collapsed: false, position: 'topright' }).addTo(map);
    map.addLayer(camadaArvores); map.addLayer(camadaSolicitacoes); map.addLayer(camadaAreas);

    // --- CONTROLE DE DESENHO ---
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    const drawControl = new L.Control.Draw({ edit: { featureGroup: drawnItems }, draw: { polygon: true, polyline: false, rectangle: true, circle: false, marker: true } });
    map.addControl(drawControl);
    
    let temporaryLayer = null;
    let editingAreaId = null;

    map.on(L.Draw.Event.CREATED, function (event) {
        temporaryLayer = event.layer;
        if (event.layerType === 'marker') {
            showToast('Em Breve', 'A lógica para adicionar uma nova árvore por aqui será implementada.', false);
            map.removeLayer(event.layer);
        } else {
            drawnItems.addLayer(temporaryLayer);
            temporaryLayer.bindPopup("Analisando área...").openPopup();
            const geometry = temporaryLayer.toGeoJSON().geometry;
            fetch(analisarAreaUrl, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }, body: JSON.stringify({ geometry: geometry }) })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    const container = document.createElement('div');
                    container.innerHTML = `<h6>Diagnóstico Rápido</h6><hr class="my-1"><p class="mb-1 small"><strong>Árvores na área:</strong> ${data.contagem_arvores}</p><p class="mb-1 small"><strong>Solicitações na área:</strong> ${data.contagem_solicitacoes}</p><div class="mt-2 text-center"><button class="btn btn-sm btn-success" id="btn-salvar-desenho">Salvar Área</button> <button class="btn btn-sm btn-danger" id="btn-descartar-desenho">Descartar</button></div>`;
                    container.querySelector('#btn-salvar-desenho').addEventListener('click', () => { 
                        editingAreaId = null; 
                        areaForm.reset(); 
                        $('#id_especies').val(null).trigger('change'); 
                        modalTitle.textContent = 'Detalhes da Nova Área'; 
                        deleteAreaButton.classList.add('d-none'); 
                        areaModal.show(); 
                    });
                    container.querySelector('#btn-descartar-desenho').addEventListener('click', () => { drawnItems.removeLayer(temporaryLayer); });
                    temporaryLayer.setPopupContent(container);
                } else { temporaryLayer.setPopupContent(`Erro: ${data.message}`); }
            }).catch(error => { console.error("Erro no Fetch:", error); temporaryLayer.setPopupContent("Erro de comunicação."); });
        }
    });

    // FUNÇÃO PARA ABRIR O MODAL DE EDIÇÃO
    window.openEditModal = function(areaId) {
        editingAreaId = areaId;
        temporaryLayer = null;
        modalTitle.textContent = 'Editar Detalhes da Área';
        deleteAreaButton.classList.remove('d-none');
        
        fetch(`/api/areas/${areaId}/`)
        .then(response => response.json())
        .then(data => {
            areaForm.elements['nome'].value = data.nome;
            areaForm.elements['tipo'].value = data.tipo;
            areaForm.elements['status'].value = data.status;
            $('#id_especies').val(data.especies).trigger('change');
            areaModal.show();
        });
    }

    // LÓGICA PARA SALVAR O FORMULÁRIO DO MODAL
    saveAreaButton.addEventListener('click', function() {
        const formData = new FormData(areaForm);
        const formObject = {};
        for (const [key, value] of formData.entries()) {
          formObject[key] = value;
        }
        formObject['especies'] = formData.getAll('especies');

        let url, method, finalData;
        
        if (editingAreaId) {
            url = `/api/areas/${editingAreaId}/`;
            method = 'PUT';
            finalData = { form_data: formObject };
        } else {
            url = "/api/salvar_area/";
            method = 'POST';
            const geometryData = temporaryLayer.toGeoJSON();
            finalData = { form_data: formObject, geometry: geometryData.geometry };
        }

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
            body: JSON.stringify(finalData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                showToast('Sucesso!', data.message);
                areaModal.hide();
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showToast('Erro ao Salvar', (data.message || 'Dados do formulário inválidos.'), true);
            }
        });
    });

    // --- LÓGICA DO BOTÃO DELETAR (ATUALIZADA PARA REDIRECIONAR) ---
    // Agora, em vez de fazer a deleção via API, ele simplesmente
    // manda o usuário para a nova página de confirmação que a gente criou.
    deleteAreaButton.addEventListener('click', function() {
        if (editingAreaId) {
            window.location.href = `/areas/${editingAreaId}/delete/`;
        }
    });

    // --- FOCO E EXIBIDOR DE COORDENADAS ---
    if (solicitacaoFocoId && solicitacaoMarkers[solicitacaoFocoId]) {
        const markerToFocus = solicitacaoMarkers[solicitacaoFocoId];
        const latLng = markerToFocus.getLatLng();
        map.flyTo(latLng, 18);
        markerToFocus.fire('click');
    }
    if (areaFocoId && areaLayers[areaFocoId]) {
        const layerToFocus = areaLayers[areaFocoId];
        map.fitBounds(layerToFocus.getBounds());
        layerToFocus.fire('click');
    }
    
    const coordsDisplay = document.getElementById('coords-display');
    map.on('mousemove', e => { coordsDisplay.innerHTML = `Lat: ${e.latlng.lat.toFixed(5)} | Lon: ${e.latlng.lng.toFixed(5)}`; });
    map.on('mouseout', () => { coordsDisplay.innerHTML = 'Lat: -- | Lon: --'; });
});