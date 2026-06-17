Documentação de Requisitos: Automação de Criação de Usuários Microsoft 365

1. Objetivo da Automação
Automatizar o fluxo de provisionamento de novas contas de e-mail e usuários no painel de administração da Microsoft, padronizando a nomenclatura e atribuindo automaticamente as licenças necessárias.

2. Dados de Entrada (Input)
A automação ou script deverá ser acionado recebendo o seguinte parâmetro obrigatório:

    Nome Completo do Colaborador: (Exemplo: João Rocha Ferneto)

3. Regras de Negócio e Tratamento de Dados
A partir do input fornecido, o sistema deve aplicar a seguinte lógica para gerar as credenciais:

    Extração: Isolar o Primeiro Nome e o Último Nome do colaborador.

    Sanitização: Converter a string para letras minúsculas, removendo espaços extras, acentos e caracteres especiais (ex: João torna-se joao).

    Formatação das Credenciais:
        O sistema gera uma sugestão padrão, mas permite que o administrador digite um usuário personalizado (útil para homônimos, ex: joao.psilva).
        
        Padrão de Usuário Sugerido: [primeiro_nome].[ultimo_nome] (Exemplo: joao.ferneto)

        Domínio/E-mail: [usuario_escolhido]@ativalocacao.com.br

4. Ações a Serem Executadas no Sistema
A automação deverá interagir com a API ou painel de administração (Admin Center) para executar os seguintes passos em sequência:

    Iniciar a criação de um novo usuário.

    Preencher os campos de identificação (Nome e Sobrenome / Nome de Exibição).

    Definir o endereço de e-mail e nome de usuário conforme a regra de negócio detalhada no item 3.

    Atribuir ao novo usuário a licença exata: Microsoft 365 Business Basic (ou Microsoft 365 empresas Basic).

    Gerar a senha temporária (permitindo que o sistema crie uma automaticamente ou gerando uma senha forte padrão) e confirmar a criação.
    
    Gerar a Imagem da Assinatura e Aplicar na Caixa de Correio via script (aguarda até 15 minutos pelo provisionamento da caixa no Exchange).

5. Retorno Esperado (Output)
Após a conclusão com sucesso do fluxo, a automação deve obrigatoriamente devolver os dados de acesso para quem solicitou a criação, contendo:

    E-mail: endereço completo gerado.

    Senha: senha temporária atrelada à nova conta.

Exemplo de Execução Desejada:

    Input: João Rocha Ferneto
    Processamento interno: Cria usuário joao.ferneto@ativalocacao.com.br, aplica licença Microsoft 365 Business Basic.
    Output: > E-mail: joao.ferneto@ativalocacao.com.br
    Senha: [SenhaGeradaPeloSistema]