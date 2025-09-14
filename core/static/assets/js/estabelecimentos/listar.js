function confirmarExclusao(id, nome) {
    Swal.fire({
        title: 'Confirmar Exclusão',
        html: `Deseja realmente excluir <b>${nome}</b>?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sim, excluir!'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/estabelecimentos/excluir/${id}`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({
                            title: 'Excluído!',
                            text: 'O estabelecimento foi removido com sucesso.',
                            icon: 'success'
                        }).then(() => {
                            // Redireciona para a URL garantida do Flask
                            window.location.href = data.redirect_url;
                        });
                    }
                })
                .catch(error => {
                    console.error('Erro:', error);
                    Swal.fire('Erro!', 'Falha na comunicação', 'error');
                });
        }
    });
}
// Inicialização do DataTable
$(document).ready(function () {
    $('#dataTable').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.10.25/i18n/Portuguese-Brasil.json"
        },
        "order": [[0, "asc"]],
        "responsive": true
    });
});

function carregarModal(acao, id) {
    // Mostra um spinner enquanto carrega
    $('#modal-content').html(`
        <div class="modal-body text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Carregando...</span>
            </div>
            <p class="mt-2">Carregando...</p>
        </div>
    `);

    const modal = new bootstrap.Modal(document.getElementById('estabelecimentoModal'));
    modal.show();

    const url = acao === 'ver'
        ? `/estabelecimentos/${id}/modal`
        : `/estabelecimentos/editar/${id}/modal`;

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Erro ao carregar');
            return response.text();
        })
        .then(html => {
            $('#modal-content').html(html);

            // Se for edição, inicializa o formulário
            if (acao === 'editar') {
                initFormEdicao();
            }
        })
        .catch(error => {
            $('#modal-content').html(`
                <div class="modal-body">
                    <div class="alert alert-danger">
                        Falha ao carregar: ${error.message}
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Fechar</button>
                </div>
            `);
        });
}

function initFormEdicao() {
    $('#formEdicao').on('submit', function (e) {
        e.preventDefault();

        // Mostra spinner no botão de submit
        const submitBtn = $(this).find('[type="submit"]');
        submitBtn.prop('disabled', true).html(`
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            Salvando...
        `);

        fetch($(this).attr('action'), {
            method: 'POST',
            body: new FormData(this)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Fecha o modal e recarrega a página
                    $('#estabelecimentoModal').modal('hide');
                    Swal.fire({
                        title: 'Sucesso!',
                        text: data.message,
                        icon: 'success'
                    }).then(() => {
                        window.location.href = data.redirect_url || window.location.href;
                    });
                } else {
                    Swal.fire('Erro!', data.message, 'error');
                    submitBtn.prop('disabled', false).text('Salvar Alterações');
                }
            })
            .catch(error => {
                Swal.fire('Erro!', 'Falha na comunicação com o servidor', 'error');
                submitBtn.prop('disabled', false).text('Salvar Alterações');
            });
    });
}