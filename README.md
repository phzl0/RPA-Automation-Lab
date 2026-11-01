# RPA Automation Lab — Docker

Projeto de aprendizado: **Flask + SQLite local + Gemini + Playwright**. ERP demonstrativo, controle de estoque, cadastro/atualização de pedidos, chat com IA e automação pela interface gráfica (sem API de gravação). **Não utilizar dados reais.**

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

Abra **http://127.0.0.1:5000** para o ERP, **http://127.0.0.1:5000/estoque** para o estoque e **http://127.0.0.1:5000/controle** para o chat.

## CLI interativa pelo Docker

```bash
sudo docker compose exec -it erp python -m rpa.cli
```

Exemplos: `bom dia`; `o que é RPA?`; `quero cadastrar um pedido`; `consulte o estoque do SKU M-01`. As conversas gerais não devem exigir SKU. Ao reconhecer uma operação ERP, a IA apresenta os campos obrigatórios e opcionais; gravações requerem `SIM` para confirmar. Use `/sair` para encerrar e `/limpar` para limpar o contexto da sessão.

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

No novo pedido, `pedido_id`, cliente, produto, quantidade e valor unitário são obrigatórios. Status (padrão `pendente`) e CEP são opcionais; quando omitido, CEP fica `NULL`. Pode-se atualizar o CEP ou limpá-lo posteriormente. O ERP é um laboratório local, sem autenticação, e **o chat web não executa alterações diretamente**.

## Estado dos testes

Testes unitários e de integração Flask podem ser executados via `docker-check.sh`; não há garantia de teste ponta a ponta no ambiente do usuário nem de disponibilidade da API Gemini. Falhas HTTP 429/503 no Gemini não são resolvidas pelo Docker por si só.
