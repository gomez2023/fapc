# =============================================================================
# TESTES UNITÁRIOS — v4.1
# Novos testes para: crime_doloso (art. 313, I e II) e instrucao_encerrada
# Todos os 29 testes da v4.0 mantidos e atualizados para o novo dataclass.
# =============================================================================

import pytest
from fapc import avaliar_prisao_preventiva, ProcessoData


# ---------------------------------------------------------------------------
# FIXTURE BASE — processo completamente legal
# ---------------------------------------------------------------------------
def proc(**overrides) -> ProcessoData:
    defaults = dict(
        justica_federal=False,
        fase_inquerito=True,
        dias_em_inquerito=5,
        dias_desde_ultima_revisao=30,
        envolve_lei_de_drogas=False,
        caso_complexo=False,
        crime_doloso=True,               # novo v4.1-A
        admissivel_inc_i=True,
        admissivel_inc_ii=False,
        admissivel_inc_iii=False,
        duvida_identidade_civil=False,
        medidas_cautelares_diversas_insuficientes=True,
        indicios_autoria=True,
        prova_materialidade=True,
        risco_ordem_publica=True,
        risco_ordem_economica=False,
        risco_instrucao_criminal=False,
        instrucao_encerrada=False,       # novo v4.1-B
        risco_aplicacao_lei_penal=False,
        fundamentacao_generica=False,
        fatos_novos_ou_contemporaneos=True,
        crime_permanente=False,
        conduta_recente_demonstrada=False,
        juizo_foi_intimado_apos_90_dias=False,
    )
    defaults.update(overrides)
    return ProcessoData(**defaults)


# ---------------------------------------------------------------------------
# 1. CASO BASE
# ---------------------------------------------------------------------------
def test_processo_completamente_legal():
    status, _, _ = avaliar_prisao_preventiva(proc())
    assert status == "LEGAL"


# ---------------------------------------------------------------------------
# 2. PRAZO DO INQUÉRITO
# ---------------------------------------------------------------------------
class TestPrazoInquerito:

    def test_estadual_no_limite_legal(self):
        assert avaliar_prisao_preventiva(proc(dias_em_inquerito=10))[0] == "LEGAL"

    def test_estadual_um_dia_alem_ilegal(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(dias_em_inquerito=11))
        assert status == "ILEGAL"
        assert "10 dias" in motivo

    def test_federal_no_limite_legal(self):
        assert avaliar_prisao_preventiva(proc(justica_federal=True, dias_em_inquerito=15))[0] == "LEGAL"

    def test_federal_um_dia_alem_ilegal(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(justica_federal=True, dias_em_inquerito=16))
        assert status == "ILEGAL"
        assert "15 dias" in motivo

    def test_lei_drogas_no_limite_legal(self):
        assert avaliar_prisao_preventiva(proc(envolve_lei_de_drogas=True, dias_em_inquerito=30))[0] == "LEGAL"

    def test_lei_drogas_um_dia_alem_ilegal(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(envolve_lei_de_drogas=True, dias_em_inquerito=31))
        assert status == "ILEGAL"
        assert "51" in motivo and "11.343" in motivo

    def test_caso_complexo_excesso_gera_alerta(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(dias_em_inquerito=20, caso_complexo=True))
        assert status == "ALERTA"
        assert "complex" in motivo.lower()

    def test_caso_nao_complexo_excesso_gera_ilegal(self):
        assert avaliar_prisao_preventiva(proc(dias_em_inquerito=20))[0] == "ILEGAL"


