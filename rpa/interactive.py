import os
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
URL = os.getenv("ERP_URL", "http://127.0.0.1:5000").rstrip("/")

def run_command(command, headless=False):
    action, data = command["action"], command["data"]
    if not command.get("ready"):
        raise ValueError("Comando incompleto.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(extra_http_headers={"X-RPA-Origin": "1"})
        try:
            route = "/estoque" if action not in ("criar_pedido", "atualizar_pedido", "excluir_pedido") else "/"
            page.goto(URL + route, wait_until="domcontentloaded", timeout=15000)
            if action == "criar_pedido":
                if any(r.get_attribute("data-pedido-id") == data["pedido_id"] for r in page.locator("tr[data-pedido-id]").all()):
                    return "Pedido já existente; nenhuma alteração."
                for key in ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario"):
                    page.locator('form[action="/pedidos"] [name="' + key + '"]').fill(data[key])
                page.locator('form[action="/pedidos"] [name="status"]').select_option(data["status"])
                if data.get("cep"):
                    page.locator('form[action="/pedidos"] [name="cep"]').fill(data["cep"])
                page.get_by_role("button", name="Salvar pedido").click()
                rows = [r for r in page.locator("tr[data-pedido-id]").all() if r.get_attribute("data-pedido-id") == data["pedido_id"]]
                if len(rows) != 1:
                    raise RuntimeError("Pedido não confirmado na interface.")
                cells = rows[0].locator("td").all_text_contents()
                if cells[1] != data["cliente"] or cells[2] != data["produto"] or cells[3] != data["quantidade"] or cells[5] != data["status"]:
                    raise RuntimeError("Dados divergentes.")
                if cells[6] != (data.get("cep") or "—"):
                    raise RuntimeError("CEP divergente.")
                return "Pedido cadastrado e conferido."
            if action == "atualizar_pedido":
                form = page.locator('form[action="/pedidos/atualizar"]')
                form.locator('[name="pedido_id"]').fill(data["pedido_id"])
                for key, value in data.items():
                    if key == "pedido_id":
                        continue
                    if key == "cep" and value == "":
                        form.locator('[name="limpar_cep"]').check()
                    else:
                        form.locator('[name="' + key + '"]').fill(value)
                form.get_by_role("button", name="Atualizar").click()
                rows = [r for r in page.locator("tr[data-pedido-id]").all() if r.get_attribute("data-pedido-id") == data["pedido_id"]]
                if not rows:
                    raise RuntimeError("Pedido não encontrado para atualização.")
                cells = rows[0].locator("td").all_text_contents()
                positions = {"cliente":1,"produto":2,"quantidade":3,"valor_unitario":4,"status":5,"cep":6}
                for key, value in data.items():
                    if key == "pedido_id":
                        continue
                    expected = "—" if key == "cep" and not value else value
                    if cells[positions[key]] != expected:
                        raise RuntimeError("Campo atualizado divergente: " + key)
                return "Pedido atualizado e conferido."
            if action == "excluir_pedido":
                rows=[r for r in page.locator("tr[data-pedido-id]").all() if r.get_attribute("data-pedido-id")==data["pedido_id"]]
                if len(rows)!=1:
                    raise ValueError("Pedido não encontrado; nada foi excluído.")
                form=page.locator('form[action="/pedidos/excluir"]')
                form.locator('[name="pedido_id"]').fill(data["pedido_id"])
                form.get_by_role("button", name="Excluir pedido").click()
                page.locator("#erp-confirm").wait_for(state="visible")
                page.locator("#erp-confirm-accept").click()
                if any(r.get_attribute("data-pedido-id")==data["pedido_id"] for r in page.locator("tr[data-pedido-id]").all()):
                    raise RuntimeError("Exclusão não confirmada na interface.")
                return "Pedido excluído e conferido: "+data["pedido_id"]
            if action == "excluir_produto":
                rows=[r for r in page.locator("tr[data-sku]").all() if r.get_attribute("data-sku")==data["sku"]]
                if len(rows)!=1:
                    raise ValueError("Produto não encontrado; nada foi excluído.")
                form=page.locator('form[action="/estoque/excluir"]')
                form.locator('[name="sku"]').fill(data["sku"])
                form.get_by_role("button", name="Excluir produto").click()
                page.locator("#erp-confirm").wait_for(state="visible")
                page.locator("#erp-confirm-accept").click()
                if any(r.get_attribute("data-sku")==data["sku"] for r in page.locator("tr[data-sku]").all()):
                    raise RuntimeError("Exclusão não confirmada na interface.")
                return "Produto excluído e conferido: "+data["sku"]
            if action == "atualizar_produto":
                form=page.locator('form[action="/estoque/editar"]')
                form.locator('[name="sku"]').fill(data["sku"])
                for key,value in data.items():
                    if key!="sku":
                        form.locator('[name="'+key+'"]').fill(value)
                form.get_by_role("button", name="Atualizar produto").click()
                rows=[r for r in page.locator("tr[data-sku]").all() if r.get_attribute("data-sku")==data["sku"]]
                if len(rows)!=1:
                    raise ValueError("Produto não encontrado para atualização.")
                cells=rows[0].locator("td").all_text_contents()
                for key,pos in (("produto",1),("quantidade",2),("preco",3)):
                    if key in data and cells[pos]!=data[key]:
                        raise RuntimeError("Valor divergente na interface: "+key)
                return "Produto atualizado e conferido: "+data["sku"]
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
