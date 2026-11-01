# RPA Automation Lab

Automação empresarial com **Python, Playwright e ERP demonstrativo local**. O robô cadastra pedidos pela interface gráfica, sem API de escrita.

## Status
Etapas 1–4 implementadas em código; execução ponta a ponta depende de validação no ambiente com navegador. Testes unitários configurados para GitHub Actions. Etapa 5 (IA/MCP) não implementada.

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

## Roadmap
- [x] Estrutura e dependências
- [x] ERP local
- [x] Robô de cadastro via navegador
- [x] Validação, prevenção de duplicados, relatórios, logs e testes unitários
- [ ] Teste E2E validado no Ubuntu e Windows
- [ ] Agente IA / MCP (futuro)
