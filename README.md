# RPA Automation Lab — Beta

> **Projeto em fase beta.** ERP administrativo demonstrativo com RPA, chat com IA e histórico persistente. Desenvolvido para estudar automação de processos empresariais, interpretação de linguagem natural, Playwright e integração de sistemas. **Utilize somente dados fictícios.**

Aplicação local com **Python/Flask**, **SQLite**, **Playwright/Chromium**, **Gemini** e **Docker Compose**. Inclui dashboard ADM, pedidos, produtos, estoque, chat web/CLI, auditoria e execução assistida de tarefas administrativas.

## Comece aqui: executar no seu computador

**O projeto já está preparado para rodar integralmente pelo Docker.** Não é necessário instalar Python, Flask, Playwright ou Chromium no computador; a imagem é construída localmente a partir do `Dockerfile`. O `compose.yaml` inicia o ERP e mantém os dados no próprio computador.

Você precisa de **Git, Docker e Docker Compose**, acesso à internet na instalação e uma chave pessoal do Gemini para usar os recursos de IA. **O ERP e os formulários manuais podem ser usados sem uma chave funcional; o chat com Gemini não.**

| Requisito | Finalidade |
| --- | --- |
| Git | Clonar e atualizar o código |
| Docker Engine + Compose (Linux) / Docker Desktop (Windows) | Construir e executar o ambiente |
| Chave Gemini | Interpretar mensagens no chat web e na CLI |
| Porta local `5000` disponível | Abrir o ERP no navegador |

A API Gemini é um serviço externo: disponibilidade, cotas e eventuais custos dependem da conta Google. Cada pessoa usa sua própria chave. O projeto não fornece créditos de API.

### Linux / Ubuntu

