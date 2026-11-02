# RPA Automation Lab — Docker

Projeto de aprendizado: **Flask + SQLite local + Gemini + Playwright**, com painel ADM e histórico de conversas compartilhado entre CLI e web. ERP demonstrativo, controle de estoque, cadastro/atualização de pedidos, chat com IA e automação pela interface gráfica (sem API de gravação). **Não utilizar dados reais.**

## Requisitos
- Ubuntu com Docker Engine e Docker Compose plugin funcionando (`sudo docker compose version`)
- Git para baixar atualizações
- Internet para construir a imagem e chamar o Gemini

**Não é necessário** usar `.venv`, instalar Python ou instalar dependências com `sudo pip`. O `sudo` serve apenas para chamar o Docker se seu usuário ainda não tiver permissão no daemon. Não use `chmod 777` ou instale pacotes Python globalmente.

## Atualizar o computador e iniciar — Ubuntu

Primeiro, pare servidores locais antigos iniciados com `python -m erp.app` e outras CLIs antigas. Em seu terminal, sem `.venv`:

```bash
cd ~/Projetos/RPA-Automation-Lab
deactivate 2>/dev/null || true
git status --short
git pull --ff-only
```

Se houver conflito por alterações locais, preserve seus arquivos e resolva o conflito antes de continuar. O pull não substitui o arquivo `.env` ignorado pelo Git.

Configure `.env` (somente uma vez):

```bash
cp -n .env.example .env
nano .env
```

Exemplo (use sua chave real **apenas no .env local**, nunca no GitHub):

```dotenv
GEMINI_API_KEY=COLOQUE_SUA_CHAVE_AQUI
GEMINI_MODEL=gemini-3.5-flash-lite
```

**Inicie e recrie tudo pelo Docker**, inclusive uma imagem limpa:

```bash
sudo bash scripts/docker-up.sh
```

O script preserva os dados: se existir `erp.sqlite3` na raiz do projeto e ainda não existir `storage/erp.sqlite3`, copia o banco antigo. O novo banco é persistido em `./storage/erp.sqlite3`, no host. A migração do ERP adiciona a coluna `cep` sem apagar pedidos antigos. Os arquivos de `.env`, `storage`, `reports` e `screenshots` não entram na imagem.

Abra **http://127.0.0.1:5000/** (ou **http://127.0.0.1:5000/adm**) para o painel ADM, **http://127.0.0.1:5000/pedidos/lista** para pedidos, **http://127.0.0.1:5000/produtos** para produtos, **http://127.0.0.1:5000/pedidos/gerenciar** para cadastro manual, **http://127.0.0.1:5000/estoque** para estoque manual e **http://127.0.0.1:5000/controle** para o chat ADM.

## CLI interativa pelo Docker

```bash
sudo docker compose exec -it erp python -m rpa.cli
```

Exemplos: `bom dia`; `o que é RPA?`; `quero cadastrar um pedido`; `consulte o estoque do SKU M-01`. A CLI permite retomar conversas anteriores armazenadas no mesmo SQLite do chat do site. A interface web permite criar, abrir e excluir históricos. As conversas gerais não devem exigir SKU. Ao reconhecer uma operação ERP, a IA apresenta os campos obrigatórios e opcionais; gravações requerem `SIM` para confirmar. Use `/sair` para encerrar e `/limpar` para limpar o contexto da sessão.

O Playwright roda com **Chromium headless** dentro do contêiner, sem abrir uma janela gráfica no Ubuntu; ele ainda interage com a interface web do ERP. Isso é intencional e dispensa configurar X11, DISPLAY ou servidores gráficos no host. Para executar o robô CSV:

```bash
sudo docker compose exec -T erp python -m rpa.robot
```

## Diagnóstico completo

```bash
sudo bash scripts/docker-check.sh
```

Valida os arquivos Python carregados **dentro do contêiner**, uma saudação que não depende do Gemini, a migração da coluna CEP e os testes `pytest`. Para consultar modelos disponíveis para sua chave:

```bash
sudo docker compose exec -T erp python -m rpa.diagnostico
```

Esse diagnóstico não publica a chave; disponibilidade de modelos ainda depende da API Google. Para ver logs:

```bash
sudo docker compose logs --tail=100 erp
```

