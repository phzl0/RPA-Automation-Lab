import argparse
import csv
import logging
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario", "status")
STATUSES = {"pendente", "processando", "concluido"}

def load_orders(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    if path.suffix.lower() == ".xlsx":
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        try:
            rows = wb.active.iter_rows(values_only=True)
            header = [str(x).strip() if x is not None else "" for x in next(rows)]
            return [dict(zip(header, ("" if x is None else str(x) for x in row))) for row in rows]
        finally:
            wb.close()
    raise ValueError("Use arquivos .csv ou .xlsx")

def validate(row):
    data = {k: str(row.get(k, "")).strip() for k in FIELDS}
    if any(not data[k] for k in FIELDS):
        raise ValueError("Campos obrigatórios ausentes")
    try:
        quantity = int(data["quantidade"])
        value = Decimal(data["valor_unitario"])
    except (ValueError, InvalidOperation):
        raise ValueError("Quantidade ou valor inválido")
    if quantity <= 0 or not value.is_finite() or value < 0 or value > 100000000 or data["status"] not in STATUSES:
        raise ValueError("Quantidade, valor ou status inválido")
    data["quantidade"] = str(quantity)
    data["valor_unitario"] = format(value, ".2f")
    return data

def execute(source, url, headless=False):
    orders = load_orders(source)
    output = ROOT / "reports"
    output.mkdir(exist_ok=True)
    shots = ROOT / "screenshots"
    shots.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = output / f"resultado_{stamp}.csv"
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = []
    seen = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.get_by_role("heading", name="ERP Demonstrativo").wait_for()
            for index, row in enumerate(orders, 1):
                order_id = str(row.get("pedido_id", "")).strip()
                try:
                    data = validate(row)
                    if data["pedido_id"] in seen:
                        results.append((order_id, "duplicado", "Repetido no arquivo"))
                        continue
                    seen.add(data["pedido_id"])
                    selector = f'tr[data-pedido-id="{data["pedido_id"]}"]'
                    # Avoid selector injection: use attribute lookup through DOM locator filtering.
                    existing = page.locator("tr[data-pedido-id]").filter(has=page.locator("td", has_text=data["pedido_id"]))
                    if any(c.get_attribute("data-pedido-id") == data["pedido_id"] for c in existing.all()):
                        results.append((order_id, "duplicado", "Já existe no ERP"))
                        continue
                    for field in ("pedido_id", "cliente", "produto", "quantidade", "valor_unitario"):
                        page.locator(f'[name="{field}"]').fill(data[field])
                    page.locator('[name="status"]').select_option(data["status"])
                    page.get_by_role("button", name="Salvar pedido").click()
                    page.get_by_role("heading", name="ERP Demonstrativo").wait_for()
                    matching = [r for r in page.locator("tr[data-pedido-id]").all() if r.get_attribute("data-pedido-id") == order_id]
                    if len(matching) != 1:
                        raise RuntimeError("Pedido não encontrado após cadastro")
                    cells = matching[0].locator("td").all_text_contents()
                    if cells[1] != data["cliente"] or cells[2] != data["produto"] or cells[3] != data["quantidade"] or cells[5] != data["status"] or Decimal(cells[4]) != Decimal(data["valor_unitario"]):
                        raise RuntimeError("Dados divergentes na conferência")
                    results.append((order_id, "sucesso", "Conferido na interface"))
                except Exception as exc:
                    logging.exception("Falha no pedido %s", order_id)
                    try:
                        page.screenshot(path=str(shots / f"falha_{stamp}_{index}.png"))
                    except Exception:
                        pass
                    results.append((order_id, "erro", str(exc)[:300]))
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    except Exception:
                        pass
        finally:
            browser.close()
    with report.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("pedido_id", "resultado", "detalhes"))
        writer.writerows(results)
    print(f"Relatório: {report}")
    print(f"Sucessos: {sum(x[1]=='sucesso' for x in results)} | Duplicados: {sum(x[1]=='duplicado' for x in results)} | Erros: {sum(x[1]=='erro' for x in results)}")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(ROOT / "data" / "pedidos_exemplo.csv"))
    parser.add_argument("--url", default=os.getenv("ERP_URL", "http://127.0.0.1:5000"))
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    execute(args.file, args.url, args.headless or os.getenv("RPA_HEADLESS") == "1")