**1. Instale os requisitos.** Se ainda não tiver Docker, siga a [documentação oficial do Docker para Ubuntu](https://docs.docker.com/engine/install/ubuntu/), incluindo o plugin Docker Compose.

Confira:

```bash
git --version
sudo docker --version
sudo docker compose version
```

**2. Clone o projeto.** Se a pasta já existir, **não clone novamente**; siga a seção de atualização mais abaixo.

```bash
mkdir -p ~/Projetos
cd ~/Projetos
git clone https://github.com/phzl0/RPA-Automation-Lab.git
cd RPA-Automation-Lab
```

**3. Configure sua chave Gemini** (somente na primeira instalação):

```bash
cp -n .env.example .env
nano .env
```

Preencha no `.env`:

```dotenv
GEMINI_API_KEY=cole_sua_chave_aqui
GEMINI_MODEL=gemini-3.5-flash-lite
```

Substitua a chave de exemplo pela sua. No Nano, salve com `Ctrl+O`, `Enter` e saia com `Ctrl+X`. **Nunca envie o `.env` ao GitHub** nem compartilhe a chave.

**4. Construa e inicie pelo Docker:**

```bash
sudo bash scripts/docker-up.sh
```

O script valida o Compose, cria as pastas persistentes, copia o antigo `erp.sqlite3` para `storage/` se necessário e ainda não houver banco nesse local, **reconstrói a imagem sem cache** e inicia o ERP. A primeira execução baixa as dependências e o navegador Chromium.

**5. Confira se iniciou:**

```bash
sudo docker compose ps
sudo docker compose logs --tail=50 erp
```

Abra **[http://127.0.0.1:5000](http://127.0.0.1:5000)**. A página inicial é o Dashboard ADM. Você **não precisa abrir um terminal para iniciar o Flask**; o contêiner faz isso automaticamente.

### Windows — PowerShell

**1. Instale** [Git para Windows](https://git-scm.com/downloads/win) e [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) com o mecanismo de **contêineres Linux** habilitado (WSL 2, quando aplicável).

Abra o Docker Desktop e aguarde o mecanismo iniciar. Depois, em um novo PowerShell:

```powershell
git --version
docker --version
docker compose version
```

**2. Baixe o código:**

```powershell
git clone https://github.com/phzl0/RPA-Automation-Lab.git
cd RPA-Automation-Lab
```

**3. Crie seu `.env` local e abra para edição:**

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha `GEMINI_API_KEY` e mantenha um `GEMINI_MODEL` válido para a sua conta. Não publique a chave.

**4. Construa e inicie os serviços:** no Windows use **Docker Compose diretamente**, sem `sudo` e sem executar scripts Bash:

```powershell
New-Item -ItemType Directory -Force storage, reports, screenshots | Out-Null
docker compose up --build -d
docker compose ps
docker compose logs --tail=50 erp
```

Se estiver migrando uma instalação antiga, copie seu `erp.sqlite3` para `storage/erp.sqlite3` **antes** de iniciar, desde que não exista banco no destino. Nunca sobrescreva um banco já em uso.

**5. Abra [http://127.0.0.1:5000](http://127.0.0.1:5000).** Mantenha o Docker Desktop iniciado durante o uso.

## Telas disponíveis

| Módulo | Endereço | O que faz |
| --- | --- | --- |
| Dashboard | [localhost:5000](http://127.0.0.1:5000/) | KPIs, pedidos recentes, alertas de estoque, atividades |
| Pedidos | [localhost:5000/pedidos/lista](http://127.0.0.1:5000/pedidos/lista) | Consultar e filtrar pedidos |
| Gerenciar pedidos | [localhost:5000/pedidos/gerenciar](http://127.0.0.1:5000/pedidos/gerenciar) | Cadastrar, editar e excluir manualmente |
| Produtos | [localhost:5000/produtos](http://127.0.0.1:5000/produtos) | Consultar e filtrar produtos |
| Estoque | [localhost:5000/estoque](http://127.0.0.1:5000/estoque) | Cadastrar produtos, alterar quantidades, editar e excluir |
| Chat ADM | [localhost:5000/controle](http://127.0.0.1:5000/controle) | Conversar com IA, pesquisar registros e aprovar ações RPA |
| Auditoria | [localhost:5000/auditoria](http://127.0.0.1:5000/auditoria) | Consultar alterações, origem, status e horários |
| Configurações | [localhost:5000/configuracoes](http://127.0.0.1:5000/configuracoes) | Visualizar informações do ambiente local |

O layout administrativo usa sidebar vertical, perfil ADM **demonstrativo**, tema escuro com detalhes neon e componentes compartilhados.

## Como testar o RPA e a IA

O **chat web** está em `/controle`. Ele mantém conversas no SQLite, interpreta solicitações pelo Gemini, exibe resultados encontrados no banco e solicita aprovação antes de executar alterações.

Exemplos de mensagens:

- `Bom dia`
- `Mostre os pedidos cadastrados`
- `Quantos produtos estão no estoque?`
- `Cadastre um pedido para Ana, 2 mouses de R$ 50 cada`
- `Exclua o pedido do cliente teste 10`

Na exclusão por nome, o sistema pesquisa os pedidos, mostra os registros encontrados e pede que você selecione e confirme o ID correto. Não faz exclusão em massa. O robô utiliza o **Playwright no Chromium headless**, preenchendo formulários do ERP mesmo sem abrir uma janela gráfica no computador.

### Chat pelo terminal (CLI)

No **Linux/Ubuntu**, abra outro terminal na pasta do repositório:

```bash
sudo docker compose exec -it erp python -m rpa.cli
```

No **Windows/PowerShell**:

```powershell
docker compose exec erp python -m rpa.cli
```

O CLI oferece acesso a conversas persistidas anteriormente, `/nova` para criar outra sessão, `/historico` para ver mensagens e `/sair` para encerrar. Alterações pedem a confirmação `SIM`; consultas não precisam de confirmação de gravação.

### Automação por CSV/XLSX

Um arquivo de exemplo está em `data/pedidos_exemplo.csv`. Execute:

**Linux:**

```bash
sudo docker compose exec -T erp python -m rpa.robot
```

**Windows:**

```powershell
docker compose exec -T erp python -m rpa.robot
```

Os resultados ficam em `reports/`. Capturas de falhas ficam em `screenshots/`. O robô verifica duplicidades e confere registros na interface.

## Atualizar uma instalação existente

**Antes de atualizar:** salve alterações locais de código. O arquivo `.env` e o banco SQLite são ignorados pelo Git e não devem ser apagados.

### Linux

```bash
cd ~/Projetos/RPA-Automation-Lab
git status --short
git pull --ff-only origin main
sudo bash scripts/docker-up.sh
sudo bash scripts/docker-check.sh
```

### Windows — PowerShell

```powershell
cd RPA-Automation-Lab
git status --short
git pull --ff-only origin main
docker compose up --build -d --force-recreate
docker compose exec -T erp python -m pytest -q
```

Se o Git mostrar `Your local changes would be overwritten`, **não use `git reset --hard`**. Preserve suas modificações antes de repetir o pull. Em caso de erro na porta, confirme se outra aplicação está usando `5000`. Após a atualização, recarregue o navegador com `Ctrl+Shift+R`.

**Importante:** o script Ubuntu usa `--no-cache` para forçar uma compilação limpa. É mais demorado, mas evita reutilizar camadas antigas durante a fase beta. Para desenvolvimento normal, `docker compose up --build -d` costuma ser mais rápido.

## Verificações e solução de problemas

### Linux

```bash
sudo bash scripts/docker-check.sh
sudo docker compose ps
sudo docker compose logs --tail=100 erp
```

### Windows

```powershell
docker compose ps
docker compose exec -T erp python -m pytest -q
docker compose logs --tail=100 erp
```

O diagnóstico testa a inicialização, os arquivos Python, o banco, a coluna CEP, rotas do painel, métricas e testes automatizados. Ele **não garante** uma chamada real bem-sucedida ao Gemini nem a execução ponta a ponta em cada máquina.

Para consultar a disponibilidade de modelos do Gemini no Linux:

```bash
sudo docker compose exec -T erp python -m rpa.diagnostico
```

Se a IA retornar erros HTTP 401/403, verifique a chave/permissões; 404 pode indicar modelo indisponível; 429 ou 503 podem refletir limites ou indisponibilidade temporária do Google. Não publique a chave ao pedir suporte.

### Parar e reiniciar

**Linux:**

```bash
sudo docker compose stop
sudo docker compose start
```

**Windows:**

```powershell
docker compose stop
docker compose start
```

Para remover os contêineres sem excluir os diretórios persistidos, use `docker compose down` (com `sudo` no Linux, se necessário). Não apague `storage/erp.sqlite3` se quiser preservar pedidos, produtos, conversas e histórico.

## Como o projeto funciona

```text
Administrador
    ├── Navegador: Dashboard / Pedidos / Produtos / Chat ADM
    └── CLI: conversa e comandos administrativos
                 |
                 v
          Gemini (interpretação)
                 |
                 v
      Python: validação e consultas
                 |
           Confirmação humana
                 |
                 v
        Playwright / Chromium
                 |
                 v
        Formulários do ERP Flask
                 |
                 v
         SQLite persistido
```

A **IA interpreta a intenção**, o **Python consulta e valida os dados reais**, e o **RPA executa ações na interface**. Não é necessário MCP para esse fluxo. O Chat ADM não permite SQL arbitrário nem exclusão em massa.

| Arquivo / pasta | Responsabilidade |
| --- | --- |
| `Dockerfile` e `compose.yaml` | Imagem, serviço local, persistência e porta |
| `erp/app.py` | Rotas do ERP e formulários manuais |
| `erp/adm_routes.py` | Rotas do painel ADM e chat |
| `erp/metrics.py` | Indicadores e atividades |
| `erp/order_lookup.py` | Busca de pedidos por ID/cliente |
| `erp/chat_store.py` | Histórico persistente de conversas |
| `erp/templates/` e `erp/static/` | Interface dark/neon |
| `rpa/interpreter.py` | Interpretação de solicitações por Gemini |
| `rpa/commands.py` | Validação dos comandos |
| `rpa/interactive.py` | Operações Playwright na interface |
| `rpa/cli.py` | Chat administrativo no terminal |
| `rpa/robot.py` | Importação e automação CSV/XLSX |
| `tests/` | Testes automatizados |

## Banco, dados locais e segurança

O arquivo `storage/erp.sqlite3` armazena pedidos, produtos, conversas e eventos. `reports/` e `screenshots/` guardam os resultados locais da automação. A chave da API fica em `.env`, fora do repositório.

A interface apresenta o perfil `ADM`, mas **ainda não existe login nem controle de permissões por usuário**. Na auditoria, `ADM (manual)` e `RPA (assistido)` indicam o canal, **não a identidade autenticada de uma pessoa**. Novas atividades são registradas com horários; eventos manuais anteriores à implantação do log não podem ser reconstruídos.

**Este projeto é um laboratório, não um ERP de produção.** Não utilize dados reais, não exponha a porta à internet e não trate confirmações visuais como substitutas de autenticação, autorização, proteção contra CSRF, backups e recuperação de exclusões.

## Status do projeto

- [x] Docker Compose e banco local persistente
- [x] Painel ADM dark/neon com dashboard e módulos
- [x] CRUD manual de pedidos e produtos
- [x] Chat web + CLI com histórico no SQLite
- [x] Interpretação pelo Gemini e execução via Playwright
- [x] Busca de pedidos por nome/ID e confirmação visual
- [x] Auditoria de operações recentes
- [x] Testes automatizados no repositório
- [ ] Validação E2E completa em Linux/Windows com Gemini real
- [ ] Login, perfis e autorizações
- [ ] Backups/restauração automatizados e segurança para produção

---

**Licença de uso e contribuições:** consulte os arquivos de licença e configuração do repositório. Este projeto permanece experimental.
