from src.models import ProcessoData
from typing import Tuple

def avaliar_prisao_preventiva(p: ProcessoData) -> Tuple[str, str, str]:
    # CAMADA 0 - Prazo do inquérito
    if p.fase_inquerito:
        if p.envolve_lei_de_drogas:
            limite = 30
            norma = "art. 51 da Lei 11.343/06"
        elif p.justica_federal:
            limite = 15
            norma = "art. 10 do CPP (Justiça Federal)"
        else:
            limite = 10
            norma = "art. 10 do CPP (Justiça Estadual)"
        if p.dias_em_inquerito > limite:
            if p.caso_complexo:
                return ("ALERTA", f"Excesso de prazo no inquérito ({p.dias_em_inquerito} dias; limite: {limite} dias - {norma}). Complexidade atenua mas não legitima a inércia estatal. Recomenda-se pedido de relaxamento.", norma)
            else:
                return ("ILEGAL", f"Excesso de prazo no inquérito policial. Réu preso há {p.dias_em_inquerito} dias. Limite de {limite} dias pelo {norma}. Constrangimento ilegal configurado.", norma)

    # CAMADA 1 - Admissibilidade art. 313
    inc_i_valido = p.admissivel_inc_i and p.crime_doloso
    inc_ii_valido = p.admissivel_inc_ii and p.crime_doloso
    admissivel = inc_i_valido or inc_ii_valido or p.admissivel_inc_iii or p.duvida_identidade_civil
    if not admissivel:
        if p.admissivel_inc_i and not p.crime_doloso:
            motivo = "Crime culposo nao admite preventiva pelo art. 313, I (exige dolo)."
        else:
            motivo = "Nenhum pressuposto do art. 313 presente."
        return ("ILEGAL", motivo, "Art. 313, I, II, III e §1o CPP")

    # CAMADA 2 - Subsidiariedade art. 282, §6º
    if not p.medidas_cautelares_diversas_insuficientes:
        return ("ILEGAL", "Nao demonstrada insuficiencia das medidas cautelares diversas da prisão (art. 319). Violação do art. 282, §6º.", "Art. 282, §6º CPP")

    # CAMADA 3 - Fumus
    if not p.indicios_autoria or not p.prova_materialidade:
        faltam = []
        if not p.indicios_autoria:
            faltam.append("indicios de autoria")
        if not p.prova_materialidade:
            faltam.append("prova da materialidade")
        return ("ILEGAL", f"Fumus commissi delicti ausente: faltam {', '.join(faltam)}.", "Art. 312, caput, CPP")

    # CAMADA 4 - Periculum
    risco_instrucao_valido = p.risco_instrucao_criminal and not p.instrucao_encerrada
    algum_periculum = p.risco_ordem_publica or p.risco_ordem_economica or risco_instrucao_valido or p.risco_aplicacao_lei_penal
    if not algum_periculum:
        if p.risco_instrucao_criminal and p.instrucao_encerrada:
            return ("ILEGAL", "Risco à instrução caducou com o encerramento da instrução judicial. Nenhum outro risco demonstrado.", "Art. 312, caput, CPP")
        return ("ILEGAL", "Nenhuma das quatro hipóteses de periculum libertatis demonstrada.", "Art. 312, caput, CPP")

    # CAMADA 5 - Forma da decisão
    if p.fundamentacao_generica:
        return ("ILEGAL", "Fundamentação genérica ou inidônea. Nulidade absoluta (art. 315, §2º).", "Art. 315, §2º CPP")

    # CAMADA 6 - Contemporaneidade
    if not p.fatos_novos_ou_contemporaneos:
        return ("ILEGAL", "Fatos pretéritos sem demonstração de risco atual. Violação do art. 312, §2º.", "Art. 312, §2º CPP")
    if p.crime_permanente and not p.conduta_recente_demonstrada:
        return ("ILEGAL", "Crime permanente não justifica prisão sem prova de conduta recente.", "Art. 312, §2º e jurisprudência STF")

    # CAMADA 7 - Revisão periódica
    if p.dias_desde_ultima_revisao > 90:
        if not p.juizo_foi_intimado_apos_90_dias:
            return ("ALERTA", f"Revisão obrigatória vencida ({p.dias_desde_ultima_revisao} dias). Provocar juízo imediatamente.", "Art. 316, parágrafo único, CPP; ADIs 6581/6582")
        else:
            return ("ILEGAL", f"Juízo inerte mesmo após intimação ({p.dias_desde_ultima_revisao} dias). Prisão arbitrária.", "Art. 316, parágrafo único, CPP")

    return ("LEGAL", "Prisão preventiva dentro dos parâmetros legais e constitucionais.", "Arts. 312, 313, 315, 316 e 282, §6º CPP")
