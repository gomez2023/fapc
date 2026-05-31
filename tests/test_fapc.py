import pytest
from src.auditoria import avaliar_prisao_preventiva
from src.models import ProcessoData

def base_processo(**kwargs):
    defaults = {
        "justica_federal": False,
        "fase_inquerito": True,
        "dias_em_inquerito": 5,
        "dias_desde_ultima_revisao": 30,
        "envolve_lei_de_drogas": False,
        "caso_complexo": False,
        "crime_doloso": True,
        "admissivel_inc_i": True,
        "admissivel_inc_ii": False,
        "admissivel_inc_iii": False,
        "duvida_identidade_civil": False,
        "medidas_cautelares_diversas_insuficientes": True,
        "indicios_autoria": True,
        "prova_materialidade": True,
        "risco_ordem_publica": True,
        "risco_ordem_economica": False,
        "risco_instrucao_criminal": False,
        "instrucao_encerrada": False,
        "risco_aplicacao_lei_penal": False,
        "fundamentacao_generica": False,
        "fatos_novos_ou_contemporaneos": True,
        "crime_permanente": False,
        "conduta_recente_demonstrada": False,
        "juizo_foi_intimado_apos_90_dias": False,
    }
    defaults.update(kwargs)
    return ProcessoData(**defaults)

def test_processo_completamente_legal():
    status, _, _ = avaliar_prisao_preventiva(base_processo())
    assert status == "LEGAL"

def test_estadual_no_limite_legal():
    assert avaliar_prisao_preventiva(base_processo(dias_em_inquerito=10))[0] == "LEGAL"

def test_estadual_um_dia_alem_ilegal():
    status, motivo, _ = avaliar_prisao_preventiva(base_processo(dias_em_inquerito=11))
    assert status == "ILEGAL"
    assert "10 dias" in motivo

def test_federal_no_limite_legal():
    assert avaliar_prisao_preventiva(base_processo(justica_federal=True, dias_em_inquerito=15))[0] == "LEGAL"

def test_federal_um_dia_alem_ilegal():
    status, motivo, _ = avaliar_prisao_preventiva(base_processo(justica_federal=True, dias_em_inquerito=16))
    assert status == "ILEGAL"
    assert "15 dias" in motivo

def test_lei_drogas_no_limite_legal():
    assert avaliar_prisao_preventiva(base_processo(envolve_lei_de_drogas=True, dias_em_inquerito=30))[0] == "LEGAL"

def test_lei_drogas_um_dia_alem_ilegal():
    status, motivo, _ = avaliar_prisao_preventiva(base_processo(envolve_lei_de_drogas=True, dias_em_inquerito=31))
    assert status == "ILEGAL"

def test_caso_complexo_excesso_gera_alerta():
    status, motivo, _ = avaliar_prisao_preventiva(base_processo(dias_em_inquerito=20, caso_complexo=True))
    assert status == "ALERTA"

def test_crime_culposo_pena_alta_ilegal():
    p = base_processo(crime_doloso=False, admissivel_inc_i=True, admissivel_inc_ii=False, admissivel_inc_iii=False, duvida_identidade_civil=False)
    status, motivo, _ = avaliar_prisao_preventiva(p)
    assert status == "ILEGAL"
    assert "culposo" in motivo.lower()

def test_risco_instrucao_instrucao_encerrada_ilegal():
    p = base_processo(risco_instrucao_criminal=True, instrucao_encerrada=True, risco_ordem_publica=False)
    assert avaliar_prisao_preventiva(p)[0] == "ILEGAL"

def test_91_dias_sem_intimacao_alerta():
    p = base_processo(dias_desde_ultima_revisao=91, juizo_foi_intimado_apos_90_dias=False)
    status, motivo, _ = avaliar_prisao_preventiva(p)
    assert status == "ALERTA"

def test_91_dias_com_intimacao_inerte_ilegal():
    p = base_processo(dias_desde_ultima_revisao=91, juizo_foi_intimado_apos_90_dias=True)
    status, motivo, _ = avaliar_prisao_preventiva(p)
    assert status == "ILEGAL"
