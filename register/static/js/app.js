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

    // Lógica das Abas (Tabs)
    const tabBtns = document.querySelectorAll('.tab-btn');
    const flowContainers = document.querySelectorAll('.flow-container');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all tabs
            tabBtns.forEach(b => {
                b.classList.remove('active');
            });
            // Hide all flows
            flowContainers.forEach(flow => {
                flow.style.display = 'none';
            });

            // Set active class to clicked tab
            btn.classList.add('active');

            // Show selected flow
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).style.display = 'block';
        });
    });

    // Submissão do Formulário de Backup
    const backupForm = document.getElementById('backup-form');
    const btnBackup = document.getElementById('btn-backup');
    const backupMsg = document.getElementById('backup-msg');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    let pollingInterval = null;

    if (backupForm) {
        backupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Ocultar mensagem anterior
            backupMsg.classList.add('hidden');
            progressContainer.classList.add('hidden');
            backupMsg.textContent = '';
            backupMsg.style.backgroundColor = '';
            backupMsg.style.color = '';
            
            setLoading(btnBackup, true);

            const sourceEmail = document.getElementById('source_email').value.trim();
            const destEmail = document.getElementById('dest_email').value.trim();

            try {
                // 1. Iniciar Backup do OneDrive
                const res = await fetch('/api/backup_onedrive', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_email: sourceEmail, dest_email: destEmail })
                });
                const data = await res.json();
                
                let onedriveSuccess = data.success;

                backupMsg.classList.remove('hidden');
                if (onedriveSuccess) {
                    backupMsg.textContent = data.message || "Backup do OneDrive iniciado!";
                    backupMsg.style.backgroundColor = "rgba(78, 173, 64, 0.2)";
                    backupMsg.style.color = "#4EAD40";
                    backupForm.reset();
                    
                    if (data.monitor_urls && data.monitor_urls.length > 0) {
                        startProgressPolling(data.monitor_urls);
                    }
                } else {
                    backupMsg.textContent = data.message || data.error || "Erro ao iniciar o backup do OneDrive.";
                    backupMsg.style.backgroundColor = "rgba(231, 76, 60, 0.2)";
                    backupMsg.style.color = "#E74C3C";
                }
            } catch (err) {
                backupMsg.classList.remove('hidden');
                backupMsg.textContent = 'Erro de comunicação com o servidor.';
                backupMsg.style.backgroundColor = "rgba(231, 76, 60, 0.2)";
                backupMsg.style.color = "#E74C3C";
            } finally {
                setLoading(btnBackup, false);
            }
        });
    }

    function startProgressPolling(monitorUrls) {
        progressContainer.classList.remove('hidden');
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        
        if (pollingInterval) clearInterval(pollingInterval);
        
        let maxPct = 0; // Garante que a barra nunca volte para trás
        
        const checkStatus = async () => {
            try {
                const res = await fetch('/api/backup_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ monitor_urls: monitorUrls })
                });
                const data = await res.json();
                
                if (data.success) {
                    const pct = Math.floor(data.percentage);
                    
                    if (pct > maxPct) {
                        maxPct = pct;
                    }
                    
                    progressBar.style.width = `${maxPct}%`;
                    progressText.textContent = `${maxPct}%`;
                    
                    if (maxPct >= 100) {
                        clearInterval(pollingInterval);
                        backupMsg.textContent = "Backup Concluído 100%!";
                        document.getElementById('post-backup-actions').classList.remove('hidden');
                    }
                }
            } catch (err) {
                console.error("Erro ao checar progresso:", err);
            }
        };

        // Começa a checar depois de 1 segundo (primeira batida rápida)
        setTimeout(checkStatus, 1000);
        
        // Depois continua checando a cada 1.5 segundos
        pollingInterval = setInterval(checkStatus, 1500);
    }

    // Ações Pós-Backup (Remover Licença)
    const btnRemoveYes = document.getElementById('btn-remove-license-yes');
    const btnRemoveNo = document.getElementById('btn-remove-license-no');
    const licenseMsg = document.getElementById('license-msg');

    if (btnRemoveYes && btnRemoveNo) {
        btnRemoveYes.addEventListener('click', async () => {
            licenseMsg.classList.add('hidden');
            const sourceEmail = document.getElementById('source_email') ? document.getElementById('source_email').value.trim() : "";
            btnRemoveYes.textContent = 'Removendo...';
            btnRemoveYes.disabled = true;
            btnRemoveNo.disabled = true;

            try {
                const res = await fetch('/api/remove_license', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_email: sourceEmail })
                });
                const data = await res.json();
                
                licenseMsg.classList.remove('hidden');
                if (data.success) {
                    licenseMsg.textContent = data.message || 'Licença removida com sucesso!';
                    licenseMsg.style.color = '#4EAD40';
                    btnRemoveYes.style.display = 'none';
                    btnRemoveNo.style.display = 'none';
                } else {
                    licenseMsg.textContent = data.message || data.error || 'Erro ao remover licença.';
                    licenseMsg.style.color = '#E74C3C';
                    btnRemoveYes.textContent = 'Tentar Novamente';
                    btnRemoveYes.disabled = false;
                    btnRemoveNo.disabled = false;
                }
            } catch (err) {
                licenseMsg.classList.remove('hidden');
                licenseMsg.textContent = 'Erro de comunicação com o servidor.';
                licenseMsg.style.color = '#E74C3C';
                btnRemoveYes.textContent = 'Tentar Novamente';
                btnRemoveYes.disabled = false;
                btnRemoveNo.disabled = false;
            }
        });

        btnRemoveNo.addEventListener('click', () => {
            document.getElementById('post-backup-actions').classList.add('hidden');
            backupForm.reset();
        });
    }

    // Formulário do Outlook
    const outlookForm = document.getElementById('outlook-form');
    const btnOutlook = document.getElementById('btn-outlook');
    const outlookMsg = document.getElementById('outlook-msg');
    const outlookProgContainer = document.getElementById('outlook-progress-container');
    const outlookProgBar = document.getElementById('outlook-progress-bar');
    const outlookProgText = document.getElementById('outlook-progress-text');

    if (outlookForm) {
        outlookForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            outlookMsg.classList.add('hidden');
            outlookProgContainer.classList.add('hidden');
            outlookMsg.textContent = '';
            
            setLoading(btnOutlook, true);

            const sourceEmail = document.getElementById('source-email-out').value.trim();
            const destEmail = document.getElementById('dest-email-out').value.trim();

            outlookMsg.classList.remove('hidden');
            outlookMsg.textContent = "Baixando e-mails do Outlook, por favor aguarde (pode demorar vários minutos)...";
            outlookMsg.style.color = "var(--text-main)";
            outlookMsg.style.backgroundColor = "transparent";
            
            // Simular progresso enquanto a chamada síncrona roda no backend
            outlookProgContainer.classList.remove('hidden');
            let pct = 0;
            outlookProgBar.style.width = '0%';
            outlookProgText.textContent = '0%';
            const progressInterval = setInterval(() => {
                if (pct < 95) {
                    pct += Math.floor(Math.random() * 3) + 1;
                    if (pct > 95) pct = 95;
                    outlookProgBar.style.width = pct + '%';
                    outlookProgText.textContent = pct + '%';
                }
            }, 1000);

            try {
                const resOut = await fetch('/api/backup_outlook', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_email: sourceEmail, dest_email: destEmail })
                });
                const dataOut = await resOut.json();
                
                clearInterval(progressInterval);
                
                if (dataOut.success) {
                    outlookProgBar.style.width = '100%';
                    outlookProgText.textContent = '100%';
                    outlookMsg.style.backgroundColor = "rgba(78, 173, 64, 0.2)";
                    outlookMsg.style.color = "#4EAD40";
                    outlookMsg.textContent = dataOut.message;
                    outlookForm.reset();
                } else {
                    outlookProgContainer.classList.add('hidden');
                    outlookMsg.style.backgroundColor = "rgba(231, 76, 60, 0.2)";
                    outlookMsg.style.color = "#E74C3C";
                    outlookMsg.textContent = dataOut.message || "Erro no backup do Outlook";
                }
            } catch (errOut) {
                clearInterval(progressInterval);
                outlookProgContainer.classList.add('hidden');
                outlookMsg.style.backgroundColor = "rgba(231, 76, 60, 0.2)";
                outlookMsg.style.color = "#E74C3C";
                outlookMsg.textContent = "Falha de rede ao realizar backup do Outlook.";
            } finally {
                setLoading(btnOutlook, false);
            }
        });
    }

    // Formulário de Assinatura Avulsa
    const signatureForm = document.getElementById('signature-form');
    const btnSignature = document.getElementById('btn-signature');
    const signatureMsg = document.getElementById('signature-msg');
    const signatureResult = document.getElementById('signature-result');
    const signatureImage = document.getElementById('signature-image');
    const btnDownloadSignature = document.getElementById('btn-download-signature');
    
    const sigLocalSelect = document.getElementById('sig-local');
    const sigCustomLocalGroup = document.getElementById('sig-custom-local-group');
    const sigCustomLocalInput = document.getElementById('sig-custom-local');

    if (sigLocalSelect) {
        sigLocalSelect.addEventListener('change', (e) => {
            if (e.target.value === 'Outro') {
                sigCustomLocalGroup.classList.remove('hidden');
                sigCustomLocalInput.setAttribute('required', 'true');
            } else {
                sigCustomLocalGroup.classList.add('hidden');
                sigCustomLocalInput.removeAttribute('required');
            }
        });
    }

    if (signatureForm) {
        signatureForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            signatureMsg.classList.add('hidden');
            signatureResult.classList.add('hidden');
            
            setLoading(btnSignature, true);

            let sigLocal = sigLocalSelect.value;
            if (sigLocal === 'Outro') {
                sigLocal = sigCustomLocalInput.value.trim();
            }

            const payload = {
                full_name: document.getElementById('sig-name').value.trim(),
                cargo: document.getElementById('sig-cargo').value.trim(),
                filial: '9',
                local: sigLocal,
                telefone: document.getElementById('sig-telefone').value.trim(),
                ramal: document.getElementById('sig-ramal').value.trim(),
                email_manual: document.getElementById('sig-email').value.trim()
            };

            try {
                const res = await fetch('/api/generate_signature', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (data.success) {
                    // Adiciona um cache buster pra imagem sempre recarregar se gerar duas com o mesmo nome
                    signatureImage.src = data.signature_url + "?v=" + new Date().getTime();
                    btnDownloadSignature.href = data.signature_url;
                    signatureResult.classList.remove('hidden');
                    signatureForm.reset();
                    sigCustomLocalGroup.classList.add('hidden');
                } else {
                    signatureMsg.classList.remove('hidden');
                    signatureMsg.style.backgroundColor = "rgba(231, 76, 60, 0.2)";
                    signatureMsg.style.color = "#E74C3C";
                    signatureMsg.textContent = data.message || data.error || "Erro ao gerar a assinatura.";
                }
            } catch (err) {
                signatureMsg.classList.remove('hidden');
                signatureMsg.style.backgroundColor = "rgba(231, 76, 60, 0.2)";
                signatureMsg.style.color = "#E74C3C";
                signatureMsg.textContent = "Falha de rede ao se comunicar com o servidor.";
            } finally {
                setLoading(btnSignature, false);
            }
        });
    }
});
