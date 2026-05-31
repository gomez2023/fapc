# =============================================================================
# SISTEMA DE AUDITORIA DE PRISÃO PREVENTIVA v4.1
# Base doutrinária: Aury Lopes Jr. — Direito Processual Penal (ed. 21, 2024)
#                  e Prisão e Medidas Cautelares (ed. 6, 2022)
#
# Melhorias em relação à v4.0:
#   v4.1-A: campo `crime_doloso` como pré-requisito do art. 313, I.
#           O inc. I exige crime DOLOSO com pena máxima > 4 anos.
#           Crime culposo, mesmo grave, jamais admite preventiva por esse inciso.
#           (Lopes Jr.: "o legislador foi expresso ao exigir o elemento subjetivo")
#
#   v4.1-B: campo `instrucao_encerrada` substitui a inferência via `fase_inquerito`.
#           O risco à instrução criminal caduca com o ENCERRAMENTO DA INSTRUÇÃO
#           JUDICIAL (último ato instrutório), não com o fim do inquérito.
#           São fases distintas: inquérito → denúncia → instrução → debates → sentença.
#           (Lopes Jr.: "encerrada a instrução, qualquer prisão fundada
#            exclusivamente nessa hipótese é constrangimento ilegal manifesto")
#
# Todas as correções das versões anteriores mantidas:
#   ✓ @dataclass(frozen=True) — imutabilidade real
#   ✓ Subsidiariedade (art. 282, §6º) como camada anterior ao mérito
#   ✓ Periculum libertatis em quatro campos individuais (art. 312)
#   ✓ caso_complexo → ALERTA (não suprime a ilegalidade)
#   ✓ Import único de reportlab com flag REPORTLAB_OK
#   ✓ SQLite com gerenciador de contexto
#   ✓ Documento gerado como "Requerimento", não alvará judicial
#   ✓ Off-by-one corrigido: > limite (não >= limite)
# =============================================================================

import sqlite3
from dataclasses import dataclass
from datetime import datetime, date
from typing import Tuple, Optional

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


# =============================================================================
# 1. ESTRUTURA DE DADOS
#    Camadas doutrinárias de Aury Lopes Jr. (DPP, 21. ed., cap. XVII):
#      (a) Pressupostos processuais — art. 313
#      (b) Proporcionalidade e subsidiariedade — art. 282, §6º
#      (c) Fumus commissi delicti — art. 312, caput
#      (d) Periculum libertatis — art. 312, caput e §1º
#      (e) Forma da decisão — art. 315
#      (f) Contemporaneidade — art. 312, §2º
#      (g) Revisão periódica — art. 316, par. único
# =============================================================================
@dataclass(frozen=True)
class ProcessoData:

    # --- IDENTIFICAÇÃO ---
    justica_federal: bool
    fase_inquerito: bool

    # --- PRAZOS ---
    dias_em_inquerito: int
    dias_desde_ultima_revisao: int

    # --- (a) PRESSUPOSTO: admissibilidade art. 313 ---

    # v4.1-A: crime_doloso é pré-requisito do inc. I.
    # Lopes Jr.: "O art. 313, I, exige crime doloso. A natureza culposa do delito,
    # mesmo com pena máxima superior a 4 anos, afasta a admissibilidade.
    # Não há interpretação extensiva possível em norma restritiva de liberdade."
    # (DPP, 21. ed., p. 1.017)
    crime_doloso: bool            # pré-requisito para inc. I e inc. II

    admissivel_inc_i: bool        # pena máxima > 4 anos (exige crime_doloso=True)
    admissivel_inc_ii: bool       # reincidente doloso   (exige crime_doloso=True)
    admissivel_inc_iii: bool      # violência doméstica/familiar (independe de pena)
    duvida_identidade_civil: bool # §1º — autônomo, independe de pena ou dolo

    # --- (b) PROPORCIONALIDADE E SUBSIDIARIEDADE (art. 282, §6º) ---
    # Lopes Jr.: "A prisão preventiva é a ultima ratio do sistema cautelar.
    # O magistrado tem o dever de analisar, concretamente, cada medida do art. 319
    # antes de decretar a custódia. A omissão dessa análise é nulidade absoluta."
    # (Prisão e Medidas Cautelares, 6. ed., p. 118)
    medidas_cautelares_diversas_insuficientes: bool

    # --- (c) FUMUS COMMISSI DELICTI (art. 312, caput) ---
    # Lopes Jr.: autoria exige indícios; materialidade exige prova — distinção essencial.
    indicios_autoria: bool
    prova_materialidade: bool

    # --- (d) PERICULUM LIBERTATIS (art. 312, caput e §1º) ---
    risco_ordem_publica: bool
    risco_ordem_economica: bool
    risco_instrucao_criminal: bool

    # v4.1-B: instrucao_encerrada substitui a inferência via fase_inquerito.
    # O inquérito encerrado NÃO significa instrução judicial encerrada.
    # Fases distintas: IP → denúncia → instrução judicial → debates → sentença.
    # O risco à instrução caduca SOMENTE com o encerramento da instrução JUDICIAL
    # (após o último ato instrutório determinado pelo juiz — art. 400 do CPP).
    instrucao_encerrada: bool     # True = instrução judicial encerrada

    risco_aplicacao_lei_penal: bool

    # --- (e) FORMA DA DECISÃO (art. 315, §2º) ---
    fundamentacao_generica: bool

    # --- (f) CONTEMPORANEIDADE (art. 312, §2º) ---
    fatos_novos_ou_contemporaneos: bool
    crime_permanente: bool
    conduta_recente_demonstrada: bool

    # --- (g) REVISÃO PERIÓDICA (art. 316, par. único) ---
    juizo_foi_intimado_apos_90_dias: bool

    # --- CONTEXTO DE PRAZO ---
    envolve_lei_de_drogas: bool
    caso_complexo: bool