## Banco local e persistência

- Banco SQLite: `storage/erp.sqlite3` (arquivo local, persistido entre recriações)
- Relatórios: `reports/`
- Capturas de falha: `screenshots/`
- Segredos: `.env` (não versionado)
- Código: é copiado para a imagem no momento do build. **Qualquer atualização exige nova construção** com `sudo bash scripts/docker-up.sh`.
- Só o endereço `127.0.0.1:5000` é publicado na máquina anfitriã; não há autenticação no ERP.

Não rode `sudo docker compose down -v` para apagar volumes de propósito, nem exclua `storage/erp.sqlite3` se quiser manter os dados. `sudo docker compose down` para os serviços sem apagar a pasta `storage`.

## Arquitetura

`erp/app.py`: Flask e SQLite; `rpa/interpreter.py`: interpretação do Gemini; `rpa/commands.py`: validação de operações; `rpa/interactive.py`: interação com navegador Playwright; `rpa/cli.py`: conversa interativa e confirmação; `rpa/robot.py`: execução CSV/XLSX; `tests/`: testes automatizados.

No novo pedido, `pedido_id`, cliente, produto, quantidade e valor unitário são obrigatórios. Status (padrão `pendente`) e CEP são opcionais; quando omitido, CEP fica `NULL`. Pode-se atualizar o CEP ou limpá-lo posteriormente. O ERP é um laboratório local, sem autenticação; o chat web permite enviar operações validadas ao Playwright após confirmação explícita.

## Estado dos testes

Testes unitários e de integração Flask podem ser executados via `docker-check.sh`; não há garantia de teste ponta a ponta no ambiente do usuário nem de disponibilidade da API Gemini. Falhas HTTP 429/503 no Gemini não são resolvidas pelo Docker por si só.


## Painel ADM experimental, permissões e histórico
O banco persiste as tabelas `chat_conversations`, `chat_messages` e `rpa_audit`. O chat do navegador e a CLI compartilham o mesmo histórico, mas não usam credenciais de administradores (não existem usuários nem login nesta demonstração). O site permite ver o painel, pedidos, produtos, cadastrar manualmente e conversar com o Gemini. No chat web, ações de RPA completas podem ser revisadas e executadas sem repetir comandos no terminal. O robô utiliza Playwright no Chromium headless e os formulários reais do ERP.

Operações reconhecidas: `criar_pedido`, `atualizar_pedido`, `excluir_pedido`, `criar_produto`, `atualizar_produto`, `excluir_produto`, `definir_estoque`, `consultar_estoque`, `listar_pedidos`, `listar_produtos`, `resumo_erp`. Ações de leitura usam consultas limitadas e aprovadas ao SQLite; alterações e exclusões utilizam Playwright. **Nenhuma execução de SQL arbitrário ou exclusão em massa foi concedida à IA.**

**Limite importante:** permissão para executar ações administrativas não significa permissão para inventar dados. O cadastro de pedido ainda precisa de cliente, produto, quantidade e preço; o ID técnico é gerado automaticamente se omitido, enquanto status e CEP são opcionais; o sistema pode aproveitar dados fornecidos em linguagem natural e pedir apenas os que faltam. Gravações precisam de confirmação `SIM` na CLI, ou confirmação explícita no navegador. Ações ficam registradas em `rpa_audit`, mas exclusões não contam com lixeira/undo.

⚠ **NÃO É SEGURO PARA PRODUÇÃO.** Sem autenticação, autorização por usuário, CSRF, segregação de dados, backups e auditoria antifraude, não exponha a porta na internet nem use dados reais. A interface inclui alerta propositalmente destacado. Para um ambiente real, implemente login, RBAC, confirmação de exclusões com reautenticação, transações e logs externos.

Após baixar novas alterações, execute `sudo bash scripts/docker-up.sh` para reconstruir a imagem Docker e reiniciar o ERP. Execute `sudo bash scripts/docker-check.sh` para validar os testes. A disponibilidade do Gemini depende da API Google, não do Docker.


## Resolução de pedidos por nome e confirmação visual própria

Exemplo: `exclua o pedido teste 10`, quando o cliente `teste 10` pertence ao pedido de ID `10`.

