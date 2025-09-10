// Arquivo: static/core/js/mapa.js

document.addEventListener('DOMContentLoaded', function() {

    // --- FUNÇÕES AUXILIARES ---
    function showToast(title, message, isError = false) {
        // Implemente sua lógica de Toast aqui se necessário, ou remova se não for usada nesta página.
        console.log(`Toast (${isError ? 'Error' : 'Success'}): ${title} - ${message}`);
        alert(`${title}: ${message}`);
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
    const map = L.map('map').setView([-24.0965, -46.6212], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);

    // --- ÍCONES CUSTOMIZADOS ---
    const treeIcon = L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] });
    const alertIcon = L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] });
    const suggestionIcon = L.icon({ iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png', shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png', iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] });

    // --- CAMADAS (LAYERS) ---
    const camadaArvores = L.markerClusterGroup();
    const camadaSolicitacoes = L.layerGroup();
    const camadaAreas = L.layerGroup();
    const areaLayers = {}; // Dicionário para guardar as layers de área por ID

    // --- DADOS VINDOS DO DJANGO ---
    const arvoresData = JSON.parse(document.getElementById('arvores-data-json').textContent);
    const solicitacoesData = JSON.parse(document.getElementById('solicitacoes-data-json').textContent);
    const areasData = JSON.parse(document.getElementById('areas-data-json').textContent);
    const solicitacaoFocoId = JSON.parse(document.getElementById('solicitacao-foco-id').textContent);
    const areaFocoId = JSON.parse(document.getElementById('area-foco-id').textContent);

    // --- PAINÉIS DA INTERFACE ---
    const detailsPanel = document.getElementById('details-panel');
    const detailsTitle = document.getElementById('details-title');
    const detailsContent = document.getElementById('details-content');
    const closeDetailsBtn = document.getElementById('close-details-btn');
    closeDetailsBtn.addEventListener('click', () => detailsPanel.classList.add('d-none'));

    // --- PROCESSAMENTO DAS CAMADAS ---
    // Camada de Árvores
    arvoresData.forEach(arvore => {
        if (arvore.lat && arvore.lon) {
            const marker = L.marker([arvore.lat, arvore.lon], { icon: treeIcon });
            marker.on('click', () => {
                const content = `
                    <p class="mb-1 small"><strong>Científico:</strong> ${arvore.nome_cientifico || 'N/A'}</p>
                    <p class="mb-1 small"><strong>Saúde:</strong> ${arvore.saude || 'N/A'}</p>
                    <p class="mb-1 small"><strong>Plantio:</strong> ${arvore.plantio || 'N/A'}</p>
                `;
                detailsTitle.innerHTML = `<i class="bi bi-tree-fill text-success me-2"></i> ${arvore.nome}`;
                detailsContent.innerHTML = content;
                detailsPanel.classList.remove('d-none');
            });
            camadaArvores.addLayer(marker);
        }
    });

    // Camada de Solicitações
    const solicitacaoMarkers = {};
    solicitacoesData.forEach(solicitacao => {
        if (solicitacao.lat && solicitacao.lon) {
            const iconeEscolhido = (solicitacao.tipo_codigo === 'DENUNCIA') ? alertIcon : suggestionIcon;
            const marker = L.marker([solicitacao.lat, solicitacao.lon], { icon: iconeEscolhido });
            marker.on('click', () => {
                const content = `
                    <p class="mb-1 small"><strong>Status:</strong> ${solicitacao.status || 'N/A'}</p>
                    <p class="mb-1 small">${solicitacao.descricao || 'N/A'}</p>
                    <a href="/solicitacoes/${solicitacao.id}/" class="btn btn-secondary-custom btn-sm mt-2">Ver Detalhes</a>
                `;
                detailsTitle.innerHTML = `<i class="bi bi-file-earmark-text-fill text-warning me-2"></i> ${solicitacao.tipo_display}`;
                detailsContent.innerHTML = content;
                detailsPanel.classList.remove('d-none');
            });
            camadaSolicitacoes.addLayer(marker);
            solicitacaoMarkers[solicitacao.id] = marker;
        }
    });

    // Camada de Áreas
    areasData.forEach(area => {
        if (area.geom) {
            const areaLayer = L.geoJSON(area.geom, {
                style: { color: "#6f42c1", weight: 2 }
            });
            areaLayer.on('click', () => {
                const content = `
                    <p class="mb-1 small"><strong>Tipo:</strong> ${area.tipo || 'N/A'}</p>
                    <p class="mb-1 small"><strong>Status:</strong> ${area.status || 'N/A'}</p>
                    <button class="btn btn-secondary-custom btn-sm mt-2" onclick="alert('Funcionalidade de edição de área a ser implementada')">Editar Detalhes</button>
                `;
                detailsTitle.innerHTML = `<i class="bi bi-bounding-box text-primary me-2"></i> ${area.nome}`;
                detailsContent.innerHTML = content;
                detailsPanel.classList.remove('d-none');
            });
            camadaAreas.addLayer(areaLayer);
            areaLayers[area.id] = areaLayer;
        }
    });

    // Camada de Mapa de Calor (Heatmap)
    const heatPoints = arvoresData.map(arvore => [arvore.lat, arvore.lon, 1]);
    const camadaHeatmap = L.heatLayer(heatPoints, { radius: 25 });

    // --- CONTROLE DE CAMADAS (INTERFACE) ---
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

    // --- CONTROLE DE DESENHO (LEAFLET.DRAW) ---
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    const drawControl = new L.Control.Draw({
        edit: { featureGroup: drawnItems },
        draw: {
            polygon: true,
            polyline: false,
            rectangle: true,
            circle: false,
            marker: true
        }
    });
    map.addControl(drawControl);
    
    map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        drawnItems.addLayer(layer);
        alert('Forma desenhada! A lógica para salvar será implementada aqui.');
        // Aqui entraria a lógica de abrir modal, analisar área, etc.
    });


    // --- FOCO EM ITEM ESPECÍFICO (vindo da URL) ---
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

    // --- EXIBIDOR DE COORDENADAS ---
    const coordsDisplay = document.getElementById('coords-display');
    map.on('mousemove', e => {
        coordsDisplay.innerHTML = `Lat: ${e.latlng.lat.toFixed(5)} | Lon: ${e.latlng.lng.toFixed(5)}`;
    });
    map.on('mouseout', () => { coordsDisplay.innerHTML = 'Lat: -- | Lon: --'; });
});