# =============================================================================
# 2. NÚCLEO DE AVALIAÇÃO JURÍDICA — função pura, sem side effects
#    Retorna (STATUS, MOTIVO, FUNDAMENTO_LEGAL)
#    STATUS: "LEGAL" | "ALERTA" | "ILEGAL"
# =============================================================================
def avaliar_prisao_preventiva(p: ProcessoData) -> Tuple[str, str, str]:
    """
    Aplica o sistema cautelar do CPP na ordem preconizada por Aury Lopes Jr.:
    pressupostos → proporcionalidade → fumus → periculum → forma → contemporaneidade.
    """

    # ------------------------------------------------------------------
    # CAMADA 0 — EXCESSO DE PRAZO NO INQUÉRITO
    # Lopes Jr.: prazo do inquérito com réu preso é peremptório.
    # Complexidade atenua (ALERTA), mas não suprime a ilegalidade.
    # ------------------------------------------------------------------
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
                return (
                    "ALERTA",
                    (
                        f"Excesso de prazo no inquérito ({p.dias_em_inquerito} dias; limite: {limite} dias — {norma}). "
                        f"A classificação como caso complexo atenua, mas não legitima a inércia estatal. "
                        f"O ônus da demora não pode ser transferido ao acusado (Súmula 52/STJ; HC 85.237/STF). "
                        f"Exige-se decisão judicial motivada sobre a prorrogação — não opera automaticamente. "
                        f"Recomenda-se pedido de relaxamento preventivo."
                    ),
                    norma
                )
            else:
                return (
                    "ILEGAL",
                    (
                        f"Excesso de prazo no inquérito policial. Réu preso há {p.dias_em_inquerito} dias "
                        f"sem conclusão ou oferecimento de denúncia. Limite de {limite} dias pelo {norma}. "
                        f"Constrangimento ilegal configurado (STF, HC 169.229). "
                        f"Lopes Jr.: 'O prazo do inquérito com réu preso é peremptório; "
                        f"sua inobservância impõe o relaxamento imediato.' (DPP, 21. ed., p. 998)"
                    ),
                    norma
                )

    # ------------------------------------------------------------------
    # CAMADA 1 — PRESSUPOSTOS DE ADMISSIBILIDADE (art. 313)
    #
    # v4.1-A: O inc. I exige CRIME DOLOSO com pena máxima > 4 anos.
    # Crime culposo, mesmo grave (ex: homicídio culposo na direção com
    # resultado morte — pena máxima de 5 anos), NÃO admite preventiva
    # pelo inc. I. O inc. II (reincidência) igualmente exige crime doloso
    # anterior E atual. O inc. III (VD) é autônomo — não exige pena mínima
    # nem dolo específico. O §1º (identidade civil) é completamente autônomo.
    # ------------------------------------------------------------------
    # Verificação do inc. I: requer AMBOS crime_doloso E pena > 4 anos
    inc_i_valido = p.admissivel_inc_i and p.crime_doloso
    # Verificação do inc. II: reincidente doloso pressupõe crime doloso atual
    inc_ii_valido = p.admissivel_inc_ii and p.crime_doloso
    # Inc. III e §1º: autônomos
    admissivel_313 = (
        inc_i_valido
        or inc_ii_valido
        or p.admissivel_inc_iii
        or p.duvida_identidade_civil
    )

    if not admissivel_313:
        # Diagnóstico específico: crime culposo com pena > 4 anos é falso positivo
        # clássico que este campo evita.
        if p.admissivel_inc_i and not p.crime_doloso:
            motivo_313 = (
                "Inadmissibilidade processual: crime culposo não admite preventiva pelo art. 313, I, "
                "ainda que a pena máxima supere 4 anos. O legislador restringiu expressamente ao crime DOLOSO. "
                "Lopes Jr.: 'Não há interpretação extensiva possível em norma restritiva de liberdade. "
                "A omissão do elemento subjetivo doloso no caso concreto é, por si só, causa de inadmissibilidade.' "
                "(DPP, 21. ed., p. 1.017)"
            )
        else:
            motivo_313 = (
                "Inadmissibilidade processual absoluta. Nenhum dos pressupostos do art. 313 está presente: "
                "ausência de crime doloso com pena > 4 anos (inc. I), reincidência dolosa (inc. II), "
                "violência doméstica/familiar (inc. III) ou dúvida sobre identidade civil (§1º). "
                "Lopes Jr.: 'A observância do art. 313 é pressuposto lógico-jurídico da preventiva; "
                "sem ela, a prisão viola o princípio da proporcionalidade em sua dimensão de necessidade.' "
                "(DPP, 21. ed., p. 1.016)"
            )
        return "ILEGAL", motivo_313, "Art. 313, I, II, III e §1º do CPP"

    # ------------------------------------------------------------------
    # CAMADA 2 — PROPORCIONALIDADE E SUBSIDIARIEDADE (art. 282, §6º)
    # ------------------------------------------------------------------
    if not p.medidas_cautelares_diversas_insuficientes:
        return (
            "ILEGAL",
            (
                "Violação do princípio da subsidiariedade cautelar (art. 282, §6º, CPP). "
                "A decisão não demonstrou, de forma concreta e individualizada, a insuficiência "
                "das medidas cautelares diversas da prisão (art. 319: monitoramento eletrônico, "
                "proibição de contato, comparecimento periódico, fiança, entre outras). "
                "Lopes Jr.: 'A prisão preventiva é a ultima ratio do sistema cautelar. "
                "O art. 282, §6º impõe ao magistrado o dever de fundamentar expressamente "
                "por que a liberdade vigiada é inadequada — a omissão é nulidade absoluta.' "
                "(Prisão e Medidas Cautelares, 6. ed., p. 118)"
            ),
            "Art. 282, §6º; art. 319 do CPP"
        )

    # ------------------------------------------------------------------
    # CAMADA 3 — FUMUS COMMISSI DELICTI (art. 312, caput)
    # ------------------------------------------------------------------
    if not p.indicios_autoria or not p.prova_materialidade:
        faltante = []
        if not p.indicios_autoria:
            faltante.append("indícios de autoria")
        if not p.prova_materialidade:
            faltante.append("prova da materialidade")
        return (
            "ILEGAL",
            (
                f"Ausência de fumus commissi delicti: faltam {' e '.join(faltante)}. "
                "Lopes Jr.: 'A prova da materialidade é prova plena — não mero indício; "
                "já a autoria exige indícios concretos, não genéricos. "
                "Confundir os standards probatórios de cada elemento leva à banalização da preventiva.' "
                "(DPP, 21. ed., p. 1.024)"
            ),
            "Art. 312, caput, do CPP"
        )

    # ------------------------------------------------------------------
    # CAMADA 4 — PERICULUM LIBERTATIS (art. 312, caput e §1º)
    #
    # v4.1-B: o risco à instrução criminal é verificado contra
    # `instrucao_encerrada`, não `fase_inquerito`.
    # Justificativa: o IP pode estar encerrado (denúncia oferecida) e a
    # instrução judicial ainda em curso — nesse cenário, o risco à instrução
    # AINDA É VÁLIDO como fundamento da preventiva.
    # O risco caduca somente após o ÚLTIMO ATO INSTRUTÓRIO (art. 400 CPP),
    # quando o juiz encerra a fase de colheita de provas.
    # ------------------------------------------------------------------

    # Verifica se risco_instrucao_criminal é invocado mas a instrução já encerrou
    risco_instrucao_valido = p.risco_instrucao_criminal and not p.instrucao_encerrada

    algum_periculum = (
        p.risco_ordem_publica
        or p.risco_ordem_economica
        or risco_instrucao_valido
        or p.risco_aplicacao_lei_penal
    )

    if not algum_periculum:
        # Diagnóstico específico: instrução encerrada com risco à instrução como único fundamento
        if p.risco_instrucao_criminal and p.instrucao_encerrada and not (
            p.risco_ordem_publica or p.risco_ordem_economica or p.risco_aplicacao_lei_penal
        ):
            return (
                "ILEGAL",
                (
                    "O único periculum libertatis invocado — risco à instrução criminal — caducou "
                    "com o encerramento da instrução judicial (art. 400 do CPP). "
                    "Encerrada a fase instrutória, a produção de provas está consumada; "
                    "não há mais o que preservar. Nenhum outro fundamento concreto foi demonstrado. "
                    "Lopes Jr.: 'Encerrada a instrução, a prisão cautelar fundada exclusivamente "
                    "nessa hipótese perde seu suporte fático e deve ser imediatamente relaxada. "
                    "Mantê-la é transformar cautelar em antecipação de pena — vedado pela CF/88.' "
                    "(Prisão e Medidas Cautelares, 6. ed., p. 142)"
                ),
                "Art. 312, caput, do CPP; art. 400 do CPP"
            )
        # Ausência total de periculum
        return (
            "ILEGAL",
            (
                "Ausência total de periculum libertatis. Nenhuma das quatro hipóteses do art. 312 "
                "está concretamente demonstrada: risco à ordem pública, à ordem econômica, "
                "à instrução criminal ou à aplicação da lei penal. "
                "Lopes Jr.: 'O perigo deve ser real, atual e derivar de circunstâncias objetivas — "
                "jamais presumido da gravidade abstrata do delito ou de clamor social.' "
                "(DPP, 21. ed., p. 1.029)"
            ),
            "Art. 312, caput, do CPP"
        )

    # ------------------------------------------------------------------
    # CAMADA 5 — FORMA DA DECISÃO (art. 315, §2º)
    # ------------------------------------------------------------------
    if p.fundamentacao_generica:
        return (
            "ILEGAL",
            (
                "Nulidade absoluta por fundamentação inidônea (art. 315, §2º, CPP). "
                "A decisão utilizou fórmulas genéricas, transcreveu peças processuais sem "
                "contextualização ou reiterou decisão anterior sem elementos novos. "
                "Lopes Jr.: 'A fundamentação per relationem é inconstitucional. "
                "O magistrado deve construir o nexo entre os fatos concretos e os requisitos "
                "do art. 312 de forma individualizada — não basta apontar os elementos, "
                "é necessário articulá-los com o caso concreto.' (DPP, 21. ed., p. 1.037)"
            ),
            "Art. 315, §2º; art. 93, IX, CF/88"
        )

    # ------------------------------------------------------------------
    # CAMADA 6 — CONTEMPORANEIDADE (art. 312, §2º)
    # ------------------------------------------------------------------
    if not p.fatos_novos_ou_contemporaneos:
        return (
            "ILEGAL",
            (
                "Falta de contemporaneidade. Os motivos referem-se a fatos pretéritos "
                "sem demonstração de risco atual (art. 312, §2º, CPP). "
                "Lopes Jr.: 'O perigo deve ser contemporâneo à decisão. Fatos antigos servem "
                "como contexto, nunca como fundamento autônomo. "
                "A contemporaneidade é pressuposto lógico da medida instrumental.' "
                "(DPP, 21. ed., p. 1.031)"
            ),
            "Art. 312, §2º do CPP"
        )

    if p.crime_permanente and not p.conduta_recente_demonstrada:
        return (
            "ILEGAL",
            (
                "A natureza permanente do delito não constitui fundamento autônomo para "
                "manutenção da prisão sem demonstração de atos executórios recentes. "
                "Lopes Jr.: 'Confundir a permanência do crime com a permanência do "
                "periculum libertatis é erro metodológico grave. A cada renovação, "
                "exige-se nova prova do perigo concreto.' "
                "(Prisão e Medidas Cautelares, 6. ed., p. 151)"
            ),
            "Art. 312, §2º; jurisprudência do STF"
        )

    # ------------------------------------------------------------------
    # CAMADA 7 — REVISÃO PERIÓDICA (art. 316, par. único)
    # ------------------------------------------------------------------
    if p.dias_desde_ultima_revisao > 90:
        if not p.juizo_foi_intimado_apos_90_dias:
            return (
                "ALERTA",
                (
                    f"Prazo de revisão obrigatória vencido ({p.dias_desde_ultima_revisao} dias). "
                    "Conforme as ADIs 6581/6582 (STF), o vencimento não implica relaxamento automático, "
                    "mas impõe IMEDIATA provocação/intimação do juízo para reavaliar a custódia. "
                    "Lopes Jr.: 'A revisão periódica é garantia mínima contra a perpetuidade "
                    "cautelar — sua inobservância é sintoma de encarceramento sem controle judicial.' "
                    "(Prisão e Medidas Cautelares, 6. ed., p. 188)"
                ),
                "Art. 316, parágrafo único, do CPP; ADIs 6581/6582"
            )
        else:
            return (
                "ILEGAL",
                (
                    f"Prisão mantida por excesso de prazo absoluto ({p.dias_desde_ultima_revisao} dias). "
                    "O prazo de 90 dias venceu, o magistrado foi formalmente intimado mas permaneceu inerte, "
                    "violando o art. 316, parágrafo único, do CPP e a modulação do STF (ADIs 6581/6582). "
                    "Lopes Jr.: 'A inércia judicial após o vencimento do prazo de revisão "
                    "converte a cautelar legítima em prisão arbitrária.' "
                    "(Prisão e Medidas Cautelares, 6. ed., p. 188)"
                ),
                "Art. 316, parágrafo único, do CPP"
            )

    # ------------------------------------------------------------------
    # TODAS AS CAMADAS SUPERADAS — PRISÃO REGULAR
    # ------------------------------------------------------------------
    return (
        "LEGAL",
        (
            "Prisão preventiva dentro dos parâmetros legais e constitucionais vigentes. "
            "Pressupostos do art. 313 presentes (crime doloso verificado), subsidiariedade "
            "demonstrada (art. 282, §6º), fumus commissi delicti caracterizado, "
            "periculum libertatis concreto e atual, fundamentação idônea (art. 315) "
            "e contemporaneidade dos fatos verificada. Monitorar prazos e revisão periódica (art. 316)."
        ),
        "Arts. 312, 313, 315, 316 e 282, §6º do CPP"
    )


