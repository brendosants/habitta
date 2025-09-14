// static/assets/js/pages/modals.js

document.addEventListener('DOMContentLoaded', function() {
    initializeProfileModal();
});

function initializeProfileModal() {
    // Configura máscara do CPF
    if (window.$ && $.fn.mask) {
        $('.cpf-mask').mask('000.000.000-00');
    }

    // Função global para abrir modal
    window.carregarModalPerfil = function() {
        refreshAvatarPreview();
        $('#perfilModal').modal('show');
    };

    // Configura o formulário
    const formPerfil = document.getElementById('formEditarPerfil');
    if (formPerfil) {
        formPerfil.addEventListener('submit', handleProfileSubmit);
    }

    // Configura preview do avatar
    const avatarUpload = document.getElementById('avatarUpload');
    if (avatarUpload) {
        avatarUpload.addEventListener('change', handleAvatarUpload);
    }
}

function refreshAvatarPreview() {
    const avatarPreview = document.getElementById('avatarPreview');
    if (avatarPreview) {
        const currentSrc = avatarPreview.src.split('?')[0];
        avatarPreview.src = `${currentSrc}?t=${new Date().getTime()}`;
    }
}

function handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(event) {
        document.querySelectorAll('#avatarPreview, .img-profile').forEach(img => {
            img.src = event.target.result;
        });
    };
    reader.readAsDataURL(file);
}

async function handleProfileSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('[type="submit"]');
    
    // Validação de senha no frontend
    if (formData.get('senha') && formData.get('senha') !== formData.get('confirmar_senha')) {
        showAlert('error', 'Erro!', 'As senhas não coincidem');
        return;
    }

    // Feedback visual
    toggleSubmitButton(submitBtn, true);

    try {
        const response = await fetch(form.action || form.dataset.url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Erro na resposta do servidor');
        }

        if (data.success) {
            handleSuccessResponse(data);
        } else {
            throw new Error(data.message || 'Erro ao atualizar perfil');
        }
    } catch (error) {
        console.error('Erro:', error);
        showAlert('error', 'Erro!', error.message);
    } finally {
        toggleSubmitButton(submitBtn, false);
    }
}

function toggleSubmitButton(button, isLoading) {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            Salvando...
        `;
    } else {
        button.disabled = false;
        button.textContent = 'Salvar Alterações';
    }
}

function handleSuccessResponse(data) {
    // Atualiza avatar se necessário
    if (data.avatar_url) {
        updateAvatarImage(data.avatar_url);
    }

    // Mostra mensagem de sucesso
    showAlert('success', 'Sucesso!', data.message, () => {
        if (data.reload !== false) {
            window.location.reload();
        }
    });
}

function updateAvatarImage(avatarUrl) {
    const timestamp = new Date().getTime();
    const newUrl = `${avatarUrl}?t=${timestamp}`;
    
    document.querySelectorAll('#avatarPreview, .img-profile').forEach(img => {
        img.src = newUrl;
        img.onerror = () => {
            img.src = img.dataset.defaultAvatar || '/static/assets/img/undraw_profile.svg';
        };
    });
}

function showAlert(type, title, message, callback) {
    if (window.Swal) {
        Swal.fire({
            title: title,
            text: message,
            icon: type,
            willClose: callback ? () => callback() : undefined
        });
    } else {
        alert(`${title}: ${message}`);
        if (callback) callback();
    }
}