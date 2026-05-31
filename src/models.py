from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessoData:
    justica_federal: bool
    fase_inquerito: bool
    dias_em_inquerito: int
    dias_desde_ultima_revisao: int
    envolve_lei_de_drogas: bool
    caso_complexo: bool
    crime_doloso: bool
    admissivel_inc_i: bool
    admissivel_inc_ii: bool
    admissivel_inc_iii: bool
    duvida_identidade_civil: bool
    medidas_cautelares_diversas_insuficientes: bool
    indicios_autoria: bool
    prova_materialidade: bool
    risco_ordem_publica: bool
    risco_ordem_economica: bool
    risco_instrucao_criminal: bool
    instrucao_encerrada: bool
    risco_aplicacao_lei_penal: bool
    fundamentacao_generica: bool
    fatos_novos_ou_contemporaneos: bool
    crime_permanente: bool
    conduta_recente_demonstrada: bool
    juizo_foi_intimado_apos_90_dias: bool
