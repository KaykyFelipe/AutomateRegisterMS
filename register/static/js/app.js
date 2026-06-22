document.addEventListener('DOMContentLoaded', () => {
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');

    const searchForm = document.getElementById('search-form');
    const btnSearch = document.getElementById('btn-search');
    const searchError = document.getElementById('search-error');

    const createForm = document.getElementById('create-form');
    const btnCreate = document.getElementById('btn-create');
    const createError = document.getElementById('create-error');
    const btnBack = document.getElementById('btn-back');

    const localSelect = document.getElementById('local');
    const customLocalGroup = document.getElementById('custom-local-group');
    const customLocalInput = document.getElementById('custom_local');

    let currentEmpData = {};

    // Mostrar campo personalizado se selecionar 'Outro'
    localSelect.addEventListener('change', (e) => {
        if (e.target.value === 'Outro') {
            customLocalGroup.classList.remove('hidden');
            customLocalInput.setAttribute('required', 'true');
        } else {
            customLocalGroup.classList.add('hidden');
            customLocalInput.removeAttribute('required');
        }
    });

    // Helper para botões com loading
    const setLoading = (btn, isLoading) => {
        const text = btn.querySelector('.btn-text');
        const loader = btn.querySelector('.loader');
        if (isLoading) {
            text.classList.add('hidden');
            loader.classList.remove('hidden');
            btn.disabled = true;
        } else {
            text.classList.remove('hidden');
            loader.classList.add('hidden');
            btn.disabled = false;
        }
    };

    // Passo 1: Buscar funcionário
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        searchError.classList.add('hidden');
        setLoading(btnSearch, true);

        const matricula = document.getElementById('matricula').value.trim();
        const filial = document.getElementById('filial').value.trim();

        try {
            const res = await fetch('/api/check_employee', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ matricula, filial })
            });
            const data = await res.json();

            if (data.success) {
                currentEmpData = {
                    matricula,
                    filial_protheus: filial,
                    full_name: data.nome,
                    admissao: data.admissao
                };
                
                document.getElementById('lbl-name').textContent = data.nome;
                document.getElementById('lbl-admissao').textContent = data.admissao;
                document.getElementById('username').value = data.suggested_user;

                step1.classList.remove('active');
                step1.classList.add('hidden');
                step2.classList.remove('hidden');
                step2.classList.add('active');
            } else {
                searchError.textContent = data.message || data.error;
                searchError.classList.remove('hidden');
            }
        } catch (err) {
            searchError.textContent = 'Erro de comunicação com o servidor.';
            searchError.classList.remove('hidden');
        } finally {
            setLoading(btnSearch, false);
        }
    });

    // Passo 2: Voltar
    btnBack.addEventListener('click', () => {
        step2.classList.remove('active');
        step2.classList.add('hidden');
        step1.classList.remove('hidden');
        step1.classList.add('active');
    });

    // Passo 2: Criar Usuário
    createForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        createError.classList.add('hidden');
        setLoading(btnCreate, true);

        const cargo = document.getElementById('cargo').value.trim();
        let local = localSelect.value;
        if (local === 'Outro') {
            local = customLocalInput.value.trim();
        }
        const telefone = document.getElementById('telefone').value.trim();
        const ramal = document.getElementById('ramal').value.trim();
        const username = document.getElementById('username').value.trim();

        const payload = {
            ...currentEmpData,
            cargo,
            local,
            telefone,
            ramal,
            username
        };

        try {
            const res = await fetch('/api/create_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                document.getElementById('res-email').textContent = data.email;
                document.getElementById('res-password').textContent = data.password;
                document.getElementById('res-vpn').textContent = data.vpn_user;
                
                const sigImg = document.getElementById('res-signature-img');
                const btnDownload = document.getElementById('btn-download');
                
                sigImg.src = data.signature_url;
                btnDownload.href = data.signature_url;

                step2.classList.remove('active');
                step2.classList.add('hidden');
                step3.classList.remove('hidden');
                step3.classList.add('active');
            } else {
                createError.textContent = data.error || data.message || 'Erro desconhecido.';
                createError.classList.remove('hidden');
            }
        } catch (err) {
            createError.textContent = 'A criação demorou demais ou houve um erro no servidor.';
            createError.classList.remove('hidden');
        } finally {
            setLoading(btnCreate, false);
        }
    });

    // Reiniciar fluxo
    document.getElementById('btn-restart').addEventListener('click', () => {
        searchForm.reset();
        createForm.reset();
        customLocalGroup.classList.add('hidden');
        currentEmpData = {};

        step3.classList.remove('active');
        step3.classList.add('hidden');
        step1.classList.remove('hidden');
        step1.classList.add('active');
    });
});
