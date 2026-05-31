# fapc

Ferramenta de Análise de Prisões Cautelares — auditoria automatizada da legalidade de prisões preventivas com base nos arts. 312 a 316 do CPP e doutrina de Aury Lopes Jr.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Pytest](https://img.shields.io/badge/Testes-34%20passed-22c55e?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![Licenca](https://img.shields.io/badge/Licenca-Academica-f59e0b?style=flat-square)](#licenca)
[![Versao](https://img.shields.io/badge/Versao-4.1-6366f1?style=flat-square)](#historico-de-versoes)

## Sumario

- [Background](#background)
- [Instalacao](#instalacao)
- [Uso](#uso)
- [API](#api)
- [Testes](#testes)
- [Historico de Versoes](#historico-de-versoes)
- [Como Citar](#como-citar)
- [Contribuicoes](#contribuicoes)
- [Licenca](#licenca)

## Background

O FAPC e um sistema baseado em regras (nao em IA) que traduz a logica juridica do sistema cautelar brasileiro em um algoritmo deterministico, auditavel e testavel. Diferentemente de sistemas preditivos, o FAPC apenas aplica explicitamente a lei e a doutrina — qualquer operador juridico pode verificar linha por linha a correspondencia com os arts. 312 a 316 do CPP.

O sistema emite tres status:

| Status | Significado | Acao recomendada |
|--------|-------------|------------------|
| `LEGAL` | Todos os requisitos legais presentes | Monitorar prazos e revisao periodica |
| `ALERTA` | Irregularidade iminente ou prazo vencido | Provocar o juizo imediatamente |
| `ILEGAL` | Constrangimento ilegal identificado | Impetrar HC ou pedido de relaxamento |

**Base juridica aplicada:**

| Norma | Conteudo auditado |
|-------|------------------|
| CPP, art. 10 | Prazo do inquerito policial com reu preso (10 dias estadual / 15 dias federal) |
| Lei 11.343/06, art. 51 | Prazo do inquerito em crimes de drogas (30 dias) |
| CPP, art. 282, paragrafo 6 | Subsidiariedade — analise obrigatoria das cautelares do art. 319 antes da preventiva |
| CPP, art. 312, caput | Fumus commissi delicti (indicios de autoria + prova da materialidade) |
| CPP, art. 312, caput e paragrafo 1 | Periculum libertatis — quatro hipoteses individuais |
| CPP, art. 312, paragrafo 2 | Contemporaneidade dos fatos que motivam a prisao |
| CPP, art. 313, I, II, III e paragrafo 1 | Admissibilidade processual — requisitos por inciso |
| CPP, art. 315, paragrafo 2 | Forma da decisao — vedacao a fundamentacao generica |
| CPP, art. 316, par. unico | Revisao periodica obrigatoria a cada 90 dias |
| CPP, art. 400 | Encerramento da instrucao criminal judicial |
| CF/88, art. 93, IX | Dever de fundamentacao das decisoes judiciais |

**Jurisprudencia incorporada:**

- STF, ADIs 6581 e 6582 (julgadas em 08/03/2022, rel. Min. Edson Fachin) — vencimento dos 90 dias nao gera relaxamento automatico; impoe provocacao imediata do juizo.
- STF, HC 85.237 — complexidade do caso nao legitima automaticamente a inércia estatal.
- STJ, Sumula 52 (aprovada em 17/09/1992, DJ 24/09/1992, p. 16.070) — encerrada a instrucao, fica superada a alegacao de excesso de prazo.

**Doutrina de referencia:**

- LOPES JR., Aury. Direito Processual Penal. 21. ed. Sao Paulo: SaraivaJur, 2024.
- LOPES JR., Aury. Prisao e Medidas Cautelares. 6. ed. Sao Paulo: SaraivaJur, 2022.

Aviso: este sistema e uma ferramenta de apoio academico e de triagem forense preliminar. Os documentos gerados nao possuem validade judicial autonoma. Toda peca processual deve ser assinada por advogado ou Defensor Publico habilitado (art. 133, CF/88).

## Instalacao

Requisitos: Python 3.10 ou superior (Windows 10+, Linux ou macOS).

```bash
git clone https://github.com/gomez2023/fapc.git
cd fapc
pip install -r requirements.txt
```

A dependencia `reportlab` e necessaria apenas para geracao de PDF. A analise juridica funciona sem ela.

```bash
pip install reportlab
pip install pytest
```

## Uso

```bash
python run.py
```

O sistema conduz o usuario por um formulario estruturado nas mesmas camadas doutrinárias do fluxo de avaliacao:

```
=== AUDITORIA DE PRISAO PREVENTIVA v4.1 (base: Aury Lopes Jr.) ===

Nome completo do reu: Joao da Silva
Numero do processo/inquerito: 0001234-56.2024.8.26.0050
Data da prisao (DD/MM/AAAA): 10/04/2024
...

=================================================================
STATUS        : ILEGAL
MOTIVO        : Violacao do principio da subsidiariedade cautelar...
BASE LEGAL    : Art. 282, paragrafo 6; art. 319 do CPP
=================================================================

Cabivel: habeas corpus ou pedido de relaxamento (art. 648, I e II, CPP)
PDF GERADO: Requerimento_Relaxamento_Joao_da_Silva_20240530.pdf
```

O sistema registra cada analise no banco `decisoes_v41.db` e, conforme o status, gera:

- `Requerimento_Relaxamento_<reu>_<timestamp>.pdf` — quando `ILEGAL`; estruturado como minuta de requerimento de relaxamento, sem validade judicial autonoma.
- `Alerta_Cautelar_<reu>_<timestamp>.pdf` — quando `ALERTA`; documento de uso interno da defesa.

## API

O nucleo de avaliacao e uma funcao pura que pode ser integrada diretamente:

```python
from src.auditoria import avaliar_prisao_preventiva, ProcessoData

processo = ProcessoData(
    justica_federal=False,
    fase_inquerito=True,
    dias_em_inquerito=11,
    dias_desde_ultima_revisao=30,
    envolve_lei_de_drogas=False,
    caso_complexo=False,
    crime_doloso=True,
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
    instrucao_encerrada=False,
    risco_aplicacao_lei_penal=False,
    fundamentacao_generica=False,
    fatos_novos_ou_contemporaneos=True,
    crime_permanente=False,
    conduta_recente_demonstrada=False,
    juizo_foi_intimado_apos_90_dias=False,
)

status, motivo, fundamento = avaliar_prisao_preventiva(processo)
# status   -> "ILEGAL"
# fundamento -> "art. 10 do CPP (Justica Estadual)"
```

`ProcessoData` e um `@dataclass(frozen=True)` com 23 campos organizados em sete camadas juridicas:

**Identificacao e prazos**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `justica_federal` | bool | Caso tramita na Justica Federal |
| `fase_inquerito` | bool | Reu preso em fase de inquerito policial |
| `dias_em_inquerito` | int | Dias de prisao durante o inquerito |
| `dias_desde_ultima_revisao` | int | Dias desde a ultima revisao judicial (art. 316) |
| `envolve_lei_de_drogas` | bool | Crime sob a Lei 11.343/06 (prazo de 30 dias) |
| `caso_complexo` | bool | Inquerito complexo (atenua, nao suprime a ilegalidade) |

**Admissibilidade — art. 313**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `crime_doloso` | bool | Pre-requisito para inc. I e inc. II |
| `admissivel_inc_i` | bool | Pena maxima > 4 anos (requer `crime_doloso=True`) |
| `admissivel_inc_ii` | bool | Reincidente doloso (requer `crime_doloso=True`) |
| `admissivel_inc_iii` | bool | Violencia domestica/familiar (autonomo) |
| `duvida_identidade_civil` | bool | Duvida sobre identidade civil — par. 1 (autonomo) |

**Subsidiariedade — art. 282, par. 6**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `medidas_cautelares_diversas_insuficientes` | bool | Decisao demonstrou concretamente a insuficiencia das medidas do art. 319 |

**Fumus commissi delicti — art. 312, caput**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `indicios_autoria` | bool | Indicios concretos de autoria |
| `prova_materialidade` | bool | Prova plena da materialidade do crime |

**Periculum libertatis — art. 312**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `risco_ordem_publica` | bool | Risco concreto e atual a ordem publica |
| `risco_ordem_economica` | bool | Risco concreto a ordem economica |
| `risco_instrucao_criminal` | bool | Risco concreto a instrucao criminal |
| `instrucao_encerrada` | bool | Instrucao judicial encerrada (art. 400) — caduca o fundamento acima |
| `risco_aplicacao_lei_penal` | bool | Risco concreto de fuga (indicios objetivos) |

**Forma, contemporaneidade e revisao**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `fundamentacao_generica` | bool | Decisao com fundamentacao generica ou per relationem |
| `fatos_novos_ou_contemporaneos` | bool | Fatos motivadores sao atuais |
| `crime_permanente` | bool | Delito de natureza permanente |
| `conduta_recente_demonstrada` | bool | Prova de conduta criminosa recente (relevante se `crime_permanente=True`) |
| `juizo_foi_intimado_apos_90_dias` | bool | Juizo formalmente intimado apos vencimento dos 90 dias |

## Testes

```bash
pytest tests/test_fapc.py -v
```

Resultado esperado:

```
collected 34 items

testes/test_fapc.py::test_processo_completamente_legal              PASSED
testes/test_fapc.py::TestPrazoInquerito::test_estadual_no_limite_legal  PASSED
...
testes/test_fapc.py::TestRevisao316::test_91_dias_com_intimacao_inerte_ilegal  PASSED

34 passed in 0.29s
```

Cobertura:

| Modulo | Cenarios cobertos |
|--------|------------------|
| TestPrazoInquerito | Fronteiras exatas 10/15/30 dias; complexidade -> ALERTA |
| TestAdmissibilidade313 | Crime culposo com pena > 4 anos; VD e par.1 autonomos; reincidencia dolosa |
| TestSubsidiariedade | Ausencia de analise do art. 319 como nulidade autonoma |
| TestFumus | Autoria e materialidade separados; ausencia de ambos |
| TestPericulum | Instrucao em curso vs. encerrada; unico fundamento caducado |
| Forma / Contemporaneidade | Fundamentacao generica; fatos preteritos; crime permanente |
| TestRevisao316 | Fronteira exata de 90 dias; ALERTA vs. ILEGAL por inércia |

## Historico de Versoes

**v4.1 (atual)**
- Campo `crime_doloso` como pre-requisito do art. 313, I e II — elimina falso positivo em crimes culposos com pena > 4 anos (ex: homicidio culposo no transito).
- Campo `instrucao_encerrada` substitui inferencia via `fase_inquerito` — distingue corretamente encerramento do IP do encerramento da instrucao judicial (art. 400 CPP).

**v4.0**
- `@dataclass(frozen=True)` em substituicao ao `TypedDict` — imutabilidade real.
- Camada de subsidiariedade (art. 282, par. 6) anterior ao merito cautelar.
- Periculum libertatis desmembrado em quatro campos individuais.
- `caso_complexo` gera ALERTA (nao suprime a verificacao de prazo).
- SQLite com gerenciador de contexto (`with ... as conn`).
- Documento gerado como "Requerimento", nao alvara judicial.
- Correcao do off-by-one nos prazos do inquerito (`>` nao `>=`).

**v3.0**
- Substituicao de CSV por SQLite (operacoes atomicas).
- Status ALERTA introduzido para o art. 316.
- Distincao entre Justica Federal e Estadual nos prazos do inquerito.
- Suporte a Lei de Drogas (Lei 11.343/06, art. 51).

## Como Citar

ABNT:

> GOMEZ, Emerson. FAPC - Ferramenta de Analise de Prisoes Cautelares. Versao 4.1. Campo Grande, 2026. Disponivel em: https://github.com/gomez2023/fapc. Acesso em: [data].

## Contribuicoes

Contribuicoes sao bem-vindas, especialmente de profissionais do direito e desenvolvedores interessados em garantismo algoritmico.

Para reportar erros juridicos (interpretacao de norma, jurisprudencia desatualizada):

1. Abra uma issue com a tag `juridico` descrevendo a norma ou precedente afetado.
2. Inclua a referencia legal ou doutrinaria que embasa a correcao.

Para contribuir com codigo:

1. Abra uma issue descrevendo a melhoria proposta.
2. Faca um fork do repositorio.
3. Crie uma branch com nome descritivo (ex: `fix/art313-inciso-iv`).
4. Escreva ou atualize os testes unitarios correspondentes.
5. Envie um pull request — contribuicoes sem testes nao serao aceitas.

Aviso: toda alteracao no nucleo de avaliacao juridica (`avaliar_prisao_preventiva`) deve ser acompanhada de fundamentacao doutrinaria ou jurisprudencial.

## Licenca

Academica — uso livre com atribuicao.

Contato: assisemerson934@gmail.com | LinkedIn: https://linkedin.com/in/emerson-gomez | GitHub: https://github.com/gomez2023