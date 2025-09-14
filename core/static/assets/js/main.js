// main.js - Arquivo centralizado de scripts

// Funções relacionadas ao modal de perfil
function setupProfileModal() {
    // Função global para abrir o modal
    window.carregarModalPerfil = function() {
        const avatarUrl = document.body.getAttribute('data-avatar-url');
        const avatarPreview = document.getElementById('avatarPreview');
        
        // Atualiza a imagem com cache busting
        if (avatarUrl && avatarPreview) {
            avatarPreview.src = `${avatarUrl}?t=${new Date().getTime()}`;
        }

        // Preenche os campos do formulário
        const nomeInput = document.getElementById('nome');
        const emailInput = document.getElementById('email');
        const cpfInput = document.getElementById('cpf');
        
        if (nomeInput) nomeInput.value = nomeInput.getAttribute('value') || '';
        if (emailInput) emailInput.value = emailInput.getAttribute('value') || '';
        if (cpfInput) {
            const rawCpf = cpfInput.getAttribute('value') || '';
            if (rawCpf.length === 11) {
                cpfInput.value = rawCpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
            } else {
                cpfInput.value = rawCpf;
            }
        }

        // Abre o modal
        $('#perfilModal').modal('show');
    };

    // Preview do avatar
    document.getElementById('avatarUpload')?.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                // Atualiza a prévia no modal
                const avatarPreview = document.getElementById('avatarPreview');
                if (avatarPreview) avatarPreview.src = event.target.result;

                // Atualiza a imagem na navbar
                document.querySelectorAll('.img-profile').forEach(img => {
                    img.src = event.target.result;
                });
            };
            reader.readAsDataURL(file);
        }
    });

    // Envio do formulário
    const formEditarPerfil = document.getElementById('formEditarPerfil');
    if (formEditarPerfil) {
        formEditarPerfil.addEventListener('submit', function(e) {
            e.preventDefault();
            handleProfileFormSubmit(this);
        });
    }
}

function handleProfileFormSubmit(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('[type="submit"]');
    const avatarElements = document.querySelectorAll('.img-profile, #avatarPreview');
    const profileUrl = form.getAttribute('action') || document.body.getAttribute('data-profile-url');
    const defaultAvatar = document.body.getAttribute('data-default-avatar');

    // Validação de senha
    if (formData.get('senha') {
        if (formData.get('senha') !== formData.get('confirmar_senha')) {
            Swal.fire('Erro!', 'As senhas não coincidem', 'error');
            return false;
        }
        if (formData.get('senha').length < 6) {
            Swal.fire('Erro!', 'A senha deve ter pelo menos 6 caracteres', 'error');
            return false;
        }
    }

    // Feedback visual
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Salvando...
    `;

    // Timestamp para cache
    const timestamp = new Date().getTime();

    fetch(profileUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(/* ... manter o resto da função igual ao anterior ... */)
    .catch(/* ... manter o tratamento de erro ... */)
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Salvar Alterações';
        document.getElementById('avatarUpload').value = '';
    });
}

// Funções relacionadas a máscaras de formulário
function setupFormMasks() {
    $(document).ready(function() {
        // Máscara para CPF
        $('.cpf-mask').mask('000.000.000-00');

        // Remove a formatação antes de enviar
        $('#formEditarPerfil').on('submit', function(e) {
            let cpfInput = $('#cpf');
            cpfInput.val(cpfInput.val().replace(/\D/g, '')); // Remove não-dígitos
        });

        // Formata ao exibir
        $('#perfilModal').on('show.bs.modal', function() {
            let cpfInput = $('#cpf');
            let cpf = cpfInput.val();
            if (cpf && cpf.length === 11) {
                cpfInput.val(cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4"));
            }
        });
    });
}

// Função para mostrar mensagens flash
function showFlashMessages() {
    const messagesContainer = document.getElementById('flash-messages');
    if (messagesContainer) {
        const messages = JSON.parse(messagesContainer.getAttribute('data-messages'));
        if (messages && messages.length > 0) {
            messages.forEach(({category, message}) => {
                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: category,
                    title: message,
                    showConfirmButton: false,
                    timer: 5000,
                    timerProgressBar: true
                });
            });
        }
    }
}

// Função de debounce
function setupDebounce() {
    function debounce(func, timeout = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }

    // Exemplo de uso:
    window.addEventListener('resize', debounce(() => {
        console.log('Resized');
    }));
}

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    setupProfileModal();
    setupFormMasks();
    showFlashMessages();
    setupDebounce();
});