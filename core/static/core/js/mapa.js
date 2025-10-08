// Arquivo: static/core/js/mapa.js (VERSÃO FINAL CORRIGIDA)

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

    // --- INICIALIZAÇÃO DO MAPA E DADOS DE FOCO ---
    const mapContainer = document.getElementById('map');
    const analisarAreaUrl = mapContainer.dataset.analisarUrl;
    const solicitacaoFocoId = JSON.parse(document.getElementById('solicitacao-foco-id').textContent);
    const areaFocoId = JSON.parse(document.getElementById('area-foco-id').textContent);

    const map = L.map('map', { zoomControl: false }).setView([-24.0965, -46.6212], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // --- INICIALIZAÇÃO DOS MODAIS ---
    const areaModalEl = document.getElementById('areaFormModal');
    const areaModal = new bootstrap.Modal(areaModalEl);
    const areaForm = document.getElementById('area-form');
    const saveAreaButton = document.getElementById('saveAreaButton');
    const deleteAreaButton = document.getElementById('deleteAreaButton');
    const modalTitle = document.getElementById('modalTitle');
    const addTreeModalEl = document.getElementById('addTreeModal');
    const addTreeModal = new bootstrap.Modal(addTreeModalEl);
    const addTreeForm = document.getElementById('add-tree-form');
    const submitNewTreeButton = document.getElementById('submitNewTree');
    const deleteConfirmModalEl = document.getElementById('deleteConfirmModal');
    const deleteConfirmModal = new bootstrap.Modal(deleteConfirmModalEl);
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    const treeIdPlaceholder = document.getElementById('tree-id-placeholder');

    areaModalEl.addEventListener('shown.bs.modal', function () {
        $('.select2-multiple').select2({
            placeholder: "Selecione as espécies",
            allowClear: true,
            dropdownParent: $('#areaFormModal')
        });
    });

    // --- LÓGICA DE CONTROLE DE CIDADES ---
    let mascaraCinza = null;
    let grupoCidades = null;
    let cidadesGlobais = [];
    const painelSeletor = document.getElementById('city-selector-panel');
    const containerDoMenu = document.getElementById('city-select-container');
    const statusMapa = document.getElementById('map-status');

    function garantirPaneMascara() {
        if (!map.getPane('mask')) {
            map.createPane('mask');
            map.getPane('mask').style.zIndex = 350;
        }
    }

    function aplicarMascaraECentralizar(cidades) {
        if (mascaraCinza) map.removeLayer(mascaraCinza);
        if (grupoCidades) grupoCidades.clearLayers(); // Limpa o grupo em vez de recriar
        
        mascaraCinza = null;
        if (!grupoCidades) {
            grupoCidades = L.featureGroup().addTo(map);
        }

        const worldRing = [[-90, -180], [-90, 180], [90, 180], [90, -180]];
        const holes = [];

        cidades.forEach(obj => {
            const feature = {
                "type": "Feature",
                "properties": { "name": obj.nome },
                "geometry": obj.geom
            };
            
            // CORREÇÃO PRINCIPAL: Usamos onEachFeature para adicionar a camada certa ao grupo
            L.geoJSON(feature, {
                style: { color: '#2a9d8f', weight: 2, fillOpacity: 0 },
                onEachFeature: function (feature, layer) {
                    // Adicionamos o "documento" (a camada de polígono) direto no "gaveteiro"
                    grupoCidades.addLayer(layer);

                    // Lógica da máscara continua a mesma
                    const geojson = layer.toGeoJSON();
                    const type = geojson.geometry.type;
                    const coords = geojson.geometry.coordinates;

                    if (type === 'Polygon') {
                        coords.forEach(ring => holes.push(ring.map(p => [p[1], p[0]])));
                    } else if (type === 'MultiPolygon') {
                        coords.forEach(polygon => polygon.forEach(ring => holes.push(ring.map(p => [p[1], p[0]]))));
                    }
                }
            });
        });

        garantirPaneMascara();
        mascaraCinza = L.polygon([worldRing, ...holes], {
            pane: 'mask', color: '#999', weight: 0, fillColor: '#999', fillOpacity: 0.65, interactive: false
        }).addTo(map);

        if (!solicitacaoFocoId && !areaFocoId) {
            const bounds = grupoCidades.getBounds();
            if (bounds.isValid()) {
                map.fitBounds(bounds.pad(0.15));
            }
        }
    }

    function focarCidadePeloNome(nomeCidade) {
        if (!grupoCidades) return;
        let alvo = null;
        
        // Agora essa busca funciona, pois a camada certa está no grupoCidades
        grupoCidades.eachLayer(layer => {
            const props = layer.feature.properties;
            if (props && props.name && props.name.toLowerCase() === nomeCidade.toLowerCase()) {
                alvo = layer;
            }
        });

        if (alvo) {
            const b = alvo.getBounds();
            if (b.isValid()) {
                map.fitBounds(b.pad(0.05));
            }
        }
    }

    async function iniciarControleDeCidades() {
        try {
            const resp = await fetch("/api/cidades-geo/", { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            const data = await resp.json();
            cidadesGlobais = data.cidades || [];

            painelSeletor.classList.remove('d-none');
            statusMapa.style.display = 'none';

            if (cidadesGlobais.length === 0) return;

            const select = document.createElement('select');
            select.className = 'form-select form-select-sm';
            select.id = 'city-select';
            cidadesGlobais.forEach(c => {
                const o = document.createElement('option');
                o.value = c.nome;
                o.textContent = c.nome;
                select.appendChild(o);
            });
            containerDoMenu.innerHTML = '';
            containerDoMenu.appendChild(select);

            aplicarMascaraECentralizar(cidadesGlobais);

            if (cidadesGlobais.length > 0 && !solicitacaoFocoId && !areaFocoId) {
                focarCidadePeloNome(cidadesGlobais[0].nome);
            }

            select.addEventListener('change', function () {
                focarCidadePeloNome(this.value);
            });

        } catch (e) {
            console.error("Erro ao carregar cidades:", e);
            painelSeletor.classList.remove('d-none');
            statusMapa.textContent = "Erro ao carregar cidades.";
        }
    }
    
    // O RESTANTE DO CÓDIGO PERMANECE IGUAL...
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
                const content = `<p class="mb-1 small"><strong>Científico:</strong> ${arvore.nome_cientifico || 'N/A'}</p><p class="mb-1 small"><strong>Saúde:</strong> ${arvore.saude || 'N/A'}</p><p class="mb-1 small"><strong>Plantio:</strong> ${arvore.plantio || 'N/A'}</p><div class="mt-2"><button class="btn btn-danger-outline btn-sm" onclick="deleteTree(${arvore.id})"><i class="bi bi-trash-fill me-1"></i> Apagar Árvore</button></div>`;
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
                const content = `<p class="mb-1 small"><strong>Tipo:</strong> ${area.tipo || 'N/A'}</p><p class="mb-1 small"><strong>Status:</strong> ${area.status || 'N/A'}</p><button class="btn btn-secondary-custom btn-sm mt-2" onclick="openEditModal(${area.id})">Editar Detalhes</button>`;
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
    map.addLayer(camadaArvores);
    map.addLayer(camadaSolicitacoes);
    map.addLayer(camadaAreas);

    // --- CONTROLE DE DESENHO ---
    L.drawLocal.draw.toolbar.actions.title = 'Cancelar desenho';
    L.drawLocal.draw.toolbar.actions.text = 'Cancelar';
    L.drawLocal.draw.toolbar.finish.title = 'Finalizar desenho';
    L.drawLocal.draw.toolbar.finish.text = 'Finalizar';
    L.drawLocal.draw.toolbar.undo.title = 'Apagar último ponto';
    L.drawLocal.draw.toolbar.undo.text = 'Desfazer';
    L.drawLocal.draw.toolbar.buttons.polygon = 'Desenhar uma área';
    L.drawLocal.draw.toolbar.buttons.rectangle = 'Desenhar um retângulo';
    L.drawLocal.draw.toolbar.buttons.marker = 'Marcar um ponto';
    L.drawLocal.draw.handlers.polygon.tooltip.start = 'Clique para começar a desenhar.';
    L.drawLocal.draw.handlers.polygon.tooltip.cont = 'Continue clicando para desenhar.';
    L.drawLocal.draw.handlers.polygon.tooltip.end = 'Clique no primeiro ponto para fechar.';

    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    const drawControl = new L.Control.Draw({ position: 'topleft', edit: { featureGroup: drawnItems }, draw: { polygon: true, polyline: false, rectangle: true, circle: false, circlemarker: false, marker: true } });
    map.addControl(drawControl);

    const drawControlContainer = drawControl.getContainer();
    map.on('draw:drawstart', () => drawControlContainer.classList.add('drawing-active'));
    map.on('draw:drawstop', () => drawControlContainer.classList.remove('drawing-active'));

    let temporaryLayer = null;
    let editingAreaId = null;

    map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        const layerType = event.layerType;

        if (layerType === 'marker') {
            const coords = layer.getLatLng();
            addTreeForm.reset();
            $('#tree-especie').val(null).trigger('change');
            document.getElementById('tree-lat').value = coords.lat;
            document.getElementById('tree-lon').value = coords.lng;
            addTreeModal.show();
            setTimeout(() => $('#tree-especie').select2({ placeholder: "Busque e selecione uma espécie", dropdownParent: $('#addTreeModal') }), 150);
            drawnItems.addLayer(layer);
            addTreeModalEl.addEventListener('hidden.bs.modal', () => drawnItems.removeLayer(layer), { once: true });
        } else {
            temporaryLayer = layer;
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
                    container.querySelector('#btn-descartar-desenho').addEventListener('click', () => drawnItems.removeLayer(temporaryLayer));
                    temporaryLayer.setPopupContent(container);
                } else {
                    temporaryLayer.setPopupContent(`Erro: ${data.message}`);
                }
            }).catch(error => {
                console.error("Erro no Fetch:", error);
                temporaryLayer.setPopupContent("Erro de comunicação.");
            });
        }
    });

    submitNewTreeButton.addEventListener('click', function() {
        const formData = new FormData(addTreeForm);
        fetch('/api/instancias/nova/', { method: 'POST', headers: { 'X-CSRFToken': csrftoken }, body: formData })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'ok') {
                addTreeModal.hide();
                showToast('Sucesso!', result.message || 'Árvore adicionada!');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showToast('Erro', result.message || 'Não foi possível salvar.', true);
            }
        }).catch(error => {
            console.error('Erro no fetch:', error);
            showToast('Erro de Rede', 'Falha na comunicação.', true);
        });
    });

    window.openEditModal = function(areaId) {
        editingAreaId = areaId;
        temporaryLayer = null;
        modalTitle.textContent = 'Editar Detalhes da Área';
        deleteAreaButton.classList.remove('d-none');
        fetch(`/api/areas/${areaId}/`).then(res => res.json()).then(data => {
            areaForm.elements['nome'].value = data.nome;
            areaForm.elements['tipo'].value = data.tipo;
            areaForm.elements['status'].value = data.status;
            $('#id_especies').val(data.especies).trigger('change');
            areaModal.show();
        });
    }

    saveAreaButton.addEventListener('click', function() {
        const formData = new FormData(areaForm);
        const formObject = {};
        formData.forEach((value, key) => formObject[key] = value);
        formObject['especies'] = formData.getAll('especies');

        let url, method, finalData;
        if (editingAreaId) {
            url = `/api/areas/${editingAreaId}/`;
            method = 'PUT';
            finalData = { form_data: formObject };
        } else {
            url = "/api/salvar_area/";
            method = 'POST';
            finalData = { form_data: formObject, geometry: temporaryLayer.toGeoJSON().geometry };
        }

        fetch(url, { method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }, body: JSON.stringify(finalData) })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                showToast('Sucesso!', data.message);
                areaModal.hide();
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showToast('Erro ao Salvar', data.message || 'Dados inválidos.', true);
            }
        });
    });

    deleteAreaButton.addEventListener('click', () => { if (editingAreaId) window.location.href = `/areas/${editingAreaId}/delete/`; });

    window.deleteTree = function(treeId) {
        treeIdPlaceholder.textContent = treeId;
        confirmDeleteBtn.dataset.treeId = treeId;
        deleteConfirmModal.show();
    }

    confirmDeleteBtn.addEventListener('click', function() {
        const treeId = this.dataset.treeId;
        if (treeId) {
            fetch(`/api/arvores/${treeId}/delete/`, { method: 'DELETE', headers: { 'X-CSRFToken': csrftoken } })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    showToast('Sucesso!', data.message);
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast('Erro!', data.message, true);
                }
            }).catch(error => {
                console.error('Erro:', error);
                showToast('Erro de Rede!', 'Falha na comunicação.', true);
            }).finally(() => deleteConfirmModal.hide());
        }
    });

    // --- FOCO E EXIBIDOR DE COORDENADAS ---
    const coordsDisplay = document.getElementById('coords-display');
    map.on('mousemove', e => { coordsDisplay.innerHTML = `Lat: ${e.latlng.lat.toFixed(5)} | Lon: ${e.latlng.lng.toFixed(5)}`; });
    map.on('mouseout', () => { coordsDisplay.innerHTML = 'Lat: -- | Lon: --'; });
    
    // --- INICIA A LÓGICA DE CIDADES E DEPOIS O FOCO ---
    iniciarControleDeCidades().then(() => {
        if (solicitacaoFocoId && solicitacaoMarkers[solicitacaoFocoId]) {
            const markerToFocus = solicitacaoMarkers[solicitacaoFocoId];
            map.flyTo(markerToFocus.getLatLng(), 18, { duration: 1 });
            setTimeout(() => markerToFocus.fire('click'), 1000);
        }
        if (areaFocoId && areaLayers[areaFocoId]) {
            const layerToFocus = areaLayers[areaFocoId];
            map.fitBounds(layerToFocus.getBounds());
            layerToFocus.fire('click');
        }
    });
});