1. Gemini identifica a intenção e envia uma referência textual, sem presumir que ela é o ID.
2. O backend pesquisa em SQLite por ID e nome de cliente, priorizando coincidências exatas. Se houver várias correspondências, apresenta os pedidos para seleção manual.
3. O Chat ADM exibe uma **janela de confirmação do próprio sistema** (sem `window.confirm()`) mostrando o ID real, o cliente, o produto, o valor, a quantidade e o status.
4. O servidor confere novamente a identidade e os dados do pedido selecionado no SQLite antes de enviar o ID resolvido ao Playwright. Se houver mudança, rejeita e exige nova pesquisa.
5. O Playwright interage com o formulário real de exclusão e com o diálogo interno do ERP; confere em seguida que o registro desapareceu.

O mesmo tipo de confirmação interna substitui os alertas de exclusão dos formulários manuais. A CLI também consulta o banco e permite selecionar o pedido encontrado, mantendo a confirmação textual `SIM`.

**Limites:** consulta parcial (sem correspondência fonética/semântica avançada), até 20 resultados por busca, busca restrita aos primeiros 2.000 pedidos do laboratório. A exclusão não ocorre se o pedido não for encontrado. Não há exclusão em massa. Consultas e confirmação são realizadas sobre dados reais; o Gemini não deve inventar registros encontrados.

Após atualizar com `git pull --ff-only origin main`, recrie o Docker usando `sudo bash scripts/docker-up.sh`, rode `sudo bash scripts/docker-check.sh` e atualize o navegador com `Ctrl+Shift+R`.


## Upgrade de interface administrativa (Dark Neon)

A URL raiz `http://127.0.0.1:5000/` agora redireciona para o **Dashboard ADM**. Todos os módulos renderizam o template reutilizável `erp/templates/base.html` e o tema compartilhado `erp/static/admin.css` (preto grafite, ciano, violeta, toques neon). A navegação é vertical à esquerda, com perfil ADM demonstrativo, topbar, status local e relógio.

**Navegação:** Dashboard `/adm` · Pedidos `/pedidos/lista` · Produtos `/produtos` · Estoque `/estoque` · Chat ADM `/controle` · Auditoria `/auditoria` · Configurações `/configuracoes` · Gerenciar pedidos manualmente `/pedidos/gerenciar`.

**Dashboard conectado ao SQLite:** total de pedidos, valor bruto (quantidade × preço), produtos, estoque baixo (≤5), pedidos pendentes e concluídos, conversas salvas, ações manuais, execuções e falhas RPA; últimos pedidos, monitor de estoque, atividades recentes e atalhos rápidos. O filtro de texto nas listagens de pedidos/produtos funciona no navegador.

**Rastreabilidade:** `erp/metrics.py` cria automaticamente a tabela `activity_log` no SQLite existente e registra cadastros, alterações e exclusões manuais concluídos. As execuções do RPA aparecem por meio da tabela preexistente `rpa_audit`, separadas da atividade manual. Os registros são armazenados em UTC e apresentados no horário de Brasília (`America/Sao_Paulo`), com origem, status e detalhes. As atividades anteriores à implementação da auditoria manual não podem ser reconstruídas retroativamente. Não existe identidade real de operador: `ADM (manual)` e `RPA (assistido)` são rótulos de origem, não contas autenticadas.

**Compatibilidade do robô:** o Playwright para pedidos foi atualizado para o caminho `/pedidos/gerenciar` e os campos do robô CSV/XLSX foram delimitados ao formulário correto; as rotas de gravação existentes continuam disponíveis. O SQLite e o histórico de conversas continuam persistidos em `storage/erp.sqlite3`.

Para atualizar no Ubuntu, sem `.venv`:

```bash
cd ~/Projetos/RPA-Automation-Lab
git status --short
git pull --ff-only origin main
sudo bash scripts/docker-up.sh
sudo bash scripts/docker-check.sh
```

Se `git pull` acusar modificações locais, guarde-as antes de atualizar; não use `git reset --hard` nem apague `storage/erp.sqlite3`. Após reconstruir, atualize o navegador com `Ctrl+Shift+R`.

O sistema permanece **exclusivamente um laboratório**: sem autenticação ou perfis reais, sem proteções completas contra CSRF, e sem restauração automática após exclusões. Não use em produção.
