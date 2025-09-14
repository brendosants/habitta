// static/assets/js/pages/modals.js

// Função debounce para eventos frequentes
function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

// Funções específicas do modal de perfil
function initializeProfileModal() {
    // Função para abrir o modal
    window.carregarModalPerfil = function() {
        const avatarUrl = $("#avatarPreview").data('avatar-url');
        const avatarPreview = document.getElementById('avatarPreview');
        
        // Atualiza a imagem com cache busting
        if (avatarUrl && avatarPreview) {
            avatarPreview.src = avatarUrl + '?t=' + new Date().getTime();
        }

        // Preenche os campos do formulário (os valores agora vêm de data-attributes)
        $('#nome').val($("#nome").data('value'));
        $('#email').val($("#email").data('value'));
        $('#cpf').val($("#cpf").data('value'));

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
    $('#formEditarPerfil').off('submit').on('submit', function(e) {
        e.preventDefault();
        handleProfileFormSubmit(this);
    });

    // Máscara para CPF e formatação
    $('.cpf-mask').mask('000.000.000-00');
    
    // Evento quando o modal é aberto
    $('#perfilModal').on('show.bs.modal', function() {
        const avatarUrl = $("#avatarPreview").data('avatar-url');
        if (avatarUrl) {
            document.getElementById('avatarPreview').src = avatarUrl + '?t=' + new Date().getTime();
        }
        
        // Formata o CPF ao exibir
        let cpfInput = $('#cpf');
        let cpf = cpfInput.val() || cpfInput.data('value');
        if (cpf && cpf.length === 11) {
            cpfInput.val(cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4"));
        }
    });
}

// Função para lidar com o submit do formulário
function handleProfileFormSubmit(form) {
    const formData = new FormData(form);
    const submitBtn = $(form).find('[type="submit"]');
    const avatarElements = document.querySelectorAll('.img-profile, #avatarPreview');

    // Validação de senha
    if (formData.get('senha') && formData.get('senha') !== formData.get('confirmar_senha')) {
        Swal.fire('Erro!', 'As senhas não coincidem', 'error');
        return false;
    }

    // Feedback visual
    submitBtn.prop('disabled', true).html(
        `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...`
    );

    // Remove formatação do CPF antes de enviar
    let cpfInput = $('#cpf');
    cpfInput.val(cpfInput.val().replace(/\D/g, ''));

    const timestamp = new Date().getTime();
    const endpoint = $("#formEditarPerfil").data('url') || "/atualizar_perfil";

    fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(async response => {
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.message || 'Erro na resposta do servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            handleProfileUpdateSuccess(data, avatarElements, timestamp);
        } else {
            Swal.fire({
                title: 'Erro!',
                text: data.message || 'Ocorreu um erro ao atualizar',
                icon: 'error'
            });
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        Swal.fire({
            title: 'Erro de Comunicação',
            text: error.message || 'Não foi possível conectar ao servidor',
            icon: 'error'
        });
    })
    .finally(() => {
        submitBtn.prop('disabled', false).text('Salvar Alterações');
        $('#avatarUpload').val('');
    });
}

// Função para lidar com sucesso na atualização
function handleProfileUpdateSuccess(data, avatarElements, timestamp) {
    // Atualiza o avatar
    if (data.avatar_url) {
        const newUrl = `${data.avatar_url}?t=${timestamp}`;
        avatarElements.forEach(img => {
            img.src = newUrl;
            img.onerror = () => {
                img.src = $("#avatarPreview").data('default-avatar') || "/static/assets/img/undraw_profile.svg";
            };
        });
    }

    // Mostra mensagem de sucesso
    Swal.fire({
        title: 'Sucesso!',
        html: `<p>${data.message}</p>${data.avatar_url ? '<p>Imagem atualizada!</p>' : ''}`,
        icon: 'success',
        willClose: () => window.location.reload()
    });

    // Atualiza o nome do usuário se necessário
    if (data.user_data?.nome) {
        $('.user-name').text(data.user_data.nome);
    }
}

// Inicialização quando o DOM estiver pronto
$(document).ready(function() {
    initializeProfileModal();
    
    // Exemplo de uso do debounce
    window.addEventListener('resize', debounce(() => {
        console.log('Resized');
    }));
});