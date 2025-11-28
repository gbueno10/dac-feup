#!/bin/bash

# Script para baixar os arquivos necessários do Gridfinity
echo "📥 Baixando arquivos SCAD do Gridfinity..."

# URL base do repositório
BASE_URL="https://raw.githubusercontent.com/kennetek/gridfinity-rebuilt-openscad/main"

# Cria estrutura de pastas
mkdir -p src/core

# Baixa o arquivo principal
echo "Baixando arquivo principal..."
curl -o gridfinity_basic_cup.scad "${BASE_URL}/gridfinity-rebuilt-bins.scad"

# Baixa os módulos necessários
echo "Baixando módulos..."
curl -o src/core/standard.scad "${BASE_URL}/src/core/standard.scad"
curl -o src/core/gridfinity-rebuilt-utility.scad "${BASE_URL}/src/core/gridfinity-rebuilt-utility.scad"
curl -o src/core/gridfinity-rebuilt-holes.scad "${BASE_URL}/src/core/gridfinity-rebuilt-holes.scad"
curl -o src/core/bin.scad "${BASE_URL}/src/core/bin.scad"
curl -o src/core/cutouts.scad "${BASE_URL}/src/core/cutouts.scad"

echo ""
echo "✅ Arquivos baixados com sucesso!"
echo ""
echo "Arquivos disponíveis:"
ls -lh gridfinity_basic_cup.scad
ls -lh src/core/*.scad
