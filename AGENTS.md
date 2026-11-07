# Instruções para agentes no projeto Gramame

## Escopo

Este repositório contém o TCC de Emanuel Gomes Soares sobre a convergência espacial entre a vegetação nativa declarada no CAR e as classes naturais do MapBiomas na bacia hidrográfica do rio Gramame, Paraíba.

O projeto anterior sobre GOES-R RRQPE foi arquivado separadamente e não integra este repositório. Não introduza conteúdo, dados ou referências desse tema no trabalho do Gramame.

## Escrita acadêmica

- Escreva em português brasileiro, com linguagem acadêmica formal, clara, objetiva e impessoal.
- Preserve o significado científico dos resultados e diferencie resultado, interpretação, limitação e recomendação.
- Não invente referências, DOI, legislação, datas de acesso ou características técnicas.
- Antes de incluir nova citação, confirme a existência e a pertinência da fonte em publicação científica ou página oficial.
- Siga as normas da ABNT e as orientações do IF Baiano registradas no projeto.
- Não use linguagem promocional, emocional ou conclusões que excedam as evidências.
- Não trate divergência espacial como prova automática de irregularidade ambiental.

## Arquivos principais

- `tcc/main.tex`: documento acadêmico principal.
- `tcc/referencias.bib`: referências bibliográficas.
- `tcc/figuras/`: mapas e fluxograma usados no texto.
- `apresentacao/apresentacao.tex`: slides Beamer para a defesa.
- `notebooks/comparacao_car_mapbiomas_gramame.ipynb`: roteiro reproduzível da análise.
- `src/gramame_car_mapbiomas/`: código Python do processamento.

## Resultados que devem ser preservados

- 1.974 registros de imóveis rurais interceptados pela bacia.
- 279 polígonos de vegetação nativa declarada.
- 8.224,30 ha de vegetação declarada espacialmente distinta.
- 5.235,93 ha coincidentes com classes naturais.
- 2.988,81 ha associados a classes não naturais.
- índice de convergência espacial de 63,66%.
- 3.012,30 ha de classes naturais nos imóveis fora das declarações analisadas.

Altere esses valores somente quando houver novo processamento documentado e validado.

## LaTeX

- Use XeLaTeX.
- Compile o TCC com XeLaTeX e BibTeX, preferencialmente por `latexmk`.
- Não versione arquivos auxiliares, caches ou PDFs gerados.
- Preserve a estrutura ABNT, a paginação, as margens e os elementos pré-textuais definidos em `tcc/main.tex`.
- Evite ampliar o preâmbulo sem necessidade técnica comprovada.

## Dados e segurança

- Não adicione GeoPackages, shapefiles, rasters, ZIPs de dados ou resultados pesados ao Git.
- Não adicione credenciais, cookies, tokens, arquivos `.env` ou caminhos pessoais do computador.
- Use os arquivos de configuração de exemplo e mantenha configurações locais fora do versionamento.
- Testes automatizados devem usar dados sintéticos.

## Verificação

- Execute `python -m pytest -q` após alterações no código Python.
- Compile o documento afetado após alterações em LaTeX.
- Confira se tabelas, mapas, equações e números permanecem consistentes entre texto e apresentação.
