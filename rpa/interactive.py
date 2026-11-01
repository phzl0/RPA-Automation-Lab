import os
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = os.getenv("ERP_URL", "http://127.0.0.1:5000").rstrip("/")

def run_command(command, headless=False):
    action, data = command["action"], command["data"]
    if not command.get("ready"):
        raise ValueError("Comando incompleto.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            route = "/estoque" if action != "criar_pedido" else "/"
            page.goto(URL + route, wait_until="domcontentloaded", timeout=15000)
            if action == "criar_pedido":
                if any(r.get_attribute("data-pedido-id") == data["pedido_id"] for r in page.locator("tr[data-pedido-id]").all()):
                    return "Pedido já existente; nenhuma alteração."
                for key in ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario"):
                    page.locator('form[action="/pedidos"] [name="' + key + '"]').fill(data[key])
                page.locator('form[action="/pedidos"] [name="status"]').select_option(data["status"])
                page.get_by_role("button", name="Salvar pedido").click()
                rows = [r for r in page.locator("tr[data-pedido-id]").all() if r.get_attribute("data-pedido-id") == data["pedido_id"]]
                if len(rows) != 1:
                    raise RuntimeError("Pedido não confirmado na interface.")
                cells = rows[0].locator("td").all_text_contents()
                if cells[1] != data["cliente"] or cells[2] != data["produto"] or cells[3] != data["quantidade"] or cells[5] != data["status"]:
                    raise RuntimeError("Dados divergentes.")
                return "Pedido cadastrado e conferido."
            rows = [r for r in page.locator("tr[data-sku]").all() if r.get_attribute("data-sku") == data["sku"]]
            if action == "consultar_estoque":
                if not rows:
                    return "SKU não encontrado."
                return " | ".join(rows[0].locator("td").all_text_contents())
            if action == "criar_produto":
                if rows:
                    return "SKU já existente; nenhuma alteração."
                form = page.locator('form[action="/estoque"]')
                for key in ("sku", "produto", "quantidade", "preco"):
                    form.locator('[name="' + key + '"]').fill(data[key])
                form.get_by_role("button", name="Cadastrar produto").click()
            elif action == "definir_estoque":
                if not rows:
                    raise ValueError("SKU não encontrado; nenhuma alteração.")
                form = page.locator('form[action="/estoque/atualizar"]')
                form.locator('[name="sku"]').fill(data["sku"])
                form.locator('[name="quantidade"]').fill(data["quantidade"])
                form.get_by_role("button", name="Atualizar estoque").click()
            rows = [r for r in page.locator("tr[data-sku]").all() if r.get_attribute("data-sku") == data["sku"]]
            if len(rows) != 1:
                raise RuntimeError("Produto não confirmado na interface.")
            cells = rows[0].locator("td").all_text_contents()
            if cells[2] != data["quantidade"]:
                raise RuntimeError("Quantidade divergente na conferência.")
            if action == "criar_produto" and (cells[1] != data["produto"] or cells[3] != data["preco"]):
                raise RuntimeError("Dados divergentes na conferência.")
            return "Estoque conferido: " + " | ".join(cells)
        except Exception:
            shots = ROOT / "screenshots"
            shots.mkdir(exist_ok=True)
            page.screenshot(path=str(shots / ("comando_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png")))
            raise
        finally:
            browser.close()
