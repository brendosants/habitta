export class ProfileManager {
    constructor() {
        this.initProfileModal();
        this.initAvatarUpload();
        this.initProfileForm();
        this.initCPFMask();
    }

    initProfileModal() {
        window.carregarModalPerfil = () => {
            const avatarUrl = document.currentScript.getAttribute('data-avatar-url');
            const avatarPreview = document.getElementById('avatarPreview');

            avatarPreview.src = `${avatarUrl}?t=${new Date().getTime()}`;
            $('#perfilModal').modal('show');
        };

        $('#perfilModal').on('show.bs.modal', () => {
            const avatarUrl = document.currentScript.getAttribute('data-avatar-url');
            document.getElementById('avatarPreview').src = `${avatarUrl}?t=${new Date().getTime()}`;
        });
    }

    initAvatarUpload() {
        document.getElementById('avatarUpload')?.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    document.getElementById('avatarPreview').src = event.target.result;
                    document.querySelector('.img-profile').src = event.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    initProfileForm() {
        $('#formEditarPerfil').on('submit', function (e) {
            e.preventDefault();

            const form = this;
            const formData = new FormData(form);
            const submitBtn = $(form).find('[type="submit"]');
            const avatarElements = document.querySelectorAll('.img-profile, #avatarPreview');

            // Validação de senha no frontend
            if (formData.get('senha') && formData.get('senha') !== formData.get('confirmar_senha')) {
                Swal.fire('Erro!', 'As senhas não coincidem', 'error');
                return false;
            }

            // Feedback visual durante o processamento
            submitBtn.prop('disabled', true).html(`
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Salvando...
    `);

            // Adiciona timestamp para evitar cache
            const timestamp = new Date().getTime();

            fetch("{{ url_for('atualizar_perfil') }}", {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest' // Identifica como AJAX
                }
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
                        // Atualiza todas as instâncias da imagem com cache busting
                        if (data.avatar_url) {
                            const newUrl = `${data.avatar_url}?t=${timestamp}`;
                            avatarElements.forEach(img => {
                                img.src = newUrl;
                                img.onerror = () => {
                                    img.src = "{{ url_for('static', filename='assets/img/undraw_profile.svg') }}";
                                };
                            });
                        }

                        // Feedback de sucesso com mais informações
                        Swal.fire({
                            title: 'Sucesso!',
                            html: `<p>${data.message}</p>${data.avatar_url ? '<p>Imagem atualizada!</p>' : ''}`,
                            icon: 'success',
                            showConfirmButton: true,
                            timer: 3000,
                            willClose: () => {
                                // Recarrega a página quando o usuário clica em OK
                                window.location.reload();
                            }
                        });

                        // Atualiza outros campos se necessário
                        if (data.user_data) {
                            $('.user-name').text(data.user_data.nome || '{{ current_user.nome }}');
                        }
                    } else {
                        // Mensagem de erro detalhada
                        Swal.fire({
                            title: 'Erro!',
                            text: data.message || 'Ocorreu um erro ao atualizar',
                            icon: 'error',
                            showConfirmButton: true
                        });
                    }
                })
                .catch(error => {
                    console.error('Erro:', error);
                    Swal.fire({
                        title: 'Erro de Comunicação',
                        text: error.message || 'Não foi possível conectar ao servidor',
                        icon: 'error',
                        showConfirmButton: true
                    });
                })
                .finally(() => {
                    // Restaura o botão independente do resultado
                    submitBtn.prop('disabled', false).text('Salvar Alterações');

                    // Limpa o campo de arquivo para permitir nova seleção do mesmo arquivo
                    $('#avatarUpload').val('');
                });
        });
    }

    initCPFMask() {
        $('.cpf-mask').mask('000.000.000-00');

        $('#formEditarPerfil').on('submit', (e) => {
            let cpfInput = $('#cpf');
            cpfInput.val(cpfInput.val().replace(/\D/g, ''));
        });

        $('#perfilModal').on('show.bs.modal', () => {
            let cpfInput = $('#cpf');
            let cpf = cpfInput.val();
            if (cpf && cpf.length === 11) {
                cpfInput.val(cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4"));
            }
        });
    }
}