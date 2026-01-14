#!/bin/bash

# Archeon 3D - Automated Docker Installer
# Robust setup and management script

set -e

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   Archeon 3D - Docker Setup Tool       ${NC}"
echo -e "${BLUE}=========================================${NC}"

# 1. Prerequisite Checks
check_prerequisites() {
    echo -e "\n${YELLOW}[1/3] Verificando pré-requisitos...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERRO: Docker não encontrado. Por favor, instale o Docker primeiro.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✔ Docker detectado.${NC}"

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}ERRO: Docker Compose (V2) não encontrado.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✔ Docker Compose detectado.${NC}"

    # Check NVIDIA GPU
    if ! command -v nvidia-smi &> /dev/null; then
        echo -e "${YELLOW}AVISO: NVIDIA GPU não detectada via nvidia-smi. A aplicação pode rodar mas será muito lenta (CPU mode).${NC}"
    else
        echo -e "${GREEN}✔ NVIDIA GPU detectada.${NC}"
        # Check NVIDIA Container Toolkit
        if ! docker run --rm hello-world &> /dev/null; then
             echo -e "${RED}ERRO: Docker não consegue rodar containers.${NC}"
             echo -e "${YELLOW}Dica: Verifique se o serviço Docker está rodando ou se você precisa de permissões de administrador (sudo).${NC}"
             echo -e "${YELLOW}Tente rodar: 'sudo usermod -aG docker \$USER' e reinicie a sessão.${NC}"
             exit 1
        fi
    fi
}

# 2. Environment Setup
setup_environment() {
    echo -e "\n${YELLOW}[2/3] Preparando ambiente...${NC}"
    mkdir -p logs gradio_cache
    chmod 777 logs gradio_cache
    echo -e "${GREEN}✔ Diretórios de cache e logs criados.${NC}"
}

# 3. Helper Functions
wait_and_open() {
    local url=$1
    local max_retries=60 # Wait up to 60 seconds
    local count=0
    
    echo -e "${YELLOW}Aguardando serviço iniciar em ${url}...${NC}"
    
    # Run in background to not block the menu loop if it takes too long, 
    # but initially we want to give it a chance. 
    # Actually, simpler to just background the whole wait process.
    (
        while ! curl -s --head "$url" > /dev/null; do
            sleep 1
            count=$((count+1))
            if [ $count -ge $max_retries ]; then
                # Timeout silently to not mess up the terminal if user is doing other things
                exit 1
            fi
        done
        
        if command -v xdg-open &> /dev/null; then
            xdg-open "$url" &> /dev/null
        elif command -v open &> /dev/null; then
            open "$url" &> /dev/null
        fi
    ) &
}

# 4. Interactive Menu
show_menu() {
    echo -e "\n${BLUE}--- Menu de Gerenciamento ---${NC}"
    echo -e "1) ${GREEN}Build${NC} (Construir/Atualizar Imagem)"
    echo -e "2) ${GREEN}Start${NC} (Iniciar Interface Gradio)"
    echo -e "3) ${GREEN}Start API${NC} (Iniciar Servidor de API)"
    echo -e "4) ${YELLOW}Stop${NC} (Parar todos os containers)"
    echo -e "5) ${BLUE}Logs${NC} (Ver logs em tempo real)"
    echo -e "6) ${RED}Clean${NC} (Remover containers e imagens antigas)"
    echo -e "q) Sair"
    echo -ne "\nEscolha uma opção: "
    read opt
}

# Logic execution
check_prerequisites
setup_environment

while true; do
    show_menu
    case $opt in
        1)
            echo -e "${YELLOW}Construindo imagem Docker...${NC}"
            docker compose build
            ;;
        2)
            echo -e "${YELLOW}Iniciando Archeon 3D (Gradio)...${NC}"
            docker compose up -d
            echo -e "${GREEN}Aplicação disponível em http://localhost:7860${NC}"
            wait_and_open "http://localhost:7860"
            ;;
        3)
            echo -e "${YELLOW}Iniciando Archeon 3D (API Server)...${NC}"
            docker compose run -d -p 8000:8000 hunyuan3d python3 -m hy3dgen.apps.api_server
            echo -e "${GREEN}API disponível em http://localhost:8000${NC}"
            ;;
        4)
            echo -e "${YELLOW}Parando serviços...${NC}"
            docker compose down
            ;;
        5)
            docker compose logs -f
            ;;
        6)
            echo -e "${RED}Limpando ambiente docker...${NC}"
            docker compose down --rmi all --volumes --remove-orphans
            ;;
        q)
            echo -e "Saindo..."
            exit 0
            ;;
        *)
            echo -e "${RED}Opção inválida.${NC}"
            ;;
    esac
done
