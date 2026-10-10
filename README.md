# Convergência espacial entre CAR e MapBiomas na bacia do rio Gramame

[![Abrir no Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Emanuel2806PB/gramame-car-mapbiomas/blob/main/notebooks/comparacao_car_mapbiomas_gramame.ipynb)

Códigos do Trabalho de Conclusão de Curso de Emanuel Gomes Soares, desenvolvido no Curso de Especialização em Geoprocessamento do Instituto Federal Baiano. O projeto compara a vegetação nativa declarada no Cadastro Ambiental Rural (CAR) com as classes naturais do MapBiomas Coleção 11, ano de 2025, na bacia hidrográfica do rio Gramame, Paraíba.

O índice de convergência é a proporção da área válida do MapBiomas, dentro da vegetação nativa declarada, classificada como formação natural:

```text
IC (%) = 100 × área MapBiomas natural coincidente / área MapBiomas válida na vegetação declarada
```

O indicador é exploratório. Ele não substitui a análise administrativa do CAR nem determina, isoladamente, a regularidade ambiental dos imóveis.

## Estrutura

```text
config/       configuração de exemplo e códigos temáticos
notebooks/    roteiro executável da análise
src/          pacote Python do processamento geoespacial
tests/        teste sintético independente dos dados reais
pyproject.toml
```

Os dados brutos e os resultados processados não integram o repositório. Essa separação evita redistribuição indevida, reduz o tamanho do histórico Git e preserva a identificação das fontes oficiais.

## Fontes de dados

- SICAR: imóveis rurais e vegetação nativa declarada, disponibilizados no GeoServer/WebGIS do cadastro;
- AESA: limite da bacia hidrográfica do rio Gramame;
- IBGE: limites político-administrativos de apoio cartográfico;
- MapBiomas Brasil: cobertura e uso da terra, Coleção 11, ano de 2025, resolução espacial de 30 m.

Registre no trabalho e nos metadados a URL, a data de acesso, a camada, a abrangência, o formato e a versão efetivamente utilizados. A configuração considera como naturais os códigos `3, 4, 5, 6, 7, 11, 12, 29, 32, 49, 50, 77 e 84`, conforme a legenda da Coleção 11 consultada para a pesquisa.

## Preparação

Requer Python 3.11 ou superior. Na raiz do repositório:

```bash
python -m venv .venv
```

No Windows:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

No Linux ou macOS:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Copie `config/gramame.example.yaml` para `config/gramame.yaml` e ajuste caminhos, camadas e campos aos arquivos obtidos nas fontes oficiais. A estrutura esperada é:

```text
dados/
├── limites/bacia_gramame.gpkg
├── car/imoveis_rurais.gpkg
├── car/vegetacao_nativa.gpkg
└── mapbiomas/mapbiomas_coverage_collection_11_2025.tif
```

## Execução

Pelo terminal:

```bash
python -m gramame_car_mapbiomas --config config/gramame.yaml
```

Ou abra `notebooks/comparacao_car_mapbiomas_gramame.ipynb`, selecione o ambiente criado e execute as células em ordem.

### Google Colab

O notebook também contém uma célula específica para o Colab. Antes da primeira execução:

1. mantenha a pasta `TCC_Gramame/dados` no Google Drive, conforme os caminhos de `config/gramame.colab.example.yaml`;
2. autorize a montagem do Drive quando solicitado;
3. copie o arquivo de exemplo para `config/gramame.colab.yaml`, se precisar alterar caminhos ou nomes das camadas, e execute as demais células.

O botão “Abrir no Google Colab” utiliza diretamente a versão publicada neste repositório.

## Produtos

O pipeline grava em `output/gramame_car_mapbiomas/`:

- GeoPackage com área de estudo, imóveis e vegetação declarada recortados;
- tabelas CSV de indicadores, classes e controle de qualidade;
- raster categórico da convergência CAR–MapBiomas;
- mapas em PNG e SVG;
- metadados de execução e arquivo de log.

## Verificação

O teste não depende dos dados oficiais e verifica, em geometrias sintéticas, a união sem dupla contagem e o cruzamento raster-vetor:

```bash
python -m pytest -q
```

## Citação

Ao reutilizar os códigos, cite o TCC e a versão arquivada do repositório. Os metadados básicos estão em `CITATION.cff`. A referência definitiva deverá ser atualizada após a entrega do trabalho e, se houver depósito, com o DOI ou endereço do repositório institucional.

## Autoria e uso

Autor: Emanuel Gomes Soares. Os códigos são disponibilizados para transparência e reprodução acadêmica. Nenhuma licença de reutilização foi definida nesta versão; para usos além da consulta e reprodução do estudo, contate o autor.
