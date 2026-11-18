#!/bin/bash

# Script para baixar os arquivos necessários do Gridfinity
echo "📥 Baixando arquivos SCAD do Gridfinity..."

# URL base do repositório
BASE_URL="https://raw.githubusercontent.com/kennetek/gridfinity-rebuilt-openscad/main"

# Cria estrutura de pastas
mkdir -p src/core
mkdir -p src/helpers

# Baixa o arquivo principal
echo "Baixando arquivo principal..."
curl -o gridfinity_basic_cup.scad "${BASE_URL}/gridfinity-rebuilt-bins.scad"

# Baixa os módulos core
echo "Baixando módulos core..."
curl -o src/core/standard.scad "${BASE_URL}/src/core/standard.scad"
curl -o src/core/gridfinity-rebuilt-utility.scad "${BASE_URL}/src/core/gridfinity-rebuilt-utility.scad"
curl -o src/core/gridfinity-rebuilt-holes.scad "${BASE_URL}/src/core/gridfinity-rebuilt-holes.scad"
curl -o src/core/bin.scad "${BASE_URL}/src/core/bin.scad"
curl -o src/core/cutouts.scad "${BASE_URL}/src/core/cutouts.scad"
curl -o src/core/tab.scad "${BASE_URL}/src/core/tab.scad"
curl -o src/core/base.scad "${BASE_URL}/src/core/base.scad"
curl -o src/core/wall.scad "${BASE_URL}/src/core/wall.scad"

# Baixa os helpers
echo "Baixando helpers..."
curl -o src/helpers/generic-helpers.scad "${BASE_URL}/src/helpers/generic-helpers.scad"
curl -o src/helpers/grid.scad "${BASE_URL}/src/helpers/grid.scad"
curl -o src/helpers/grid_element.scad "${BASE_URL}/src/helpers/grid_element.scad"
curl -o src/helpers/angles.scad "${BASE_URL}/src/helpers/angles.scad"
curl -o src/helpers/shapes.scad "${BASE_URL}/src/helpers/shapes.scad"
curl -o src/helpers/list.scad "${BASE_URL}/src/helpers/list.scad"

echo ""
echo "✅ Arquivos baixados com sucesso!"
echo ""
echo "Estrutura criada:"
tree -L 2 src/ 2>/dev/null || find src/ -type f | sort
echo ""
ls -lh gridfinity_basic_cup.scad
