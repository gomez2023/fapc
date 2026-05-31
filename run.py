from src.database import init_log_database, registrar_log_sqlite
from src.cli import coletar_dados_cli, obter_bool
from src.auditoria import avaliar_prisao_preventiva
from src.pdf_generator import gerar_pdf_documento
from datetime import datetime

def main():
    try:
        from src.pdf_generator import REPORTLAB_OK
    except ImportError:
        REPORTLAB_OK = False
    if not REPORTLAB_OK:
        print("reportlab nao instalado. PDFs nao serao gerados.")
    init_log_database()
    while True:
        nome_reu, num_processo, processo = coletar_dados_cli()
        status, motivo, fundamento = avaliar_prisao_preventiva(processo)
        print(f"\nSTATUS: {status}")
        print(f"MOTIVO: {motivo}")
        print(f"BASE LEGAL: {fundamento}")
        registrar_log_sqlite({
            "data_hora": datetime.now().isoformat(),
            "nome_reu": nome_reu,
            "numero_processo": num_processo,
            "status": status,
            "motivo": motivo,
            "fundamento_legal": fundamento,
        })
        if status == "ILEGAL":
            print("\nCabivel: habeas corpus ou pedido de relaxamento.")
            gerar_pdf_documento(nome_reu, num_processo, motivo, fundamento, tipo="ILEGAL", justica_federal=processo.justica_federal)
        elif status == "ALERTA":
            print("\nProvidencia urgente – provocar o juizo.")
            gerar_pdf_documento(nome_reu, num_processo, motivo, fundamento, tipo="ALERTA", justica_federal=processo.justica_federal)
        else:
            print("\nPrisao regular. Monitore revisao periodica.")
        if not obter_bool("\nAnalisar outro processo?"):
            break

if __name__ == "__main__":
    main()
