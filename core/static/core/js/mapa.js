// Arquivo: static/core/js/mapa.js (VERSÃO FINAL COM ÍCONES COLORIDOS VIA CSS)

document.addEventListener('DOMContentLoaded', function() {

    // --- FUNÇÕES AUXILIARES ---
    function showToast(title, message, isError = false) {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return; // Garante que o container existe
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
    const analisarAreaUrl = mapContainer ? mapContainer.dataset.analisarUrl : null;

    const getJsonData = (id) => {
        const element = document.getElementById(id);
        try {
            return element ? JSON.parse(element.textContent) : null;
        } catch (e) {
            console.error(`Erro ao parsear JSON do elemento #${id}:`, e);
            return null;
        }
    };

    const solicitacaoFocoId_antigo = getJsonData('solicitacao-foco-id');
    const focoSolicitacao = getJsonData('foco-solicitacao-data');
    const areaFocoId = getJsonData('area-foco-id');

    if (!mapContainer) {
        console.error("Elemento #map não encontrado. Mapa não inicializado.");
        return;
    }

    const map = L.map('map', { zoomControl: false }).setView([-24.0965, -46.6212], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // --- INICIALIZAÇÃO DOS MODAIS (com checagens) ---
    const areaModalEl = document.getElementById('areaFormModal');
    const areaModal = areaModalEl ? new bootstrap.Modal(areaModalEl) : null;
    const areaForm = document.getElementById('area-form');
    const saveAreaButton = document.getElementById('saveAreaButton');
    const deleteAreaButton = document.getElementById('deleteAreaButton');
    const modalTitle = document.getElementById('modalTitle');
    const addTreeModalEl = document.getElementById('addTreeModal');
    const addTreeModal = addTreeModalEl ? new bootstrap.Modal(addTreeModalEl) : null;
    const addTreeForm = document.getElementById('add-tree-form');
    const submitNewTreeButton = document.getElementById('submitNewTree');
    const deleteConfirmModalEl = document.getElementById('deleteConfirmModal');
    const deleteConfirmModal = deleteConfirmModalEl ? new bootstrap.Modal(deleteConfirmModalEl) : null;
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    const treeIdPlaceholder = document.getElementById('tree-id-placeholder');

    if (areaModalEl) {
        areaModalEl.addEventListener('shown.bs.modal', function () {
            if (typeof $ !== 'undefined' && $.fn.select2) {
                $('.select2-multiple').select2({
                    placeholder: "Selecione as espécies",
                    allowClear: true,
                    dropdownParent: $('#areaFormModal')
                });
            } else {
                 console.warn("jQuery ou Select2 não carregado. Select de espécies pode não funcionar.");
            }
        });
    }

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
        if (grupoCidades) grupoCidades.clearLayers();
        
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
            
            L.geoJSON(feature, {
                style: { color: '#2a9d8f', weight: 2, fillOpacity: 0 },
                onEachFeature: function (feature, layer) {
                    grupoCidades.addLayer(layer);
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

        if (!focoSolicitacao && !areaFocoId) {
            const bounds = grupoCidades.getBounds();
            if (bounds.isValid()) {
                map.fitBounds(bounds.pad(0.15));
            }
        }
    }

    function focarCidadePeloNome(nomeCidade) {
        if (!grupoCidades) return;
        let alvo = null;
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
        if (!painelSeletor || !containerDoMenu || !statusMapa) {
            console.warn("Elementos do painel de cidade não encontrados.");
            return;
        }
        try {
            const resp = await fetch("/api/cidades-geo/", { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (!resp.ok) throw new Error(`Erro na API: ${resp.statusText}`);
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

            if (cidadesGlobais.length > 0 && !focoSolicitacao && !areaFocoId) {
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
    
    // --- ÍCONES CUSTOMIZADOS VIA L.divIcon E CLASSES CSS --- <<<<<<<<<<<<<<<<<<<<<<<<<<<<
    const createCustomIcon = (className, htmlContent) => L.divIcon({
        className: `custom-marker-icon ${className}`,
        html: htmlContent,
        iconSize: [24, 24], // Ajuste conforme o CSS
        iconAnchor: [12, 24], // Ponto 'inferior central' do ícone
        popupAnchor: [0, -24] // Onde o popup se ancora em relação ao ícone
    });

    const treeIcon = createCustomIcon('marker-arvore', '<i class="bi bi-tree-fill"></i>');
    const alertIcon = createCustomIcon('marker-denuncia', '<i class="bi bi-exclamation-triangle-fill"></i>');
    const suggestionIcon = createCustomIcon('marker-sugestao', '<i class="bi bi-lightbulb-fill"></i>');
    const ghostIcon = createCustomIcon('marker-fantasma', '<i class="bi bi-pin-fill"></i>'); // Ícone para o fantasma

    // --- CAMADAS, DADOS, PAINÉIS ---
    const camadaArvores = L.markerClusterGroup();
    const camadaSolicitacoes = L.layerGroup();
    const camadaAreas = L.layerGroup();
    const areaLayers = {};

    const arvoresData = getJsonData('arvores-data-json') || [];
    const solicitacoesData = getJsonData('solicitacoes-data-json') || [];
    const areasData = getJsonData('areas-data-json') || [];

    const detailsPanel = document.getElementById('details-panel');
    const detailsTitle = document.getElementById('details-title');
    const detailsContent = document.getElementById('details-content');
    const closeDetailsBtn = document.getElementById('close-details-btn');
    if(closeDetailsBtn) closeDetailsBtn.addEventListener('click', () => detailsPanel.classList.add('d-none'));

    // --- PROCESSAMENTO DAS CAMADAS (USANDO OS NOVOS ÍCONES) ---
    arvoresData.forEach(arvore => {
        if (arvore.lat && arvore.lon) {
            const marker = L.marker([arvore.lat, arvore.lon], { icon: treeIcon, treeId: arvore.id }); // Add treeId to options
            marker.on('click', () => {
                const content = `<p class="mb-1 small"><strong>Científico:</strong> ${arvore.nome_cientifico || 'N/A'}</p><p class="mb-1 small"><strong>Saúde:</strong> ${arvore.saude || 'N/A'}</p><p class="mb-1 small"><strong>Plantio:</strong> ${arvore.plantio || 'N/A'}</p><div class="mt-2"><button class="btn btn-danger-outline btn-sm" onclick="deleteTree(${arvore.id})"><i class="bi bi-trash-fill me-1"></i> Apagar Árvore</button></div>`;
                detailsTitle.innerHTML = `<i class="bi bi-tree-fill text-success me-2"></i> ${arvore.nome}`;
                detailsContent.innerHTML = content;
                if(detailsPanel) detailsPanel.classList.remove('d-none');
            });
            camadaArvores.addLayer(marker);
        }
    });

    const solicitacaoMarkers = {};
    solicitacoesData.forEach(solicitacao => {
        if (solicitacao.lat && solicitacao.lon) {
            const iconeEscolhido = (solicitacao.tipo_codigo === 'DENUNCIA') ? alertIcon : suggestionIcon;
            const marker = L.marker([solicitacao.lat, solicitacao.lon], { icon: iconeEscolhido, solicitacaoId: solicitacao.id }); // Add solicitacaoId
            marker.on('click', () => {
                const content = `<p class="mb-1 small"><strong>Status:</strong> ${solicitacao.status || 'N/A'}</p><p class="mb-1 small">${solicitacao.descricao || 'N/A'}</p><a href="/solicitacoes/${solicitacao.id}/" class="btn btn-secondary-custom btn-sm mt-2">Ver Detalhes</a>`;
                detailsTitle.innerHTML = `<i class="bi bi-file-earmark-text-fill text-warning me-2"></i> ${solicitacao.tipo_display}`;
                detailsContent.innerHTML = content;
                 if(detailsPanel) detailsPanel.classList.remove('d-none');
            });
            camadaSolicitacoes.addLayer(marker);
            solicitacaoMarkers[solicitacao.id] = marker;
        }
    });

    areasData.forEach(area => {
        if (area.geom) {
            try {
                const areaLayer = L.geoJSON(area.geom, { style: { color: "#6f42c1", weight: 2 } });
                areaLayer.on('click', () => {
                    const content = `<p class="mb-1 small"><strong>Tipo:</strong> ${area.tipo || 'N/A'}</p><p class="mb-1 small"><strong>Status:</strong> ${area.status || 'N/A'}</p><button class="btn btn-secondary-custom btn-sm mt-2" onclick="openEditModal(${area.id})">Editar Detalhes</button>`;
                    detailsTitle.innerHTML = `<i class="bi bi-bounding-box text-primary me-2"></i> ${area.nome}`;
                    detailsContent.innerHTML = content;
                     if(detailsPanel) detailsPanel.classList.remove('d-none');
                });
                camadaAreas.addLayer(areaLayer);
                areaLayers[area.id] = areaLayer;
            } catch (e) {
                 console.error(`Erro ao processar GeoJSON da área #${area.id}:`, e, area.geom);
            }
        }
    });

    // --- CONTROLE DE CAMADAS (AGORA COM OS NOVOS ÍCONES) ---
    let camadaHeatmap = null;
    if (arvoresData.length > 0) {
        const heatPoints = arvoresData.map(arvore => [arvore.lat, arvore.lon, 1]);
        camadaHeatmap = L.heatLayer(heatPoints, { radius: 25 });
    }

    const baseLayers = {};
    const overlayLayers = {
        // Agora usa ícones Bootstrap com o CSS customizado
        "<span class='layer-name'><i class='bi bi-tree-fill text-success me-1'></i> Árvores</span>": camadaArvores,
        "<span class='layer-name'><i class='bi bi-file-earmark-text-fill text-warning me-1'></i> Solicitações</span>": camadaSolicitacoes,
        "<span class='layer-name'><i class='bi bi-bounding-box text-primary me-1'></i> Áreas Planejadas</span>": camadaAreas
    };
    if (camadaHeatmap) {
         overlayLayers["<span class='layer-name'><i class='bi bi-thermometer-half text-danger me-1'></i> Mapa de Calor</span>"] = camadaHeatmap;
    }

    L.control.layers(baseLayers, overlayLayers, { collapsed: false, position: 'topright' }).addTo(map);
    map.addLayer(camadaArvores);
    map.addLayer(camadaSolicitacoes);
    map.addLayer(camadaAreas);

    // --- CONTROLE DE DESENHO (Leaflet.draw) ---
    L.drawLocal.draw.toolbar.actions.title = 'Cancelar desenho';
    L.drawLocal.draw.toolbar.actions.text = 'Cancelar';
    L.drawLocal.draw.toolbar.finish.title = 'Finalizar desenho';
    L.drawLocal.draw.toolbar.finish.text = 'Finalizar';
    L.drawLocal.draw.toolbar.undo.title = 'Apagar último ponto';
    L.drawLocal.draw.toolbar.undo.text = 'Desfazer';
    L.drawLocal.draw.toolbar.buttons.polygon = 'Desenhar uma área';
    L.drawLocal.draw.toolbar.buttons.rectangle = 'Desenhar um retângulo';
    L.drawLocal.draw.toolbar.buttons.marker = 'Marcar um ponto (nova árvore)';
    L.drawLocal.draw.handlers.polygon.tooltip.start = 'Clique para começar a desenhar.';
    L.drawLocal.draw.handlers.polygon.tooltip.cont = 'Continue clicando para desenhar.';
    L.drawLocal.draw.handlers.polygon.tooltip.end = 'Clique no primeiro ponto para fechar.';
    L.drawLocal.draw.handlers.marker.tooltip.start = 'Clique no mapa para adicionar uma árvore.';

    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    const drawControl = new L.Control.Draw({ 
        position: 'topleft', 
        edit: { featureGroup: drawnItems },
        draw: { 
            polygon: true, 
            polyline: false, 
            rectangle: true, 
            circle: false, 
            circlemarker: false, 
            marker: { icon: treeIcon }, // Usa o ícone verde para o desenho de nova árvore <<<<<<<<<<<<<<<
        } 
    });
    map.addControl(drawControl);

    const drawControlContainer = drawControl.getContainer();
    if(drawControlContainer) {
        map.on('draw:drawstart', () => drawControlContainer.classList.add('drawing-active'));
        map.on('draw:drawstop', () => drawControlContainer.classList.remove('drawing-active'));
    }

    let temporaryLayer = null;
    let editingAreaId = null;

    map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        const layerType = event.layerType;

        if (layerType === 'marker') {
            const coords = layer.getLatLng();
            if(addTreeForm) addTreeForm.reset();
            if (typeof $ !== 'undefined' && $.fn.select2) {
                $('#tree-especie').val(null).trigger('change');
            }
            const treeLatInput = document.getElementById('tree-lat');
            const treeLonInput = document.getElementById('tree-lon');
            if(treeLatInput) treeLatInput.value = coords.lat.toFixed(6);
            if(treeLonInput) treeLonInput.value = coords.lng.toFixed(6);
            
            if(addTreeModal) addTreeModal.show();
            
            if (typeof $ !== 'undefined' && $.fn.select2 && addTreeModalEl) {
                addTreeModalEl.addEventListener('shown.bs.modal', () => {
                    $('#tree-especie').select2({ 
                        placeholder: "Busque e selecione uma espécie", 
                        dropdownParent: $('#addTreeModal') 
                    });
                }, { once: true });
            } else if (addTreeModalEl) {
                 console.warn("jQuery or Select2 not found. Select de espécie no modal pode não funcionar.");
            }

            drawnItems.addLayer(layer);
            if (addTreeModalEl) {
                addTreeModalEl.addEventListener('hidden.bs.modal', () => {
                    if (drawnItems.hasLayer(layer)) {
                        drawnItems.removeLayer(layer);
                    }
                }, { once: true });
            }
        } else { // Polygon or Rectangle
            temporaryLayer = layer;
            drawnItems.addLayer(temporaryLayer);
            temporaryLayer.bindPopup("Analisando área...").openPopup();
            const geometry = temporaryLayer.toGeoJSON().geometry;

            if (!analisarAreaUrl) {
                console.error("URL para analisar área não definida.");
                temporaryLayer.setPopupContent("Erro: URL de análise não configurada.");
                return;
            }

            fetch(analisarAreaUrl, { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }, 
                body: JSON.stringify({ geometry: geometry }) 
            })
            .then(response => response.ok ? response.json() : Promise.reject('Erro na resposta da API'))
            .then(data => {
                if (data.status === 'ok') {
                    const container = document.createElement('div');
                    container.innerHTML = `<h6>Diagnóstico Rápido</h6><hr class="my-1"><p class="mb-1 small"><strong>Árvores na área:</strong> ${data.contagem_arvores}</p><p class="mb-1 small"><strong>Solicitações na área:</strong> ${data.contagem_solicitacoes}</p><div class="mt-2 text-center"><button class="btn btn-sm btn-success" id="btn-salvar-desenho">Salvar Área</button> <button class="btn btn-sm btn-danger" id="btn-descartar-desenho">Descartar</button></div>`;
                    
                    const btnSalvar = container.querySelector('#btn-salvar-desenho');
                    const btnDescartar = container.querySelector('#btn-descartar-desenho');

                    if(btnSalvar) btnSalvar.addEventListener('click', () => {
                        editingAreaId = null;
                        if(areaForm) areaForm.reset();
                        if (typeof $ !== 'undefined' && $.fn.select2) {
                            $('#id_especies').val(null).trigger('change');
                        }
                        if(modalTitle) modalTitle.textContent = 'Detalhes da Nova Área';
                        if(deleteAreaButton) deleteAreaButton.classList.add('d-none');
                        if(areaModal) areaModal.show();
                    });
                    if(btnDescartar) btnDescartar.addEventListener('click', () => drawnItems.removeLayer(temporaryLayer));
                    
                    temporaryLayer.setPopupContent(container);
                } else {
                    temporaryLayer.setPopupContent(`Erro: ${data.message || 'Análise falhou.'}`);
                }
            }).catch(error => {
                console.error("Erro no Fetch:", error);
                temporaryLayer.setPopupContent("Erro de comunicação ao analisar.");
            });
        }
    });

    // --- LÓGICA DE SUBMISSÃO DOS MODAIS ---
    if (submitNewTreeButton && addTreeForm && addTreeModal) {
        submitNewTreeButton.addEventListener('click', function() {
            const formData = new FormData(addTreeForm);
            if (!formData.get('especie')) {
                showToast('Erro', 'Selecione uma espécie.', true);
                return;
            }

            fetch('/api/instancias/nova/', { method: 'POST', headers: { 'X-CSRFToken': csrftoken }, body: formData })
            .then(response => response.ok ? response.json() : Promise.reject('Erro ao salvar árvore'))
            .then(result => {
                if (result.status === 'ok') {
                    addTreeModal.hide();
                    showToast('Sucesso!', result.message || 'Árvore adicionada!');
                    const tempMarker = drawnItems.getLayers().find(layer => layer instanceof L.Marker);
                    if (tempMarker) drawnItems.removeLayer(tempMarker);
                    adicionarMarcadorArvoreAoMapa(result.nova_arvore);
                } else {
                    showToast('Erro', result.message || 'Não foi possível salvar.', true);
                }
            }).catch(error => {
                console.error('Erro no fetch:', error);
                showToast('Erro de Rede', 'Falha na comunicação.', true);
            });
        });
    }

    window.openEditModal = function(areaId) {
        if (!areaForm || !modalTitle || !deleteAreaButton || !areaModal) return;
        
        editingAreaId = areaId;
        temporaryLayer = null;
        modalTitle.textContent = 'Editar Detalhes da Área';
        deleteAreaButton.classList.remove('d-none');
        
        fetch(`/api/areas/${areaId}/`)
            .then(res => res.ok ? res.json() : Promise.reject('Erro ao buscar área'))
            .then(data => {
                areaForm.elements['nome'].value = data.nome || '';
                areaForm.elements['tipo'].value = data.tipo || '';
                areaForm.elements['status'].value = data.status || '';
                if (typeof $ !== 'undefined' && $.fn.select2) {
                    $('#id_especies').val(data.especies || []).trigger('change');
                } else {
                    const select = areaForm.elements['especies'];
                    if (select) {
                           const speciesIds = (data.especies || []).map(String);
                           Array.from(select.options).forEach(option => {
                                option.selected = speciesIds.includes(option.value);
                           });
                    }
                }
                areaModal.show();
            })
            .catch(error => {
                 console.error("Erro ao buscar dados da área:", error);
                 showToast("Erro", "Não foi possível carregar os dados da área.", true);
            });
    }

    if (saveAreaButton && areaForm && areaModal) {
        saveAreaButton.addEventListener('click', function() {
            const formData = new FormData(areaForm);
            const formObject = {};
            formObject['especies'] = $('#id_especies').val() || [];
            formData.forEach((value, key) => {
                 if (key !== 'especies' && key !== 'csrfmiddlewaretoken') {
                     formObject[key] = value;
                 }
            });

            let url, method, finalData;
            if (editingAreaId) {
                url = `/api/areas/${editingAreaId}/`;
                method = 'PUT';
                finalData = { form_data: formObject };
            } else if (temporaryLayer) {
                url = "/api/salvar_area/";
                method = 'POST';
                finalData = { 
                    form_data: formObject, 
                    geometry: temporaryLayer.toGeoJSON().geometry
                };
            } else {
                 console.error("Tentando salvar área sem ID de edição ou camada temporária.");
                 showToast("Erro", "Não há área selecionada ou desenhada para salvar.", true);
                 return;
            }

            fetch(url, { 
                method: method, 
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }, 
                body: JSON.stringify(finalData) 
            })
            .then(response => response.ok ? response.json() : response.json().then(errData => Promise.reject(errData)))
            .then(data => {
                if (data.status === 'ok') {
                    showToast('Sucesso!', data.message || 'Área salva.');
                    areaModal.hide();
                    if (!editingAreaId && temporaryLayer) {
                         drawnItems.removeLayer(temporaryLayer);
                         temporaryLayer = null;
                    }
                    adicionarOuAtualizarAreaAoMapa(data.area_salva || data.area_atualizada);
                } else {
                     let errorMsg = data.message || 'Dados inválidos.';
                     if (data.errors) {
                         try {
                             const errorsParsed = JSON.parse(data.errors);
                             errorMsg += '\n' + Object.entries(errorsParsed)
                                 .map(([field, msgs]) => `${field}: ${msgs.map(m => m.message || m).join(', ')}`)
                                 .join('\n');
                         } catch (e) { console.warn("Could not parse Django form errors:", data.errors); }
                     }
                    showToast('Erro ao Salvar', errorMsg, true);
                }
            })
             .catch(error => {
                 console.error("Erro no Fetch ao salvar área:", error);
                 let errorMsg = "Falha na comunicação.";
                 if (typeof error === 'object' && error !== null && error.message) {
                     errorMsg = error.message;
                 } else if (typeof error === 'string') {
                     errorMsg = error;
                 }
                 showToast('Erro de Rede', errorMsg, true);
            });
        });
    }

    if (deleteAreaButton) deleteAreaButton.addEventListener('click', () => {
        if (editingAreaId) {
             window.location.href = `/areas/${editingAreaId}/delete/`;
        }
    });

    window.deleteTree = function(treeId) {
        if (!treeIdPlaceholder || !confirmDeleteBtn || !deleteConfirmModal) return;
        treeIdPlaceholder.textContent = treeId;
        confirmDeleteBtn.dataset.treeId = treeId;
        deleteConfirmModal.show();
    }

    if (confirmDeleteBtn && deleteConfirmModal) {
        confirmDeleteBtn.addEventListener('click', function() {
            const treeId = this.dataset.treeId;
            if (treeId) {
                fetch(`/api/arvores/${treeId}/delete/`, { method: 'DELETE', headers: { 'X-CSRFToken': csrftoken } })
                .then(res => res.ok ? res.json() : Promise.reject('Erro ao deletar árvore'))
                .then(data => {
                    if (data.status === 'ok') {
                        showToast('Sucesso!', data.message || `Árvore #${treeId} deletada.`);
                        removerMarcadorArvoreDoMapa(treeId);
                    } else {
                        showToast('Erro!', data.message || 'Não foi possível deletar.', true);
                    }
                }).catch(error => {
                    console.error('Erro:', error);
                    showToast('Erro de Rede!', 'Falha na comunicação.', true);
                }).finally(() => deleteConfirmModal.hide());
            }
        });
    }

    // --- FOCO E EXIBIDOR DE COORDENADAS ---
    const coordsDisplay = document.getElementById('coords-display');
    if (coordsDisplay) {
        map.on('mousemove', e => { coordsDisplay.innerHTML = `Lat: ${e.latlng.lat.toFixed(5)} | Lon: ${e.latlng.lng.toFixed(5)}`; });
        map.on('mouseout', () => { coordsDisplay.innerHTML = 'Lat: -- | Lon: --'; });
    }
    
    // ======================================================
    // ============ LÓGICA DO "GPS FANTASMA" NO JS ============
    // ======================================================
    let focoRealizado = false;

    if (focoSolicitacao) {
        console.log("Focando na solicitação finalizada/recusada:", focoSolicitacao);
        
        // Usa o ícone cinza "fantasma" <<<<<<<<<<<<<<<
        const focoMarker = L.marker([focoSolicitacao.lat, focoSolicitacao.lon], { 
                icon: ghostIcon, // Usa o novo ícone fantasma
                zIndexOffset: 1000 // Para garantir que fique visível
            })
            .addTo(map)
            .bindPopup(`
                <div class="map-popup-content">
                    <h5>${focoSolicitacao.tipo_display} #${focoSolicitacao.id}</h5>
                    <p class="small text-muted">Status: <strong>${focoSolicitacao.status}</strong></p>
                    <hr class="my-1">
                    <p class="small">${focoSolicitacao.descricao}</p>
                    <a href="/solicitacoes/${focoSolicitacao.id}/" class="btn btn-secondary-custom btn-sm mt-2">Ver Detalhes</a>
                </div>
            `)
            .openPopup(); 

        map.setView([focoSolicitacao.lat, focoSolicitacao.lon], 18);
        focoRealizado = true;
    }
    // ======================================================

    // --- INICIA A LÓGICA DE CIDADES E DEPOIS O FOCO ANTIGO (SE NÃO HOUVE FOCO FANTASMA) ---
    iniciarControleDeCidades().then(() => {
        if (!focoRealizado) { 
            if (solicitacaoFocoId_antigo && solicitacaoMarkers[solicitacaoFocoId_antigo]) {
                const markerToFocus = solicitacaoMarkers[solicitacaoFocoId_antigo];
                map.flyTo(markerToFocus.getLatLng(), 18, { duration: 1 });
                setTimeout(() => markerToFocus.fire('click'), 1000);
                focoRealizado = true;
            }
            if (areaFocoId && areaLayers[areaFocoId]) {
                if (!focoRealizado) {
                    const layerToFocus = areaLayers[areaFocoId];
                    map.fitBounds(layerToFocus.getBounds());
                    layerToFocus.fire('click');
                }
            }
        }
    });

    // --- FUNÇÕES NOVAS PARA ATUALIZAR MAPA SEM RELOAD ---
    function adicionarMarcadorArvoreAoMapa(arvore) {
        if (arvore && arvore.lat && arvore.lon) {
            const marker = L.marker([arvore.lat, arvore.lon], { icon: treeIcon, treeId: arvore.id }); // Usa o ícone verde
            marker.on('click', () => {
                const content = `<p class="mb-1 small"><strong>Científico:</strong> ${arvore.nome_cientifico || 'N/A'}</p><p class="mb-1 small"><strong>Saúde:</strong> ${arvore.saude || 'N/A'}</p><p class="mb-1 small"><strong>Plantio:</strong> ${arvore.plantio || 'N/A'}</p><div class="mt-2"><button class="btn btn-danger-outline btn-sm" onclick="deleteTree(${arvore.id})"><i class="bi bi-trash-fill me-1"></i> Apagar Árvore</button></div>`;
                detailsTitle.innerHTML = `<i class="bi bi-tree-fill text-success me-2"></i> ${arvore.nome}`;
                detailsContent.innerHTML = content;
                if(detailsPanel) detailsPanel.classList.remove('d-none');
            });
            camadaArvores.addLayer(marker);
        }
    }

    function removerMarcadorArvoreDoMapa(treeId) {
        camadaArvores.eachLayer(layer => {
             // Opcional: A gente adicionou treeId na hora de criar o marker.
             // Se o layer for um Cluster, temos que procurar dentro dele.
             // Por simplicidade, faremos uma busca por todos os marcadores.
             if (layer.options && layer.options.treeId == treeId) {
                  camadaArvores.removeLayer(layer);
             }
        });
        // Para o caso de marcadores dentro de clusters, a remoção direta pode ser mais complexa.
        // Uma solução mais robusta para clusters seria recarregar os dados das árvores ou
        // ter um controle de markers fora do cluster para facilitar a remoção.
        // Por ora, o .eachLayer acima funciona para marcadores que não estão agrupados.
        // Para marcadores agrupados, o refreshClusters pode ajudar a "limpar" clusters vazios.
        camadaArvores.refreshClusters(); 
        if(detailsPanel) detailsPanel.classList.add('d-none');
    }

    function adicionarOuAtualizarAreaAoMapa(areaData) {
          if (!areaData || !areaData.geom) return;

          const areaId = areaData.id;
          let layer = areaLayers[areaId];

          const style = { color: "#6f42c1", weight: 2 };
          const geoJsonFeature = { type: "Feature", properties: areaData, geometry: areaData.geom };

          if (layer) {
              camadaAreas.removeLayer(layer);
          }
          
          layer = L.geoJSON(geoJsonFeature, { style: style });
          layer.on('click', () => {
              const content = `<p class="mb-1 small"><strong>Tipo:</strong> ${areaData.tipo || 'N/A'}</p><p class="mb-1 small"><strong>Status:</strong> ${areaData.status || 'N/A'}</p><button class="btn btn-secondary-custom btn-sm mt-2" onclick="openEditModal(${areaData.id})">Editar Detalhes</button>`;
              detailsTitle.innerHTML = `<i class="bi bi-bounding-box text-primary me-2"></i> ${areaData.nome}`;
              detailsContent.innerHTML = content;
              if(detailsPanel) detailsPanel.classList.remove('d-none');
          });
          
          camadaAreas.addLayer(layer);
          areaLayers[areaId] = layer;
    }

}); // Fim do DOMContentLoaded