# ---------------------------------------------------------------------------
# 3. ADMISSIBILIDADE ART. 313 — com crime_doloso (v4.1-A)
# ---------------------------------------------------------------------------
class TestAdmissibilidade313:

    def test_nenhum_inciso_ilegal(self):
        status, _, _ = avaliar_prisao_preventiva(proc(
            crime_doloso=False,
            admissivel_inc_i=False,
            admissivel_inc_ii=False,
            admissivel_inc_iii=False,
            duvida_identidade_civil=False,
        ))
        assert status == "ILEGAL"

    def test_crime_culposo_pena_alta_ilegal_inc_i(self):
        """
        v4.1-A: crime culposo com pena > 4 anos NÃO admite preventiva pelo inc. I.
        Exemplo clássico: homicídio culposo na direção (art. 302 CTB) — pena até 5 anos.
        """
        status, motivo, _ = avaliar_prisao_preventiva(proc(
            crime_doloso=False,     # culposo
            admissivel_inc_i=True,  # pena > 4 anos — mas irrelevante sem dolo
            admissivel_inc_ii=False,
            admissivel_inc_iii=False,
            duvida_identidade_civil=False,
        ))
        assert status == "ILEGAL"
        assert "culposo" in motivo.lower() or "doloso" in motivo.lower()

    def test_crime_culposo_com_vd_admissivel(self):
        """Inc. III (violência doméstica) é autônomo — independe de dolo."""
        status, _, _ = avaliar_prisao_preventiva(proc(
            crime_doloso=False,
            admissivel_inc_i=False,
            admissivel_inc_ii=False,
            admissivel_inc_iii=True,   # VD — autônomo
            duvida_identidade_civil=False,
        ))
        assert status == "LEGAL"

    def test_crime_culposo_com_duvida_identidade_admissivel(self):
        """§1º é autônomo — independe de dolo e de pena."""
        status, _, _ = avaliar_prisao_preventiva(proc(
            crime_doloso=False,
            admissivel_inc_i=False,
            admissivel_inc_ii=False,
            admissivel_inc_iii=False,
            duvida_identidade_civil=True,
        ))
        assert status == "LEGAL"

    def test_reincidente_doloso_admissivel(self):
        """Inc. II exige crime doloso — com crime_doloso=True deve funcionar."""
        status, _, _ = avaliar_prisao_preventiva(proc(
            crime_doloso=True,
            admissivel_inc_i=False,
            admissivel_inc_ii=True,
            admissivel_inc_iii=False,
            duvida_identidade_civil=False,
        ))
        assert status == "LEGAL"

    def test_reincidente_em_crime_culposo_inadmissivel(self):
        """Inc. II sem crime doloso atual = inadmissível."""
        status, _, _ = avaliar_prisao_preventiva(proc(
            crime_doloso=False,
            admissivel_inc_i=False,
            admissivel_inc_ii=True,    # reincidente, mas crime atual culposo
            admissivel_inc_iii=False,
            duvida_identidade_civil=False,
        ))
        assert status == "ILEGAL"


# ---------------------------------------------------------------------------
# 4. SUBSIDIARIEDADE
# ---------------------------------------------------------------------------
class TestSubsidiariedade:

    def test_sem_demonstrar_insuficiencia_ilegal(self):
        status, motivo, fundamento = avaliar_prisao_preventiva(
            proc(medidas_cautelares_diversas_insuficientes=False)
        )
        assert status == "ILEGAL"
        assert "282" in fundamento

    def test_com_demonstracao_prossegue(self):
        assert avaliar_prisao_preventiva(
            proc(medidas_cautelares_diversas_insuficientes=True)
        )[0] == "LEGAL"


# ---------------------------------------------------------------------------
# 5. FUMUS COMMISSI DELICTI
# ---------------------------------------------------------------------------
class TestFumus:

    def test_sem_indicios_autoria_ilegal(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(indicios_autoria=False))
        assert status == "ILEGAL"
        assert "autoria" in motivo.lower()

    def test_sem_prova_materialidade_ilegal(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(prova_materialidade=False))
        assert status == "ILEGAL"
        assert "materialidade" in motivo.lower()

    def test_sem_ambos_ilegal(self):
        assert avaliar_prisao_preventiva(
            proc(indicios_autoria=False, prova_materialidade=False)
        )[0] == "ILEGAL"


