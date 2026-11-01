# RPA Automation Lab

> Laboratório de automação robótica de processos empresariais com Python e Playwright.

**Status:** Etapa 1 — estrutura inicial. O ERP e o robô ainda não foram implementados ou testados.

## Objetivo
Ler pedidos fictícios de CSV/Excel, abrir um ERP local no navegador, cadastrar e conferir os registros pela interface e gerar relatórios de execução. O robô **não utilizará API para realizar cadastros**.

## Tecnologias
- **Python 3.11+** — execução e validação de dados.
- **Playwright** — automação visual do navegador.
- **Flask** — aplicação web local para simular o ERP.
- **openpyxl** — leitura de planilhas Excel.
- **pytest** — testes automatizados.

## Estrutura
```text
RPA-Automation-Lab/
├── data/pedidos_exemplo.csv   # três pedidos fictícios
├── erp/                       # ERP local (etapa 2)
├── rpa/                       # robô Playwright (etapa 3)
├── tests/                     # testes (etapa 4)
├── reports/                   # relatórios gerados
├── screenshots/               # evidências de falhas
├── requirements.txt
├── .env.example
└── .gitignore
```

## Preparação no Ubuntu
```bash
git clone https://github.com/phzl0/RPA-Automation-Lab.git
cd RPA-Automation-Lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```
Se faltar suporte a venv: `sudo apt install python3-venv`. Em distribuições Linux que precisem de bibliotecas do Chromium, consulte `python -m playwright install --with-deps chromium` (pode exigir sudo).

## Preparação no Windows (PowerShell)
```powershell
git clone https://github.com/phzl0/RPA-Automation-Lab.git
cd RPA-Automation-Lab
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```
Caso a política do PowerShell bloqueie a ativação, use diretamente `.\.venv\Scripts\python.exe` para executar os comandos Python.

## Verificação inicial
Após instalar as dependências:
```bash
python -c "import flask, playwright, openpyxl, pytest; print('Dependencias OK')"
```
Este comando verifica apenas a importação das bibliotecas. **Ainda não executa o ERP nem o RPA.**

## Dados de exemplo
`data/pedidos_exemplo.csv` contém três pedidos fictícios, com identificador, cliente, produto, quantidade, valor unitário e status. Valores usam ponto decimal.

## Roadmap
- [x] Estrutura, dependências e dados de exemplo
- [ ] ERP demonstrativo com cadastro e consulta de pedidos
- [ ] Robô Playwright visível, leitura de CSV/Excel e conferência na interface
- [ ] Validação, idempotência, logs, capturas, relatórios e testes
- [ ] Integração opcional com agente de IA e MCP

## Segurança
Utilize somente dados fictícios. Não faça commit de arquivos `.env`, credenciais ou relatórios contendo dados sensíveis. A aplicação local deverá usar o endereço `127.0.0.1` por padrão.

## Licença
Ainda não definida.
