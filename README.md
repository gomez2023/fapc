# FAPC - Ferramenta de Análise de Prisões Cautelares

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Pytest](https://img.shields.io/badge/Testes-12%20passed-22c55e?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![CI](https://github.com/gomez2023/fapc/actions/workflows/ci.yml/badge.svg)](https://github.com/gomez2023/fapc/actions/workflows/ci.yml)

## Sobre

Sistema de auditoria automatizada da legalidade de prisões preventivas baseado em regras (não IA), implementado em Python. O FAPC verifica os requisitos dos arts. 312 a 316 do CPP, jurisprudência do STF e doutrina de Aury Lopes Jr.

## Instalação e Uso

\\\ash
git clone https://github.com/gomez2023/fapc.git
cd fapc
pip install -r requirements.txt
python run.py
\\\

## Testes

\\\ash
pytest tests/test_fapc.py -v
\\\

## Licença

Acadêmica - uso livre com atribuição.

## Autor

Emerson Gomez - [LinkedIn](https://www.linkedin.com/in/emerson-gomez-20822736b) | [GitHub](https://github.com/gomez2023)
