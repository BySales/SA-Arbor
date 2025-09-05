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
    setupToggle('#togglePassword2', '#id_password2');

    // --- LÓGICA DA SIDEBAR COLAPSÁVEL ---
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.querySelector('#sidebar-toggle');

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('collapsed');
        });
    }
});