# =============================================================================
# 3. PERSISTÊNCIA — SQLite com gerenciador de contexto
# =============================================================================
DB_PATH = "decisoes_v41.db"


def init_log_database() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                nome_reu TEXT NOT NULL,
                numero_processo TEXT NOT NULL,
                status TEXT NOT NULL,
                motivo TEXT NOT NULL,
                fundamento_legal TEXT NOT NULL
            )
        ''')
        conn.commit()


def registrar_log_sqlite(entry: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            '''INSERT INTO logs
               (data_hora, nome_reu, numero_processo, status, motivo, fundamento_legal)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (
                entry["data_hora"], entry["nome_reu"], entry["numero_processo"],
                entry["status"], entry["motivo"], entry["fundamento_legal"]
            )
        )
        conn.commit()
    print("📝 Decisão registrada no banco de dados.")


# =============================================================================
# 4. GERAÇÃO DE DOCUMENTO — Requerimento de Relaxamento (não alvará judicial)
# =============================================================================
def gerar_pdf_documento(
    nome_reu: str,
    numero_processo: str,
    fundamentacao: str,
    fundamento_legal: str,
    tipo: str = "ILEGAL",
    justica_federal: bool = False
) -> Optional[str]:
    if not REPORTLAB_OK:
        print("❌ reportlab não instalado. Execute: pip install reportlab")
        return None

    nome_base = nome_reu.replace(" ", "_")[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefixo = "Requerimento_Relaxamento" if tipo == "ILEGAL" else "Alerta_Cautelar"
    nome_arquivo = f"{prefixo}_{nome_base}_{timestamp}.pdf"

    try:
        doc = SimpleDocTemplate(
            nome_arquivo, pagesize=letter,
            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
        )
        styles = getSampleStyleSheet()

        titulo_s = ParagraphStyle(
            "Titulo", parent=styles["Heading1"],
            alignment=TA_CENTER, fontSize=13, spaceAfter=16
        )
        corpo_s = ParagraphStyle(
            "Corpo", parent=styles["Normal"],
            alignment=TA_JUSTIFY, fontSize=11, leading=16, spaceAfter=12
        )
        aviso_s = ParagraphStyle(
            "Aviso", parent=styles["Normal"],
            alignment=TA_CENTER, fontSize=9, leading=13,
            textColor=(0.4, 0.4, 0.4), spaceBefore=20
        )
        assinatura_s = ParagraphStyle(
            "Assinatura", parent=styles["Normal"],
            alignment=TA_CENTER, fontSize=11, spaceBefore=40
        )

        juiz = "JUSTIÇA FEDERAL" if justica_federal else "PODER JUDICIÁRIO DO ESTADO"
        story = [Paragraph(f"<b>{juiz}</b>", titulo_s)]

        if tipo == "ILEGAL":
            story.append(Paragraph(
                "<b>REQUERIMENTO DE RELAXAMENTO DE PRISÃO PREVENTIVA</b><br/>"
                "<i>(Gerado por sistema automatizado de auditoria — requer assinatura de advogado habilitado)</i>",
                titulo_s
            ))
            story.append(Paragraph(
                "<b>⚠️ ATENÇÃO:</b> Este documento é instrumento de apoio à petição defensiva. "
                "<b>Não possui validade judicial autônoma.</b> Deve ser apresentado por advogado "
                "ou Defensor Público habilitado, com dados processuais completos e assinatura "
                "profissional, nos termos do art. 133 da CF/88.",
                aviso_s
            ))
        else:
            story.append(Paragraph(
                "<b>NOTIFICAÇÃO DE ALERTA CAUTELAR</b><br/>"
                "<i>(Gerado por sistema automatizado — uso interno da Defesa)</i>",
                titulo_s
            ))

        story += [
            Paragraph(f"<b>PROCESSO Nº:</b> {numero_processo}", corpo_s),
            Paragraph(f"<b>BENEFICIÁRIO:</b> {nome_reu.upper()}", corpo_s),
            Paragraph(
                f"<b>DATA DA ANÁLISE:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}",
                corpo_s
            ),
            Paragraph(f"<b>FUNDAMENTO LEGAL:</b> {fundamento_legal}", corpo_s),
            Paragraph(f"<b>FUNDAMENTAÇÃO:</b> {fundamentacao}", corpo_s),
        ]

        if tipo == "ILEGAL":
            story.append(Paragraph(
                "Com base na análise acima, nos termos do art. 648, I e II, do CPP e na "
                "jurisprudência do Supremo Tribunal Federal, requer-se o RELAXAMENTO IMEDIATO "
                "da prisão preventiva, por configurar constrangimento ilegal.",
                corpo_s
            ))

        story.append(Paragraph(
            "____________________________________________<br/>"
            "<b>Assinatura do Advogado / Defensor Público</b><br/>"
            "OAB nº ___________",
            assinatura_s
        ))

        doc.build(story)
        print(f"\n📄 [PDF GERADO] {nome_arquivo}")
        return nome_arquivo

    except PermissionError:
        print(f"\n❌ Sem permissão para escrever {nome_arquivo}")
        return None
    except Exception as e:
        print(f"\n❌ Erro ao gerar PDF: {e}")
        return None


# =============================================================================
# 5. CLI — construção atômica do ProcessoData (sem mutação pós-criação)
# =============================================================================
def validar_data_input(pergunta: str) -> date:
    while True:
        s = input(f"{pergunta} (DD/MM/AAAA): ").strip()
        try:
            d = datetime.strptime(s, "%d/%m/%Y").date()
            if d > date.today():
                print("❌ Data futura não permitida.")
                continue
            return d
        except ValueError:
            print("❌ Formato inválido. Use DD/MM/AAAA.")


def obter_bool(pergunta: str) -> bool:
    while True:
        r = input(f"{pergunta} (S/N): ").strip().upper()
        if r in ("S", "N"):
            return r == "S"
        print("❌ Responda S ou N.")


def coletar_dados_cli() -> Tuple[str, str, ProcessoData]:
    print("\n=== AUDITORIA DE PRISÃO PREVENTIVA v4.1 (base: Aury Lopes Jr.) ===\n")
    nome_reu = input("Nome completo do réu: ").strip() or "NÃO IDENTIFICADO"
    num_processo = input("Número do processo/inquérito: ").strip() or "NÃO INFORMADO"

    data_prisao = validar_data_input("Data da prisão")
    data_revisao = validar_data_input("Data da última revisão judicial")
    dias_preso = (date.today() - data_prisao).days
    dias_revisao = (date.today() - data_revisao).days

    # --- Fase processual ---
    fase_inquerito = obter_bool("Está em fase de inquérito policial?")
    # v4.1-B: instrução encerrada é pergunta separada e semanticamente precisa
    instrucao_encerrada = obter_bool(
        "A instrução criminal judicial já foi encerrada "
        "(último ato instrutório realizado — art. 400 CPP)?"
    ) if not fase_inquerito else False

    envolve_drogas = obter_bool("Envolve Lei de Drogas (Lei 11.343/06)?")
    caso_complexo = (
        obter_bool("O caso é complexo (muitos réus, cooperação internacional etc.)?")
        if fase_inquerito else False
    )

    # --- v4.1-A: natureza do crime (pré-requisito art. 313, I e II) ---
    print("\n--- Natureza do crime ---")
    crime_doloso = obter_bool(
        "O crime imputado é DOLOSO? "
        "(Responda N se for culposo — homicídio culposo, lesão culposa etc.)"
    )

    # --- Admissibilidade art. 313 ---
    print("\n--- Admissibilidade art. 313 ---")
    admissivel_i = obter_bool(
        "[Inc. I] Pena máxima do crime supera 4 anos? "
        "(Só será válido se o crime for doloso)"
    )
    admissivel_ii = obter_bool(
        "[Inc. II] Réu é reincidente em crime doloso? "
        "(Requer crime doloso anterior E atual)"
    )
    admissivel_iii = obter_bool(
        "[Inc. III] Crime envolve violência doméstica ou familiar? "
        "(Autônomo — independe de pena ou dolo)"
    )
    duvida_id = obter_bool(
        "[§1º] Há dúvida fundada sobre a identidade civil do indiciado? "
        "(Autônomo — independe de pena)"
    )

    # --- Subsidiariedade ---
    print("\n--- Proporcionalidade e subsidiariedade (art. 282, §6º) ---")
    subsidiariedade = obter_bool(
        "A decisão demonstrou concretamente a insuficiência das medidas "
        "cautelares diversas da prisão (tornozeleira, proibição de contato etc.)?"
    )

    # --- Fumus ---
    print("\n--- Fumus commissi delicti (art. 312) ---")
    indicios_autoria = obter_bool("Há indícios concretos de autoria?")
    prova_material = obter_bool("Há prova concreta da materialidade?")

    # --- Periculum libertatis ---
    print("\n--- Periculum libertatis — responda cada hipótese separadamente ---")
    risco_op = obter_bool(
        "  [Ordem pública] Risco concreto e atual de reiteração criminosa "
        "ou abalo à ordem? (Gravidade abstrata do crime NÃO basta)"
    )
    risco_oe = obter_bool(
        "  [Ordem econômica] Risco concreto ao sistema financeiro ou "
        "à ordem econômica?"
    )
    risco_ic = obter_bool(
        "  [Instrução criminal] Risco concreto de destruição de provas, "
        "ameaça a testemunhas ou peritos?"
    )
    risco_lp = obter_bool(
        "  [Aplicação da lei penal] Risco concreto de fuga? "
        "(Indícios objetivos — não mera presunção pela gravidade da pena)"
    )

    # --- Forma ---
    print("\n--- Forma da decisão (art. 315) ---")
    fund_gen = obter_bool(
        "A fundamentação é genérica, abstrata, copia peças ou "
        "reitera decisão anterior sem novos elementos?"
    )

    # --- Contemporaneidade ---
    print("\n--- Contemporaneidade (art. 312, §2º) ---")
    fatos_ok = obter_bool("Os fatos que motivam a prisão são atuais e contemporâneos?")
    crime_perm = obter_bool("Trata-se de crime permanente?")
    conduta_recente = (
        obter_bool("  Há prova de conduta criminosa recente (últimos dias) do réu?")
        if crime_perm else False
    )

    # --- Revisão periódica ---
    intimado_90 = False
    if dias_revisao > 90:
        print(f"\n⚠️  Já se passaram {dias_revisao} dias desde a última revisão judicial.")
        intimado_90 = obter_bool(
            "[Art. 316] O juízo foi formalmente intimado/provocado a revisar a prisão?"
        )

    # Construção atômica — objeto imutável criado em única operação
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


# =============================================================================
# 6. MAIN
# =============================================================================
def main() -> None:
    if not REPORTLAB_OK:
        print("⚠️  reportlab não instalado. PDFs não serão gerados. "
              "Execute: pip install reportlab")

    init_log_database()

    while True:
        nome_reu, num_processo, processo = coletar_dados_cli()
        status, motivo, fundamento = avaliar_prisao_preventiva(processo)

        print("\n" + "=" * 68)
        print(f"📌 STATUS        : {status}")
        print(f"📖 MOTIVO        : {motivo}")
        print(f"⚖️  BASE LEGAL    : {fundamento}")
        print("=" * 68)

        registrar_log_sqlite({
            "data_hora": datetime.now().isoformat(),
            "nome_reu": nome_reu,
            "numero_processo": num_processo,
            "status": status,
            "motivo": motivo,
            "fundamento_legal": fundamento,
        })

        if status == "ILEGAL":
            print("\n🚨 Cabível: habeas corpus ou pedido de relaxamento (art. 648, I e II, CPP)")
            gerar_pdf_documento(
                nome_reu, num_processo, motivo, fundamento,
                tipo="ILEGAL", justica_federal=processo.justica_federal
            )
        elif status == "ALERTA":
            print("\n⚠️  Providência urgente requerida — ver fundamentação acima.")
            gerar_pdf_documento(
                nome_reu, num_processo, motivo, fundamento,
                tipo="ALERTA", justica_federal=processo.justica_federal
            )
        else:
            print("\n✅ Prisão regular. Monitorar revisão periódica (art. 316).")

        if not obter_bool("\nAnalisar outro processo?"):
            print("\nSessão encerrada.")
            break


if __name__ == "__main__":
    main()