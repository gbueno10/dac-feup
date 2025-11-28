#!/bin/bash

# Script para baixar os arquivos necessários do Gridfinity
echo "📥 Baixando arquivos SCAD do Gridfinity..."

# URL base do repositório
BASE_URL="https://raw.githubusercontent.com/kennetek/gridfinity-rebuilt-openscad/main"

# Baixa os arquivos principais
curl -o gridfinity_basic_cup.scad "${BASE_URL}/gridfinity-rebuilt-bins.scad"
curl -o gridfinity_modules.scad "${BASE_URL}/standard.scad"

echo "✅ Arquivos baixados com sucesso!"
echo ""
echo "Arquivos disponíveis:"
ls -lh *.scad
