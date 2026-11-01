# RPA Automation Lab

Automação empresarial com **Python, Playwright e ERP demonstrativo local**. O robô cadastra pedidos pela interface gráfica, sem API de escrita.

## Status
ERP, automação de pedidos, estoque e interpretação por Gemini implementados. MCP ainda não implementado. Teste ponta a ponta depende de execução local com Chromium e disponibilidade da API Gemini.

## Componentes
- `erp/app.py`: Flask + SQLite, formulário e listagem de pedidos.
- `erp/templates/index.html`: interface escura com verde suave.
- `rpa/robot.py`: leitura CSV/XLSX, validação, Playwright visível, verificação, duplicados, relatório e screenshots.
- `data/pedidos_exemplo.csv`: três pedidos fictícios.
- `tests/`: testes unitários; `.github/workflows/tests.yml`: CI.

## Ubuntu
```bash
git clone https://github.com/phzl0/RPA-Automation-Lab.git
cd RPA-Automation-Lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m pytest -q
```
Se necessário: `sudo apt install python3-venv` e `python -m playwright install --with-deps chromium`.

**Terminal 1 — ERP:**
```bash
python -m erp.app
```
Acesse http://127.0.0.1:5000.

**Terminal 2 — robô (com ambiente virtual ativado):**
```bash
python -m rpa.robot
```
O Chromium abre visivelmente. Veja os pedidos no ERP e o relatório em `reports/`. Execute novamente para verificar a detecção de duplicados. Use `--headless` para execução sem janela, e `--file caminho.xlsx` para Excel.

## Windows (PowerShell)
```powershell
git clone https://github.com/phzl0/RPA-Automation-Lab.git
cd RPA-Automation-Lab
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest -q
```
Em dois terminais distintos, execute `.\.venv\Scripts\python.exe -m erp.app` e `.\.venv\Scripts\python.exe -m rpa.robot`.

## Confiabilidade e limites
A chave única `pedido_id` no SQLite impede duplicações. O robô confere os dados pela tabela HTML e gera `reports/resultado_*.csv`; falhas geram capturas em `screenshots/`. O ERP é uma demonstração **sem autenticação** e deve permanecer acessível somente em `127.0.0.1`; nunca use dados reais. Não há mecanismo de recuperação automática após falhas complexas, nem testes E2E em CI nesta versão.


## Gemini + estoque + controle (versão experimental)
As telas estão em:
- http://127.0.0.1:5000/ — pedidos
- http://127.0.0.1:5000/estoque — cadastro, consulta e definição de quantidade absoluta
- http://127.0.0.1:5000/controle — interpretação por Gemini, sem execução direta (por segurança)

Após atualizar o repositório, execute `python -m pip install -r requirements.txt`.

Configure a chave local em `.env` (não envie ao GitHub):
```bash
cp -n .env.example .env
nano .env
```
Defina `GEMINI_API_KEY` e `GEMINI_MODEL=gemini-3.5-flash-lite` no arquivo. O projeto carrega `.env` automaticamente via `python-dotenv`. O arquivo `.env.example` é apenas um modelo e não deve conter uma chave real.

Para conferir a versão local, use `git pull --ff-only` e `grep -n 'Consultando Gemini' rpa/cli.py`. Diagnóstico seguro (não exibe a chave): `python -m rpa.diagnostico`. O comando lista modelos informados pela API para a chave configurada. Um modelo listado não garante capacidade disponível naquele instante. O interpretador faz até duas tentativas para erros HTTP temporários e informa falhas sem executar o RPA.

Inicie o ERP com `python -m erp.app`. Em outro terminal:
```bash
python -m rpa.cli
```
Exemplo: `Cadastre o mouse SKU M-01, com 20 unidades a R$ 49,90`. O Gemini interpreta; Python valida; se faltar algum campo a CLI pergunta; você deve digitar exatamente `SIM` para o robô executar. Para consulta: `Consulte o estoque do SKU M-01`. Para ajuste absoluto: `Defina o estoque do SKU M-01 para 30 unidades`.

**Limitações importantes:** Não há memória conversacional entre comandos, nem incremento/decremento relativo de estoque; "adicionar mais 10" precisa de esclarecimento. A interface de chat interpreta e valida, mas a execução confirmada é feita pela CLI. O LLM depende da internet, da disponibilidade do Gemini e dos limites/custos de sua conta. Nunca coloque a chave no GitHub. O ERP não tem autenticação; use apenas localmente e com dados fictícios.

**Testes:** `python -m pytest -q` valida regras, rotas e respostas simuladas do interpretador; não exige chamadas reais ao Gemini. Testes completos com Chromium e Gemini ainda precisam ser executados em um ambiente configurado.

## Roadmap
- [x] Estrutura e dependências
- [x] ERP local
- [x] Robô de cadastro via navegador
- [x] Validação, prevenção de duplicados, relatórios, logs e testes unitários
- [ ] Teste E2E validado no Ubuntu e Windows
- [x] Interpretador Gemini e controle via CLI (experimental)
- [ ] Agente com MCP (futuro)


## Chat conversacional e CEP opcional
O modelo padrão é `gemini-3.5-flash-lite`. **Atualize também o arquivo local `.env`**:
```dotenv
GEMINI_MODEL=gemini-3.5-flash-lite
```
A CLI `python -m rpa.cli` agora aceita perguntas gerais, mantém contexto recente durante a sessão e permite `/limpar` e `/sair`. Quando detectar uma operação ERP, pede campos obrigatórios e informa os opcionais; só executa gravações após confirmação `SIM`. Consultas de estoque não alteram dados.

Pedidos novos exigem ID, cliente, produto, quantidade e valor unitário. Status (padrão pendente) e CEP são opcionais. CEP omitido é armazenado como `NULL`. A migração SQLite adiciona a coluna `cep` aos bancos existentes automaticamente ao iniciar o ERP. É possível atualizar um pedido existente pelo formulário `/pedidos/atualizar` ou via CLI; o comando `limpe o CEP do pedido P1` define `NULL`. Não há consulta automática de CEP nos Correios.

Para testar:
```bash
git pull --ff-only
python -m pip install -r requirements.txt
python -m pytest -q
python -m erp.app
# outro terminal, no mesmo diretório com venv ativo:
python -m rpa.cli
```
Se o ERP já estiver rodando, reinicie-o após o pull para aplicar a migração.
