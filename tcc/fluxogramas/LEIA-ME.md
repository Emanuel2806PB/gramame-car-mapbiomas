# Esboços BPMN para o Bizagi Modeler

Os arquivos `.bpmn` seguem BPMN 2.0 e já contêm formas e conectores. No Bizagi Modeler, use **Exportar/Importar > BPMN** e selecione o arquivo.

## Diagramas

- `01_aquisicao_preparacao_dados.bpmn`: seleção da bacia, aquisição das bases, conferência de metadados, padronização espacial, auditoria geométrica e consolidação.
- `02_analise_convergencia_validacao.bpmn`: rasterização, reclassificação temática, cálculo do índice, validações, mapas, tabelas e disponibilização dos produtos.

## Convenção sugerida no Bizagi

- Azul: aquisição e preparação.
- Verde: processamento concluído.
- Amarelo: validação ou decisão.
- Vermelho claro: correção/retorno.
- Objetos de dados: arquivos vetoriais, raster, YAML, CSV, JSON, QGIS e mapas.

Antes de exportar a figura para o artigo, revise os nomes das tarefas, adicione o nome do responsável por cada raia e exporte em PDF vetorial para `overleaf/figuras/fluxograma_metodologico_bpmn.pdf`.
