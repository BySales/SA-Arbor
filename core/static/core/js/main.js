document.addEventListener('DOMContentLoaded', function() {
    // --- LÓGICA DO OLHO DA SENHA ---
    const setupToggle = (toggleId, inputId) => {
        const toggle = document.querySelector(toggleId);
        const input = document.querySelector(inputId);
        if (toggle && input) {
            toggle.addEventListener('click', function () {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.classList.toggle('bi-eye');
                this.classList.toggle('bi-eye-slash');
            });
        }
    };
    setupToggle('#togglePassword', '#id_password');
    setupToggle('#togglePassword1', '#id_password1');
    setupToggle('#togglePassword2', '#id_password2');

    // A LÓGICA DA SIDEBAR FOI COMPLETAMENTE REMOVIDA DAQUI.
});

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('id_imagem'); // Assumindo que o ID do seu input de imagem é 'id_imagem'
    const fileNameDisplay = document.getElementById('file-name-display');
    const removeImageBtn = document.querySelector('.remove-image-btn');
    const imageClearCheckbox = document.getElementById('id_imagem-clear'); // O checkbox oculto para "limpar"

    if (fileInput) {
        // Atualiza o nome do arquivo na área de upload quando um novo é selecionado
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileNameDisplay.textContent = this.files[0].name;
            } else {
                // Se a imagem for removida e nenhum novo arquivo for selecionado, volta ao texto padrão
                fileNameDisplay.textContent = 'Escolher arquivo...';
            }
        });
    }

    // Lógica para o botão de remover imagem
    if (removeImageBtn && imageClearCheckbox) {
        removeImageBtn.addEventListener('click', function() {
            if (confirm('Tem certeza que deseja remover esta imagem?')) {
                // Marca o checkbox oculto para indicar ao Django para remover a imagem
                imageClearCheckbox.checked = true;
                
                // Esconde a imagem de preview
                const imagePreviewCard = document.querySelector('.image-preview-card');
                if (imagePreviewCard) {
                    imagePreviewCard.style.display = 'none';
                }

                // Reseta o input de arquivo para garantir que nenhuma imagem antiga seja enviada
                if (fileInput) {
                    fileInput.value = '';
                }

                // Atualiza o texto da área de upload
                fileNameDisplay.textContent = 'Escolher arquivo...';

                // Desativa o botão de remover
                removeImageBtn.style.display = 'none';
            }
        });
    }

    // Ativa os tooltips do Bootstrap (apenas se ainda não estiver ativado globalmente)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    })
});