# Projeto Overleaf do TCC

## Compilação

1. No Overleaf, envie todo o conteúdo desta pasta como um projeto.
2. Defina `main.tex` como documento principal.
3. Selecione o compilador **XeLaTeX**.
4. Compile duas vezes para atualizar sumário, listas, referências e a conferência de páginas.

O arquivo usa Arial quando a fonte está disponível. Como o Overleaf não distribui todas as fontes proprietárias, a configuração recorre automaticamente à TeX Gyre Heros, equivalente métrica da família Arial. Para correspondência tipográfica exata, envie ao projeto os arquivos de fonte Arial licenciados e ajuste o bloco indicado em `main.tex`.

## Organização

- `main.tex`: documento completo e autocontido, incluindo referências BibTeX.
- `figuras/`: mapas e demais ilustrações usadas no manuscrito.
- `fluxogramas/`: esboços BPMN 2.0 importáveis no Bizagi Modeler.
- `CHECKLIST_ABNT_IFBAIANO.md`: controle editorial antes da entrega.

## Estrutura adotada

O projeto está organizado como TCC monográfico: elementos pré-textuais, texto iniciado pela Introdução e elementos pós-textuais. Resumo e Abstract aparecem antes das listas e do sumário. As Referências são pós-textuais, sem numeração, mas constam no sumário.

## Pontos ainda dependentes do autor

- nome e titulação do orientador e, se houver, coorientador;
- data da defesa e composição da banca;
- revisão final das citações e confirmação de que toda referência listada foi citada;
- decisão sobre dedicatória, agradecimentos, epígrafe, glossário, apêndices e anexos.

## Revisão por capítulo no TeXstudio

O documento mestre é `main.tex`. O texto acadêmico está separado em `capitulos/`:

- `01-introducao.tex`
- `02-referencial-teorico.tex`
- `03-materiais-e-metodos.tex`
- `04-resultados-e-discussao.tex`
- `05-consideracoes-finais.tex`

Cada capítulo contém a diretiva `% !TeX root = ../main.tex`. Assim, ao abrir um capítulo no TeXstudio e executar a compilação, o programa utiliza automaticamente o documento mestre e gera o TCC completo. Não compile os capítulos isoladamente com `xelatex`; eles dependem do preâmbulo e dos elementos pré-textuais de `main.tex`.
