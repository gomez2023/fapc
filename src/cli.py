from datetime import datetime, date
from src.models import ProcessoData
from typing import Tuple

def validar_data_input(pergunta: str) -> date:
    while True:
        s = input(f"{pergunta} (DD/MM/AAAA): ").strip()
        try:
            d = datetime.strptime(s, "%d/%m/%Y").date()
            if d > date.today():
                print("Data futura não permitida.")
                continue
            return d
        except ValueError:
            print("Formato inválido. Use DD/MM/AAAA.")

def obter_bool(pergunta: str) -> bool:
    while True:
        r = input(f"{pergunta} (S/N): ").strip().upper()
        if r in ("S", "N"):
            return r == "S"
        print("Responda S ou N.")

def coletar_dados_cli() -> Tuple[str, str, ProcessoData]:
    print("\n=== AUDITORIA DE PRISÃO PREVENTIVA v4.1 (base: Aury Lopes Jr.) ===\n")
    nome_reu = input("Nome completo do réu: ").strip() or "NÃO IDENTIFICADO"
    num_processo = input("Número do processo/inquérito: ").strip() or "NÃO INFORMADO"

    data_prisao = validar_data_input("Data da prisão")
    data_revisao = validar_data_input("Data da última revisão judicial")
    dias_preso = (date.today() - data_prisao).days
    dias_revisao = (date.today() - data_revisao).days

    fase_inquerito = obter_bool("Está em fase de inquérito policial?")
    instrucao_encerrada = obter_bool("A instrução criminal judicial já foi encerrada (último ato instrutório)?") if not fase_inquerito else False
    envolve_drogas = obter_bool("Envolve Lei de Drogas (Lei 11.343/06)?")
    caso_complexo = obter_bool("O caso é complexo (muitos réus, cooperação internacional etc.)?") if fase_inquerito else False

    print("\n--- Natureza do crime ---")
    crime_doloso = obter_bool("O crime imputado é DOLOSO?")

    print("\n--- Admissibilidade art. 313 ---")
    admissivel_i = obter_bool("[Inc. I] Pena máxima do crime supera 4 anos? (Só será válido se o crime for doloso)")
    admissivel_ii = obter_bool("[Inc. II] Réu é reincidente em crime doloso? (Requer crime doloso anterior E atual)")
    admissivel_iii = obter_bool("[Inc. III] Crime envolve violência doméstica ou familiar? (Autônomo)")
    duvida_id = obter_bool("[§1º] Há dúvida fundada sobre a identidade civil do indiciado? (Autônomo)")

    print("\n--- Proporcionalidade e subsidiariedade (art. 282, §6º) ---")
    subsidiariedade = obter_bool("A decisão demonstrou concretamente a insuficiência das medidas cautelares diversas da prisão (tornozeleira, proibição de contato etc.)?")

    print("\n--- Fumus commissi delicti (art. 312) ---")
    indicios_autoria = obter_bool("Há indícios concretos de autoria?")
    prova_material = obter_bool("Há prova concreta da materialidade?")

    print("\n--- Periculum libertatis ---")
    risco_op = obter_bool("  [Ordem pública] Risco concreto e atual de reiteração criminosa ou abalo à ordem?")
    risco_oe = obter_bool("  [Ordem econômica] Risco concreto ao sistema financeiro ou à ordem econômica?")
    risco_ic = obter_bool("  [Instrução criminal] Risco concreto de destruição de provas, ameaça a testemunhas ou peritos?")
    risco_lp = obter_bool("  [Aplicação da lei penal] Risco concreto de fuga? (Indícios objetivos)")

    print("\n--- Forma da decisão (art. 315) ---")
    fund_gen = obter_bool("A fundamentação é genérica, abstrata, copia peças ou reitera decisão anterior sem novos elementos?")

    print("\n--- Contemporaneidade (art. 312, §2º) ---")
    fatos_ok = obter_bool("Os fatos que motivam a prisão são atuais e contemporâneos?")
    crime_perm = obter_bool("Trata-se de crime permanente?")
    conduta_recente = obter_bool("  Há prova de conduta criminosa recente (últimos dias) do réu?") if crime_perm else False

    intimado_90 = False
    if dias_revisao > 90:
        print(f"\nJá se passaram {dias_revisao} dias desde a última revisão judicial.")
        intimado_90 = obter_bool("[Art. 316] O juízo foi formalmente intimado/provocado a revisar a prisão?")

    processo = ProcessoData(
        justica_federal=obter_bool("\nO caso é da Justiça Federal?"),
        fase_inquerito=fase_inquerito,
        dias_em_inquerito=dias_preso,
        dias_desde_ultima_revisao=dias_revisao,
        envolve_lei_de_drogas=envolve_drogas,
        caso_complexo=caso_complexo,
        crime_doloso=crime_doloso,
        admissivel_inc_i=admissivel_i,
        admissivel_inc_ii=admissivel_ii,
        admissivel_inc_iii=admissivel_iii,
        duvida_identidade_civil=duvida_id,
        medidas_cautelares_diversas_insuficientes=subsidiariedade,
        indicios_autoria=indicios_autoria,
        prova_materialidade=prova_material,
        risco_ordem_publica=risco_op,
        risco_ordem_economica=risco_oe,
        risco_instrucao_criminal=risco_ic,
        instrucao_encerrada=instrucao_encerrada,
        risco_aplicacao_lei_penal=risco_lp,
        fundamentacao_generica=fund_gen,
        fatos_novos_ou_contemporaneos=fatos_ok,
        crime_permanente=crime_perm,
        conduta_recente_demonstrada=conduta_recente,
        juizo_foi_intimado_apos_90_dias=intimado_90,
    )
    return nome_reu, num_processo, processo