# ---------------------------------------------------------------------------
# 6. PERICULUM LIBERTATIS — com instrucao_encerrada (v4.1-B)
# ---------------------------------------------------------------------------
class TestPericulum:

    def test_nenhum_risco_ilegal(self):
        status, _, _ = avaliar_prisao_preventiva(proc(
            risco_ordem_publica=False,
            risco_ordem_economica=False,
            risco_instrucao_criminal=False,
            risco_aplicacao_lei_penal=False,
        ))
        assert status == "ILEGAL"

    def test_apenas_ordem_economica_suficiente(self):
        assert avaliar_prisao_preventiva(proc(
            risco_ordem_publica=False,
            risco_ordem_economica=True,
            risco_instrucao_criminal=False,
            risco_aplicacao_lei_penal=False,
        ))[0] == "LEGAL"

    def test_risco_instrucao_instrucao_em_curso_valido(self):
        """
        v4.1-B: inquérito encerrado (fase_inquerito=False) mas instrução
        judicial AINDA EM CURSO (instrucao_encerrada=False) → risco válido.
        Esse era o falso negativo da v4.0 (usava fase_inquerito como proxy).
        """
        status, _, _ = avaliar_prisao_preventiva(proc(
            fase_inquerito=False,        # IP encerrado
            instrucao_encerrada=False,   # instrução judicial em curso
            risco_ordem_publica=False,
            risco_instrucao_criminal=True,  # fundamento válido
            risco_aplicacao_lei_penal=False,
        ))
        assert status == "LEGAL"

    def test_risco_instrucao_pos_encerramento_sem_outros_ilegal(self):
        """
        v4.1-B: instrução encerrada E risco à instrução como único fundamento → ILEGAL.
        """
        status, motivo, _ = avaliar_prisao_preventiva(proc(
            fase_inquerito=False,
            instrucao_encerrada=True,      # instrução encerrada
            risco_ordem_publica=False,
            risco_ordem_economica=False,
            risco_instrucao_criminal=True, # único fundamento — caducou
            risco_aplicacao_lei_penal=False,
        ))
        assert status == "ILEGAL"
        assert "instrução" in motivo.lower()

    def test_risco_instrucao_pos_encerramento_com_outros_legal(self):
        """Outros periculum válidos sustentam a prisão mesmo com instrução encerrada."""
        status, _, _ = avaliar_prisao_preventiva(proc(
            fase_inquerito=False,
            instrucao_encerrada=True,
            risco_ordem_publica=True,       # outro fundamento válido
            risco_instrucao_criminal=True,
        ))
        assert status == "LEGAL"

    def test_risco_instrucao_durante_inquerito_valido(self):
        """Durante o IP, risco à instrução ainda é válido (instrucao_encerrada=False)."""
        status, _, _ = avaliar_prisao_preventiva(proc(
            fase_inquerito=True,
            instrucao_encerrada=False,
            risco_ordem_publica=False,
            risco_instrucao_criminal=True,
            risco_aplicacao_lei_penal=False,
        ))
        assert status == "LEGAL"


# ---------------------------------------------------------------------------
# 7. FORMA DA DECISÃO
# ---------------------------------------------------------------------------
def test_fundamentacao_generica_ilegal():
    status, _, fundamento = avaliar_prisao_preventiva(proc(fundamentacao_generica=True))
    assert status == "ILEGAL"
    assert "315" in fundamento

def test_fundamentacao_especifica_ok():
    assert avaliar_prisao_preventiva(proc(fundamentacao_generica=False))[0] == "LEGAL"


# ---------------------------------------------------------------------------
# 8. CONTEMPORANEIDADE
# ---------------------------------------------------------------------------
def test_fatos_pretéritos_ilegal():
    status, motivo, _ = avaliar_prisao_preventiva(proc(fatos_novos_ou_contemporaneos=False))
    assert status == "ILEGAL"
    assert "contemporan" in motivo.lower()

def test_crime_permanente_sem_conduta_recente_ilegal():
    status, motivo, _ = avaliar_prisao_preventiva(proc(
        crime_permanente=True, conduta_recente_demonstrada=False
    ))
    assert status == "ILEGAL"
    assert "permanente" in motivo.lower()

def test_crime_permanente_com_conduta_recente_legal():
    assert avaliar_prisao_preventiva(proc(
        crime_permanente=True, conduta_recente_demonstrada=True
    ))[0] == "LEGAL"


# ---------------------------------------------------------------------------
# 9. REVISÃO PERIÓDICA — art. 316
# ---------------------------------------------------------------------------
class TestRevisao316:

    def test_90_dias_no_limite_legal(self):
        assert avaliar_prisao_preventiva(proc(dias_desde_ultima_revisao=90))[0] == "LEGAL"

    def test_91_dias_sem_intimacao_alerta(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(
            dias_desde_ultima_revisao=91,
            juizo_foi_intimado_apos_90_dias=False,
        ))
        assert status == "ALERTA"
        assert "intima" in motivo.lower()

    def test_91_dias_com_intimacao_inerte_ilegal(self):
        status, motivo, _ = avaliar_prisao_preventiva(proc(
            dias_desde_ultima_revisao=91,
            juizo_foi_intimado_apos_90_dias=True,
        ))
        assert status == "ILEGAL"
        assert "inerte" in motivo.lower()